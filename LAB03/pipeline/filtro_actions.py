"""Filtro dos candidatos que usam GitHub Actions.

Para cada candidato consulta `GET /repos/{owner}/{repo}/actions/workflows?per_page=1`
e le o `total_count`: zero workflows significa que o repositorio nao usa Actions
e e descartado antes de gastar chamadas com releases e runs (secao 4 do enunciado).

O resultado de cada repositorio e gravado no CSV assim que sai. Se a execucao
for interrompida, rodar de novo pula os repositorios ja verificados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import requests

from pipeline.github_client import GitHubClient, erro_transitorio, status_http
from pipeline.retomada import carregar_processados, processar_com_retomada

FILTRO_FIELDS = ["full_name", "usa_actions", "n_workflows", "motivo_descarte"]

MOTIVO_SEM_WORKFLOWS = "sem_workflows"


def verificar_actions(client: GitHubClient, full_name: str) -> dict:
    """Verifica se um repositorio tem workflows do GitHub Actions."""
    try:
        resposta = client.get(f"/repos/{full_name}/actions/workflows", {"per_page": 1})
    except requests.HTTPError as exc:
        # Cota esgotada ou erro temporario nao e descarte: interrompe para retomar depois.
        if erro_transitorio(exc):
            raise
        return {
            "full_name": full_name,
            "usa_actions": False,
            "n_workflows": None,
            "motivo_descarte": f"erro_http_{status_http(exc)}",
        }

    n_workflows = resposta["total_count"]
    return {
        "full_name": full_name,
        "usa_actions": n_workflows > 0,
        "n_workflows": n_workflows,
        "motivo_descarte": "" if n_workflows > 0 else MOTIVO_SEM_WORKFLOWS,
    }


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
    ja_feitos = carregar_processados(caminho_saida)
    n_pendentes = sum(1 for c in candidatos if c["full_name"] not in ja_feitos)

    processados = processar_com_retomada(
        candidatos,
        lambda c: verificar_actions(client, c["full_name"]),
        caminho_saida,
        FILTRO_FIELDS,
        progresso=(lambda feitos: progresso(feitos, n_pendentes)) if progresso else None,
    )
    return [processados[c["full_name"]] for c in candidatos]


def usa_actions(linha: dict) -> bool:
    """Le a coluna `usa_actions`, que vem como texto quando carregada do CSV."""
    return str(linha["usa_actions"]) == "True"
