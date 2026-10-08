"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Etapas implementadas ate agora:
1. busca de repositorios candidatos por faixas de estrelas (dados/candidatos.csv);
2. filtro dos candidatos que usam GitHub Actions (dados/filtro_actions.csv);
3. coleta de releases (cache/releases/*.json) e commits entre releases
   (cache/commits_entre_releases/*.json);
4. calculo do lead time (RQ 02, variantes a e b) por repositorio (dados/lead_time.csv).
As etapas de coleta de workflow runs e das demais metricas serao adicionadas por
outras tasks.

Cada etapa salva o seu CSV em `dados_dir`. Se o arquivo ja existir, a etapa e
reaproveitada (ou retomada); para refaze-la do zero, apague o arquivo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metricas.lead_time import lead_time_repositorio
from pipeline.commits import coletar_commits_entre_releases
from pipeline.config import load_config
from pipeline.filtro_actions import filtrar_actions, usa_actions
from pipeline.github_client import GitHubClient, MissingTokenError
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
) -> list[dict]:
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
    return com_actions


def etapa_releases_e_lead_time(
    client: GitHubClient,
    candidatos: list[dict],
    janela: dict,
    cache_dir: Path,
    dados_dir: Path,
) -> None:
    full_names = [c["full_name"] for c in candidatos]

    print(f"\n[3] Coletando releases de {len(full_names)} repositorios...")

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

    print("\n[4] Coletando commits entre releases...")

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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    print(f"Configuracao carregada de {args.config}: {config}")

    try:
        client = GitHubClient()
    except MissingTokenError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    rate = client.get("/rate_limit")["resources"]["core"]
    print(f"API do GitHub acessivel. Requisicoes restantes: {rate['remaining']}/{rate['limit']}")

    selecao = config["selecao"]
    dados_dir = Path(config.get("dados_dir", "dados"))
    cache_dir = Path(config.get("cache_dir", "cache"))

    candidatos = etapa_busca(client, selecao, dados_dir)
    com_actions = etapa_filtro_actions(client, candidatos, dados_dir)
    etapa_releases_e_lead_time(client, com_actions, config.get("janela", {}), cache_dir, dados_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
