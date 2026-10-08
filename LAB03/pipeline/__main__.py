"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Etapas implementadas ate agora:
1. busca de repositorios candidatos por faixas de estrelas (dados/candidatos.csv).
As etapas de filtro, coleta e calculo serao adicionadas pelas proximas tasks.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.config import load_config
from pipeline.github_client import GitHubClient, MissingTokenError
from pipeline.selecao import CANDIDATE_FIELDS, buscar_candidatos, salvar_csv


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pipeline", description="Mineracao de metricas DORA (LAB03)."
    )
    parser.add_argument("--config", default="config.yaml", help="Caminho do config.yaml")
    return parser.parse_args(argv)


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
    salvar_csv(candidatos, dados_dir / "candidatos.csv", CANDIDATE_FIELDS)
    salvar_csv(fatias, dados_dir / "fatias_busca.csv", list(fatias[0].keys()))
    print(f"    {len(candidatos)} candidatos salvos em {dados_dir / 'candidatos.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
