"""Filtro dos candidatos que usam GitHub Actions.

Para cada candidato consulta `GET /repos/{owner}/{repo}/actions/workflows?per_page=1`
e le o `total_count`: zero workflows significa que o repositorio nao usa Actions
e e descartado antes de gastar chamadas com releases e runs (secao 4 do enunciado).

O resultado de cada repositorio e gravado no CSV assim que sai. Se a execucao
for interrompida, rodar de novo pula os repositorios ja verificados.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

import requests

from pipeline.github_client import GitHubClient

FILTRO_FIELDS = ["full_name", "usa_actions", "n_workflows", "motivo_descarte"]

MOTIVO_SEM_WORKFLOWS = "sem_workflows"


def verificar_actions(client: GitHubClient, full_name: str) -> dict:
    """Verifica se um repositorio tem workflows do GitHub Actions."""
    try:
        resposta = client.get(f"/repos/{full_name}/actions/workflows", {"per_page": 1})
    except requests.HTTPError as exc:
        response = exc.response
        status = response.status_code if response is not None else None
        # Cota esgotada nao e um descarte: interrompe para retomar depois.
        if status in (403, 429) and response.headers.get("X-RateLimit-Remaining") == "0":
            raise
        return {
            "full_name": full_name,
            "usa_actions": False,
            "n_workflows": None,
            "motivo_descarte": f"erro_http_{status}",
        }

    n_workflows = resposta["total_count"]
    return {
        "full_name": full_name,
        "usa_actions": n_workflows > 0,
        "n_workflows": n_workflows,
        "motivo_descarte": "" if n_workflows > 0 else MOTIVO_SEM_WORKFLOWS,
    }


def carregar_verificados(caminho: Path) -> dict[str, dict]:
    """Le o CSV de uma execucao anterior (se existir) para retomar o filtro."""
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8", newline="") as f:
        return {linha["full_name"]: linha for linha in csv.DictReader(f)}


def filtrar_actions(
    client: GitHubClient,
    candidatos: list[dict],
    caminho_saida: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Verifica todos os candidatos e devolve uma linha por candidato, na ordem original.

    Repositorios ja presentes em `caminho_saida` nao sao consultados de novo.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    verificados = carregar_verificados(caminho_saida)
    pendentes = [c for c in candidatos if c["full_name"] not in verificados]

    novo_arquivo = not caminho_saida.exists()
    with caminho_saida.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FILTRO_FIELDS)
        if novo_arquivo:
            writer.writeheader()
        for i, candidato in enumerate(pendentes, start=1):
            linha = verificar_actions(client, candidato["full_name"])
            writer.writerow(linha)
            f.flush()
            verificados[linha["full_name"]] = linha
            if progresso:
                progresso(i, len(pendentes))

    return [verificados[c["full_name"]] for c in candidatos]


def usa_actions(linha: dict) -> bool:
    """Le a coluna `usa_actions`, que vem como texto quando carregada do CSV."""
    return str(linha["usa_actions"]) == "True"
