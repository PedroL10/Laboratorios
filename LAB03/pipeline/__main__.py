"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Etapas implementadas ate agora:
1. busca de repositorios candidatos por faixas de estrelas (dados/candidatos.csv);
2. filtro dos candidatos que usam GitHub Actions (dados/filtro_actions.csv);
3. criterio de inclusao: >= 5 releases e >= 50 runs validos na janela (dados/criterio_inclusao.csv);
4. funil de selecao e amostra final (resultados/funil_selecao.csv/.md e resultados/amostra.csv);
5. metadados da amostra: contribuidores (dados/contribuidores.csv) e idade, acrescentados
   a resultados/amostra.csv;
6. coleta de releases (cache/releases/*.json) e commits entre releases
   (cache/commits_entre_releases/*.json) dos repositorios da amostra;
7. calculo do lead time (RQ 02, variantes a e b) por repositorio (dados/lead_time.csv).
As etapas de coleta de workflow runs e das demais metricas serao adicionadas por
outras tasks.

As etapas 1, 2, 3 e 5 salvam o seu CSV em `dados_dir`. Se o arquivo ja existir, a etapa e
reaproveitada (ou retomada); para refaze-la do zero, apague o arquivo. A etapa 4 nao
chama a API e e sempre refeita, em `resultados_dir` (versionado no repositorio).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import requests

from metricas.lead_time import lead_time_repositorio
from pipeline.commits import coletar_commits_entre_releases
from pipeline.config import load_config
from pipeline.criterio_inclusao import Janela, aplicar_criterio, incluido
from pipeline.filtro_actions import filtrar_actions, usa_actions
from pipeline.funil import (
    FUNIL_FIELDS,
    funil_markdown,
    funil_para_csv,
    montar_amostra,
    montar_funil,
    salvar_markdown,
)
from pipeline.github_client import (
    GitHubClient,
    MissingTokenError,
    cota_esgotada,
    erro_transitorio,
    status_http,
)
from pipeline.metadados import coletar_contribuidores, enriquecer_amostra
from pipeline.releases import coletar_releases, releases_na_janela, releases_principais
from pipeline.selecao import CANDIDATE_FIELDS, buscar_candidatos, carregar_csv, salvar_csv

LEAD_TIME_FIELDS = [
    "full_name",
    "lead_time_release_dias",
    "lead_time_commit_dias",
    "n_releases_variante_a",
    "n_commits_variante_b",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pipeline", description="Mineracao de metricas DORA (LAB03)."
    )
    parser.add_argument("--config", default="config.yaml", help="Caminho do config.yaml")
    return parser.parse_args(argv)


def etapa_busca(client: GitHubClient, selecao: dict, dados_dir: Path) -> list[dict]:
    caminho = dados_dir / "candidatos.csv"
    if caminho.exists():
        candidatos = carregar_csv(caminho)
        print(f"\n[1] Reaproveitando {len(candidatos)} candidatos de {caminho}")
        return candidatos

    print(
        f"\n[1] Buscando ate {selecao['max_candidatos']} candidatos com mais de "
        f"{selecao['estrelas_min']} estrelas..."
    )
    candidatos, fatias = buscar_candidatos(
        client, selecao["estrelas_min"], selecao["max_candidatos"]
    )
    for fatia in fatias:
        print(
            f"    {fatia['faixa']:<22} total={fatia['total_count']:>6} "
            f"resultados={fatia['resultados']:>5} novos={fatia['novos']:>5}"
        )
    salvar_csv(candidatos, caminho, CANDIDATE_FIELDS)
    salvar_csv(fatias, dados_dir / "fatias_busca.csv", list(fatias[0].keys()))
    print(f"    {len(candidatos)} candidatos salvos em {caminho}")
    return candidatos


def etapa_filtro_actions(
    client: GitHubClient, candidatos: list[dict], dados_dir: Path
) -> tuple[list[dict], list[dict]]:
    """Devolve `(com_actions, resultado)`: os candidatos aprovados e uma linha por candidato."""
    caminho = dados_dir / "filtro_actions.csv"
    print("\n[2] Verificando quais candidatos usam GitHub Actions...")

    def progresso(feitos: int, total: int) -> None:
        if feitos % 100 == 0 or feitos == total:
            print(f"    {feitos}/{total} verificados")

    resultado = filtrar_actions(client, candidatos, caminho, progresso)
    com_actions = [c for c, r in zip(candidatos, resultado) if usa_actions(r)]

    motivos: dict[str, int] = {}
    for r in resultado:
        if not usa_actions(r):
            motivos[r["motivo_descarte"]] = motivos.get(r["motivo_descarte"], 0) + 1
    print(f"    {len(com_actions)} de {len(candidatos)} usam GitHub Actions")
    for motivo, n in sorted(motivos.items()):
        print(f"    descartados ({motivo}): {n}")
    return com_actions, resultado


def etapa_criterio(
    client: GitHubClient, com_actions: list[dict], config: dict, dados_dir: Path
) -> list[dict]:
    """Devolve as linhas do criterio dos repositorios avaliados (incluidos e descartados)."""
    selecao = config["selecao"]
    janela = Janela(config["janela"]["inicio"], config["janela"]["fim"])
    n_repos = selecao.get("n_repos")
    print(
        f"\n[3] Aplicando criterio de inclusao na janela {janela.filtro_created()} "
        f"(>= {selecao['min_releases']} releases e >= {selecao['min_workflow_runs']} runs validos)..."
    )

    def progresso(feitos: int, total: int) -> None:
        if feitos % 50 == 0:
            print(f"    {feitos} avaliados nesta execucao")

    avaliados = aplicar_criterio(
        client,
        com_actions,
        janela,
        selecao["min_releases"],
        selecao["min_workflow_runs"],
        n_repos,
        dados_dir / "criterio_inclusao.csv",
        progresso,
    )
    amostra = [a for a in avaliados if incluido(a)]

    motivos: dict[str, int] = {}
    for a in avaliados:
        if not incluido(a):
            motivos[a["motivo_descarte"]] = motivos.get(a["motivo_descarte"], 0) + 1
    print(f"    {len(avaliados)} de {len(com_actions)} avaliados; {len(amostra)} incluidos na amostra")
    for motivo, n in sorted(motivos.items()):
        print(f"    descartados ({motivo}): {n}")
    if n_repos is not None and len(amostra) < n_repos:
        print(f"    ATENCAO: amostra abaixo de {n_repos}. Aumente selecao.max_candidatos.")
    return avaliados


def etapa_funil(
    candidatos: list[dict],
    filtro_actions: list[dict],
    avaliados: list[dict],
    config: dict,
    resultados_dir: Path,
) -> list[dict]:
    """Gera o funil e a amostra final; devolve os repositorios da amostra."""
    selecao = config["selecao"]
    janela = Janela(config["janela"]["inicio"], config["janela"]["fim"])
    print("\n[4] Gerando funil de selecao e amostra final...")

    funil = montar_funil(
        candidatos,
        filtro_actions,
        avaliados,
        selecao["estrelas_min"],
        selecao["min_releases"],
        selecao["min_workflow_runs"],
    )
    salvar_csv(funil_para_csv(funil), resultados_dir / "funil_selecao.csv", FUNIL_FIELDS)
    markdown = funil_markdown(funil, janela.filtro_created())
    salvar_markdown(markdown, resultados_dir / "funil_selecao.md")

    amostra = montar_amostra(candidatos, avaliados)
    if amostra:
        salvar_csv(amostra, resultados_dir / "amostra.csv", list(amostra[0].keys()))

    print("\n" + markdown)
    print(f"    Funil salvo em {resultados_dir / 'funil_selecao.csv'} e .md")
    print(f"    Amostra final ({len(amostra)} repositorios) salva em {resultados_dir / 'amostra.csv'}")
    return amostra


def etapa_metadados(
    client: GitHubClient,
    amostra: list[dict],
    config: dict,
    dados_dir: Path,
    resultados_dir: Path,
) -> list[dict]:
    """Acrescenta contribuidores e idade a amostra e regrava resultados/amostra.csv."""
    janela = Janela(config["janela"]["inicio"], config["janela"]["fim"])
    print(f"\n[5] Coletando contribuidores de {len(amostra)} repositorios da amostra...")

    def progresso(feitos: int, total: int) -> None:
        if feitos % 25 == 0 or feitos == total:
            print(f"    {feitos}/{total} contribuidores contados")

    contribuidores = coletar_contribuidores(
        client, amostra, dados_dir / "contribuidores.csv", progresso
    )
    amostra = enriquecer_amostra(amostra, contribuidores, janela.fim_data)
    salvar_csv(amostra, resultados_dir / "amostra.csv", list(amostra[0].keys()))

    sem_valor: dict[str, int] = {}
    for repo in amostra:
        if repo["erro_contribuidores"]:
            sem_valor[repo["erro_contribuidores"]] = sem_valor.get(repo["erro_contribuidores"], 0) + 1
    print(f"    {len(amostra) - sum(sem_valor.values())} de {len(amostra)} com contribuidores contados")
    for motivo, n in sorted(sem_valor.items()):
        print(f"    sem contagem ({motivo}): {n}")
    print(f"    Amostra com metadados salva em {resultados_dir / 'amostra.csv'}")
    return amostra


def etapa_releases_e_lead_time(
    client: GitHubClient,
    candidatos: list[dict],
    janela: dict,
    cache_dir: Path,
    dados_dir: Path,
) -> None:
    full_names = [c["full_name"] for c in candidatos]

    print(f"\n[6] Coletando releases de {len(full_names)} repositorios...")

    def progresso_releases(feitos: int, total: int) -> None:
        if feitos % 50 == 0 or feitos == total:
            print(f"    releases: {feitos}/{total} coletados")

    todas_releases = coletar_releases(client, full_names, cache_dir, progresso_releases)

    inicio, fim = janela.get("inicio"), janela.get("fim")
    principais_por_repo = {}
    for full_name, releases in todas_releases.items():
        principais = releases_principais(releases)
        if inicio and fim:
            principais = releases_na_janela(principais, inicio, fim)
        principais_por_repo[full_name] = principais

    print("\n[7] Coletando commits entre releases...")

    def progresso_commits(feitos: int, total: int) -> None:
        if feitos % 50 == 0 or feitos == total:
            print(f"    commits entre releases: {feitos}/{total} repositorios")

    commits_por_repo = coletar_commits_entre_releases(
        client, principais_por_repo, cache_dir, progresso_commits
    )

    linhas = []
    for full_name in full_names:
        releases_com_commits = commits_por_repo[full_name]["releases"]
        resultado = lead_time_repositorio(releases_com_commits)
        linhas.append({"full_name": full_name, **resultado})

    caminho = dados_dir / "lead_time.csv"
    salvar_csv(linhas, caminho, LEAD_TIME_FIELDS)
    print(f"    lead time de {len(linhas)} repositorios salvo em {caminho}")



def mensagem_de_erro(exc: requests.HTTPError) -> str:
    """Explica o erro HTTP que interrompeu a coleta e o que fazer."""
    status = status_http(exc)
    if status == 401:
        return "token do GitHub invalido ou expirado (401). Gere um novo e defina GITHUB_TOKEN."
    if cota_esgotada(exc):
        reset = exc.response.headers.get("X-RateLimit-Reset")
        quando = datetime.fromtimestamp(int(reset)).strftime("%H:%M") if reset else "em ate 1 hora"
        return (
            f"cota da API esgotada. Ela renova as {quando}; rode o comando de novo "
            "depois disso e a coleta continua de onde parou."
        )
    if erro_transitorio(exc):
        return (
            f"erro temporario do GitHub ({status}). Rode o comando de novo: "
            "a coleta continua de onde parou."
        )
    return str(exc)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    print(f"Configuracao carregada de {args.config}: {config}")

    try:
        client = GitHubClient()
    except MissingTokenError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    try:
        rate = client.get("/rate_limit")["resources"]["core"]
        print(f"API do GitHub acessivel. Requisicoes restantes: {rate['remaining']}/{rate['limit']}")

        selecao = config["selecao"]
        dados_dir = Path(config.get("dados_dir", "dados"))
        resultados_dir = Path(config.get("resultados_dir", "resultados"))
        cache_dir = Path(config.get("cache_dir", "cache"))

        candidatos = etapa_busca(client, selecao, dados_dir)
        com_actions, filtro_actions = etapa_filtro_actions(client, candidatos, dados_dir)
        avaliados = etapa_criterio(client, com_actions, config, dados_dir)
        amostra = etapa_funil(candidatos, filtro_actions, avaliados, config, resultados_dir)
        amostra = etapa_metadados(client, amostra, config, dados_dir, resultados_dir)
        etapa_releases_e_lead_time(
            client, amostra, config.get("janela", {}), cache_dir, dados_dir
        )
    except requests.HTTPError as exc:
        print(f"\nErro: {mensagem_de_erro(exc)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
