"""Metadados dos repositorios da amostra (fatores da RQ 06).

Estrelas, linguagem e data de criacao ja vem da busca (candidatos.csv). Este modulo
acrescenta:
- `n_contribuidores`: pela dica da secao 4 do enunciado, com
  `GET /repos/{owner}/{repo}/contributors?per_page=1&anon=true` o numero da ultima
  pagina no cabecalho `Link` (rel="last") e o total de contribuidores, ao custo de
  uma unica chamada. `anon=true` inclui contribuidores sem conta no GitHub.
- `idade_dias`: idade do repositorio no ultimo dia da janela de observacao (data
  fixa, para o valor nao mudar conforme o dia da coleta).

O GitHub nao lista contribuidores de repositorios com historico muito grande
(responde 403 com "contributor list is too large"). Nesses casos o valor fica vazio
e `erro_contribuidores` recebe "lista_muito_grande".
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import requests

from pipeline.criterio_inclusao import parse_data
from pipeline.github_client import GitHubClient, erro_transitorio, status_http
from pipeline.retomada import processar_com_retomada

CONTRIBUIDORES_FIELDS = ["full_name", "n_contribuidores", "erro_contribuidores"]

METADADOS_FIELDS = ["n_contribuidores", "erro_contribuidores", "idade_dias"]

ERRO_LISTA_MUITO_GRANDE = "lista_muito_grande"


def numero_ultima_pagina(response: requests.Response) -> int | None:
    """Le o parametro `page` do link rel="last" do cabecalho `Link` (None se nao houver)."""
    url = response.links.get("last", {}).get("url")
    if not url:
        return None
    return int(parse_qs(urlparse(url).query)["page"][0])


def contar_contribuidores(client: GitHubClient, full_name: str) -> dict:
    """Conta os contribuidores (inclusive anonimos) com uma unica chamada."""
    linha = {"full_name": full_name, "n_contribuidores": None, "erro_contribuidores": ""}
    try:
        response = client.get_response(
            f"/repos/{full_name}/contributors", {"per_page": 1, "anon": "true"}
        )
    except requests.HTTPError as exc:
        # Cota esgotada ou erro temporario nao e resultado: interrompe para retomar depois.
        if erro_transitorio(exc):
            raise
        if status_http(exc) == 403 and "too large" in exc.response.text:
            linha["erro_contribuidores"] = ERRO_LISTA_MUITO_GRANDE
        else:
            linha["erro_contribuidores"] = f"erro_http_{status_http(exc)}"
        return linha

    if response.status_code == 204:  # repositorio vazio
        linha["n_contribuidores"] = 0
        return linha

    ultima = numero_ultima_pagina(response)
    # Sem link "last" ha uma unica pagina: 0 ou 1 contribuidor.
    linha["n_contribuidores"] = ultima if ultima is not None else len(response.json())
    return linha


def idade_dias(created_at: str, referencia: date) -> int:
    """Dias entre a criacao do repositorio e a data de referencia (fim da janela)."""
    return (referencia - parse_data(created_at).date()).days


def coletar_contribuidores(
    client: GitHubClient,
    repositorios: list[dict],
    caminho_saida: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[str, dict]:
    """Conta os contribuidores de cada repositorio, com retomada pelo CSV de saida."""
    return processar_com_retomada(
        repositorios,
        lambda repo: contar_contribuidores(client, repo["full_name"]),
        caminho_saida,
        CONTRIBUIDORES_FIELDS,
        progresso=(lambda feitos: progresso(feitos, len(repositorios))) if progresso else None,
    )


def enriquecer_amostra(
    amostra: list[dict], contribuidores: dict[str, dict], fim_janela: date
) -> list[dict]:
    """Acrescenta contribuidores e idade a cada repositorio da amostra."""
    enriquecida = []
    for repo in amostra:
        dados = contribuidores[repo["full_name"]]
        enriquecida.append(
            {
                **repo,
                "n_contribuidores": dados["n_contribuidores"],
                "erro_contribuidores": dados["erro_contribuidores"],
                "idade_dias": idade_dias(repo["created_at"], fim_janela),
            }
        )
    return enriquecida
