"""Coleta de releases (`GET /repos/{full_name}/releases`).

Cada repositorio tem sua lista de releases cacheada num JSON proprio em
`cache_dir/releases/`, para que uma coleta interrompida (rate limit, queda de
rede, Ctrl+C) retome sem repetir chamadas ja feitas.

A definicao principal do enunciado (secao 3) considera deploy = release com
`draft = false` e `prerelease = false`. Pre-releases ficam de fora dessa
definicao e so aparecem como variante na RQ 07; por isso sao mantidas no cache
(dado bruto), e filtradas depois por `releases_principais`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pipeline.github_client import GitHubClient

CACHE_SUBDIR = "releases"


def _caminho_cache(cache_dir: str | Path, full_name: str) -> Path:
    return Path(cache_dir) / CACHE_SUBDIR / f"{full_name.replace('/', '__')}.json"


def coletar_releases_repositorio(client: GitHubClient, full_name: str) -> list[dict]:
    """Busca todas as releases de um repositorio, da mais antiga para a mais nova.

    A API devolve as releases da mais nova para a mais antiga; a ordem e
    invertida aqui porque o calculo de lead time percorre as releases em
    ordem cronologica.
    """
    releases = [
        {
            "id": r["id"],
            "tag_name": r["tag_name"],
            "target_commitish": r["target_commitish"],
            "draft": r["draft"],
            "prerelease": r["prerelease"],
            "published_at": r["published_at"],
        }
        for r in client.get_paginated(f"/repos/{full_name}/releases")
    ]
    releases.sort(key=lambda r: r["published_at"] or "")
    return releases


def coletar_releases(
    client: GitHubClient,
    full_names: list[str],
    cache_dir: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[str, list[dict]]:
    """Coleta as releases de varios repositorios, reaproveitando o cache existente.

    Devolve um dicionario `full_name -> releases`, na mesma ordem de entrada.
    """
    cache_dir = Path(cache_dir)
    resultado: dict[str, list[dict]] = {}
    pendentes = []
    for full_name in full_names:
        caminho = _caminho_cache(cache_dir, full_name)
        if caminho.exists():
            resultado[full_name] = json.loads(caminho.read_text(encoding="utf-8"))
        else:
            pendentes.append(full_name)

    for i, full_name in enumerate(pendentes, start=1):
        releases = coletar_releases_repositorio(client, full_name)
        caminho = _caminho_cache(cache_dir, full_name)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(releases), encoding="utf-8")
        resultado[full_name] = releases
        if progresso:
            progresso(i, len(pendentes))

    return {full_name: resultado[full_name] for full_name in full_names}


def releases_principais(releases: list[dict]) -> list[dict]:
    """Filtra a definicao principal de deploy: nao-draft e nao-prerelease."""
    return [r for r in releases if not r["draft"] and not r["prerelease"]]


def releases_na_janela(releases: list[dict], inicio: str, fim: str) -> list[dict]:
    """Filtra releases publicadas dentro da janela `[inicio, fim)` (datas ISO)."""
    return [r for r in releases if r["published_at"] and inicio <= r["published_at"] < fim]
