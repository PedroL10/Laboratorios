"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Etapas implementadas ate agora:
1. busca de repositorios candidatos por faixas de estrelas (dados/candidatos.csv);
2. filtro dos candidatos que usam GitHub Actions (dados/filtro_actions.csv);
3. criterio de inclusao: >= 5 releases e >= 50 runs validos na janela (dados/criterio_inclusao.csv).
As etapas de coleta e calculo serao adicionadas pelas proximas tasks.

Cada etapa salva o seu CSV em `dados_dir`. Se o arquivo ja existir, a etapa e
reaproveitada (ou retomada); para refaze-la do zero, apague o arquivo.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import requests

from pipeline.config import load_config
from pipeline.criterio_inclusao import Janela, aplicar_criterio, incluido
from pipeline.filtro_actions import filtrar_actions, usa_actions
from pipeline.github_client import (
    GitHubClient,
    MissingTokenError,
    cota_esgotada,
    erro_transitorio,
    status_http,
)
from pipeline.selecao import CANDIDATE_FIELDS, buscar_candidatos, carregar_csv, salvar_csv


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


def etapa_criterio(
    client: GitHubClient, com_actions: list[dict], config: dict, dados_dir: Path
) -> list[dict]:
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
    return amostra


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

        candidatos = etapa_busca(client, selecao, dados_dir)
        com_actions = etapa_filtro_actions(client, candidatos, dados_dir)
        etapa_criterio(client, com_actions, config, dados_dir)
    except requests.HTTPError as exc:
        print(f"\nErro: {mensagem_de_erro(exc)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
