"""Coleta de commits entre releases (`GET /repos/{full_name}/compare/{base}...{head}`),
usada para calcular o lead time (RQ 02).

Para cada release R (exceto a primeira da historia do repositorio, que nao tem
release anterior), os commits incluidos sao obtidos comparando R com a release
anterior. O resultado e uma lista no formato esperado por
`metricas.lead_time.lead_time_repositorio`.

O endpoint de comparacao nao pagina oficialmente, mas devolve no maximo 250
commits por chamada (secao 4 do enunciado); `comparar_commits` insiste com
`per_page`/`page` ate esgotar.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import requests

from pipeline.github_client import GitHubClient

CACHE_SUBDIR = "commits_entre_releases"
COMMITS_POR_PAGINA = 250

MOTIVO_PRIMEIRA_RELEASE = "primeira_release"
MOTIVO_COMPARE_404 = "compare_404"


def _caminho_cache(cache_dir: str | Path, full_name: str) -> Path:
    return Path(cache_dir) / CACHE_SUBDIR / f"{full_name.replace('/', '__')}.json"


def comparar_commits(client: GitHubClient, full_name: str, base: str, head: str) -> list[dict]:
    """Devolve os commits entre `base` (exclusive) e `head` (inclusive)."""
    commits: list[dict] = []
    pagina = 1
    while True:
        resposta = client.get(
            f"/repos/{full_name}/compare/{base}...{head}",
            {"per_page": COMMITS_POR_PAGINA, "page": pagina},
        )
        pagina_commits = resposta["commits"]
        commits.extend(pagina_commits)
        if len(pagina_commits) < COMMITS_POR_PAGINA:
            break
        pagina += 1
    return commits


def datas_de_autor(commits: list[dict]) -> list[str]:
    """Extrai `commit.author.date` de cada commit retornado pelo compare."""
    return [c["commit"]["author"]["date"] for c in commits]


def montar_releases_com_commits(
    client: GitHubClient, full_name: str, releases_ordenadas: list[dict]
) -> tuple[list[dict], dict[str, int]]:
    """Monta, para cada release com release anterior, a lista de commits incluidos.

    `releases_ordenadas` deve conter apenas as releases da definicao principal
    (ver `pipeline.releases.releases_principais`), em ordem cronologica.

    Devolve `(releases_com_commits, motivos_ignoradas)`: as releases prontas
    para `metricas.lead_time.lead_time_repositorio` e a contagem de releases
    ignoradas por motivo, usada no funil/ameacas a validade.
    """
    resultado: list[dict] = []
    motivos = {MOTIVO_PRIMEIRA_RELEASE: 0, MOTIVO_COMPARE_404: 0}

    if releases_ordenadas:
        motivos[MOTIVO_PRIMEIRA_RELEASE] = 1

    for anterior, atual in zip(releases_ordenadas, releases_ordenadas[1:]):
        try:
            commits = comparar_commits(client, full_name, anterior["tag_name"], atual["tag_name"])
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 404:
                motivos[MOTIVO_COMPARE_404] += 1
                continue
            raise
        resultado.append(
            {
                "tag_name": atual["tag_name"],
                "published_at": atual["published_at"],
                "commits": datas_de_autor(commits),
            }
        )

    return resultado, motivos


def coletar_commits_entre_releases(
    client: GitHubClient,
    repositorios: dict[str, list[dict]],
    cache_dir: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[str, dict]:
    """Para cada repositorio, monta as releases com commits, reaproveitando o cache.

    `repositorios` mapeia `full_name -> releases principais ordenadas` (ja
    filtradas por `releases_principais`/`releases_na_janela`).
    Devolve `full_name -> {"releases": [...], "motivos_ignoradas": {...}}`.
    """
    cache_dir = Path(cache_dir)
    resultado: dict[str, dict] = {}
    pendentes = []
    for full_name in repositorios:
        caminho = _caminho_cache(cache_dir, full_name)
        if caminho.exists():
            resultado[full_name] = json.loads(caminho.read_text(encoding="utf-8"))
        else:
            pendentes.append(full_name)

    for i, full_name in enumerate(pendentes, start=1):
        releases, motivos = montar_releases_com_commits(client, full_name, repositorios[full_name])
        dados = {"releases": releases, "motivos_ignoradas": motivos}
        caminho = _caminho_cache(cache_dir, full_name)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        resultado[full_name] = dados
        if progresso:
            progresso(i, len(pendentes))

    return {full_name: resultado[full_name] for full_name in repositorios}
