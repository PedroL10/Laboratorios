"""Monta a planilha da amostra-ouro para a validacao manual (secao 6 do enunciado).

Este modulo so automatiza a parte **reproduzivel e mecanica** da validacao: o
sorteio dos 60 repositorios e de 5 releases por repositorio, com semente fixa, e
a montagem de uma planilha com link direto para cada release (a "dica" da
secao 6). As colunas de julgamento -- tipo do projeto, se as releases
representam entregas reais, e se cada release sorteada e corretiva -- saem
vazias: cada integrante preenche a sua copia de forma independente, sem
consultar os demais nem a saida da heuristica automatica (`metricas.cfr`).
"""

from __future__ import annotations

import random

CAMPOS_PLANILHA = [
    "full_name",
    "link_repositorio",
    "tipo_projeto",
    "releases_representam_entrega_real",
    "tag_name",
    "link_release",
    "corretiva",
]


def sortear_amostra_ouro(amostra: list[dict], n: int = 60, seed: int = 42) -> list[dict]:
    """Sorteia `n` repositorios da amostra final, com semente fixa e reproduzivel."""
    return random.Random(seed).sample(amostra, k=min(n, len(amostra)))


def sortear_releases(
    releases: list[dict], full_name: str, n: int = 5, seed: int = 42
) -> list[dict]:
    """Sorteia `n` releases de um repositorio, com semente fixa por repositorio.

    A semente combina `seed` com `full_name` para que cada repositorio tenha um
    sorteio proprio e reproduzivel, mas diferente dos demais.
    """
    rng = random.Random(f"{seed}:{full_name}")
    return rng.sample(releases, k=min(n, len(releases)))


def gerar_linhas_planilha(
    amostra_ouro: list[dict],
    releases_por_repo: dict[str, list[dict]],
    n_releases_por_repo: int = 5,
    seed: int = 42,
) -> list[dict]:
    """Monta uma linha por release sorteada, pronta para `pipeline.selecao.salvar_csv`.

    `releases_por_repo` mapeia `full_name -> releases principais da janela`
    (ver `pipeline.releases.releases_principais`/`releases_na_janela`).
    """
    linhas = []
    for repo in amostra_ouro:
        full_name = repo["full_name"]
        releases = sortear_releases(
            releases_por_repo.get(full_name, []), full_name, n_releases_por_repo, seed
        )
        if not releases:
            linhas.append(
                {
                    "full_name": full_name,
                    "link_repositorio": f"https://github.com/{full_name}",
                    "tipo_projeto": "",
                    "releases_representam_entrega_real": "",
                    "tag_name": "",
                    "link_release": "",
                    "corretiva": "",
                }
            )
            continue
        for release in releases:
            linhas.append(
                {
                    "full_name": full_name,
                    "link_repositorio": f"https://github.com/{full_name}",
                    "tipo_projeto": "",
                    "releases_representam_entrega_real": "",
                    "tag_name": release["tag_name"],
                    "link_release": f"https://github.com/{full_name}/releases/tag/{release['tag_name']}",
                    "corretiva": "",
                }
            )
    return linhas
