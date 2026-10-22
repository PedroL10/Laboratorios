"""Coleta de tags com a data do commit apontado, para a variante "tag" da RQ 07.

Tags nao trazem data; o enunciado (secao 4) manda usar a data do commit para o
qual a tag aponta. Na API REST isso custaria uma chamada por tag
(`/tags` + `/commits/{sha}`), e ha repositorios com milhares de tags. Por isso
a coleta usa a API GraphQL, que lista as tags (`refs/tags/`) ja ordenadas pela
data do commit, da mais nova para a mais antiga, 100 por chamada: a paginacao
para assim que encontra a primeira tag anterior ao inicio da janela, que e
guardada como base do compare da primeira tag da janela (como em `pipeline.commits`).

A data usada e o `committedDate` do commit (quando ele entrou no repositorio).
Tags anotadas apontam para um objeto Tag, que por sua vez aponta para o commit;
os dois casos sao tratados. Tags que apontam para outra coisa (arvore, blob) nao
tem data e sao descartadas.

Cada repositorio tem as suas tags cacheadas num JSON proprio em
`cache_dir/tags/`, junto com a janela usada (a parada depende do inicio dela).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pipeline.criterio_inclusao import Janela, parse_data
from pipeline.github_client import GitHubClient, GraphQLError
from pipeline.retomada import gravar_json

CACHE_SUBDIR = "tags"

CONSULTA_TAGS = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    refs(refPrefix: "refs/tags/", first: 100, after: $cursor,
         orderBy: {field: TAG_COMMIT_DATE, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        target {
          ... on Commit { committedDate }
          ... on Tag { target { ... on Commit { committedDate } } }
        }
      }
    }
  }
}
"""


def _caminho_cache(cache_dir: str | Path, full_name: str) -> Path:
    return Path(cache_dir) / CACHE_SUBDIR / f"{full_name.replace('/', '__')}.json"


def data_do_commit(no: dict) -> str | None:
    """`committedDate` do commit apontado pela tag (leve ou anotada), ou None."""
    alvo = no.get("target") or {}
    if "committedDate" in alvo:
        return alvo["committedDate"]
    return (alvo.get("target") or {}).get("committedDate")


def coletar_tags_repositorio(client: GitHubClient, full_name: str, janela: Janela) -> list[dict]:
    """Tags da janela (e as posteriores a ela) mais a ultima tag anterior a janela.

    Devolve as tags em ordem cronologica, no formato de release usado por
    `pipeline.commits` e `metricas`: `{"tag_name", "published_at"}`, em que
    `published_at` e a data do commit apontado. Um repositorio que nao existe
    mais (apagado ou renomeado depois da selecao) fica sem tags.
    """
    owner, name = full_name.split("/", 1)
    tags: list[dict] = []
    cursor = None
    while True:
        try:
            dados = client.graphql(CONSULTA_TAGS, {"owner": owner, "name": name, "cursor": cursor})
        except GraphQLError as exc:
            if "NOT_FOUND" in exc.tipos:
                return []
            raise
        refs = dados["repository"]["refs"]
        for no in refs["nodes"]:
            data = data_do_commit(no)
            if data is None:
                continue
            tags.append({"tag_name": no["name"], "published_at": data})
            if parse_data(data) < janela.inicio:
                # A primeira tag anterior a janela e a base do compare: basta ela.
                return sorted(tags, key=lambda t: t["published_at"])
        if not refs["pageInfo"]["hasNextPage"]:
            return sorted(tags, key=lambda t: t["published_at"])
        cursor = refs["pageInfo"]["endCursor"]


def coletar_tags(
    client: GitHubClient,
    full_names: list[str],
    janela: Janela,
    cache_dir: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[str, list[dict]]:
    """Coleta as tags de varios repositorios, reaproveitando o cache existente.

    Devolve `full_name -> tags em ordem cronologica`, na ordem de entrada.
    Um cache de outra janela e refeito.
    """
    cache_dir = Path(cache_dir)
    chave_janela = janela.filtro_created()
    resultado: dict[str, list[dict]] = {}
    pendentes = []
    for full_name in full_names:
        caminho = _caminho_cache(cache_dir, full_name)
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if dados.get("janela") == chave_janela:
                resultado[full_name] = dados["tags"]
                continue
        pendentes.append(full_name)

    for i, full_name in enumerate(pendentes, start=1):
        tags = coletar_tags_repositorio(client, full_name, janela)
        caminho = _caminho_cache(cache_dir, full_name)
        gravar_json(caminho, {"janela": chave_janela, "tags": tags})
        resultado[full_name] = tags
        if progresso:
            progresso(i, len(pendentes))

    return {full_name: resultado[full_name] for full_name in full_names}
