"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Por enquanto so carrega a configuracao e confere o acesso a API do GitHub.
As etapas de selecao, coleta e calculo serao adicionadas pelas proximas tasks.
"""

from __future__ import annotations

import argparse
import sys

from pipeline.config import load_config
from pipeline.github_client import GitHubClient, MissingTokenError


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
