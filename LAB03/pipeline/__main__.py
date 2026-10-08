"""Ponto de entrada do pipeline: `python -m pipeline --config config.yaml`.

Etapas implementadas ate agora:
1. busca de repositorios candidatos por faixas de estrelas (dados/candidatos.csv);
2. filtro dos candidatos que usam GitHub Actions (dados/filtro_actions.csv).
As etapas de criterio de inclusao, coleta e calculo serao adicionadas pelas proximas tasks.

Cada etapa salva o seu CSV em `dados_dir`. Se o arquivo ja existir, a etapa e
reaproveitada (ou retomada); para refaze-la do zero, apague o arquivo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline.config import load_config
from pipeline.filtro_actions import filtrar_actions, usa_actions
from pipeline.github_client import GitHubClient, MissingTokenError
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

    candidatos = etapa_busca(client, selecao, dados_dir)
    etapa_filtro_actions(client, candidatos, dados_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
