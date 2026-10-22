"""Testes da coleta de tags via GraphQL. As respostas da API sao simuladas."""

from __future__ import annotations

import pytest

from pipeline.criterio_inclusao import Janela
from pipeline.github_client import GraphQLError
from pipeline.tags import coletar_tags, coletar_tags_repositorio, data_do_commit

JANELA = Janela("2024-01-01", "2024-12-31")


def tag_leve(nome: str, data: str) -> dict:
    return {"name": nome, "target": {"committedDate": data}}


def tag_anotada(nome: str, data: str) -> dict:
    return {"name": nome, "target": {"target": {"committedDate": data}}}


class FakeClient:
    """`paginas` sao listas de nos de tag, ja na ordem da API (mais nova primeiro)."""

    def __init__(self, paginas: list[list[dict]] | Exception):
        self.paginas = paginas
        self.cursores: list[str | None] = []

    def graphql(self, query, variables=None):
        if isinstance(self.paginas, Exception):
            raise self.paginas
        assert variables["owner"] == "org" and variables["name"] == "a"
        self.cursores.append(variables["cursor"])
        indice = 0 if variables["cursor"] is None else int(variables["cursor"])
        return {
            "repository": {
                "refs": {
                    "pageInfo": {
                        "hasNextPage": indice + 1 < len(self.paginas),
                        "endCursor": str(indice + 1),
                    },
                    "nodes": self.paginas[indice],
                }
            }
        }


def test_data_do_commit_de_tag_leve_e_anotada():
    assert data_do_commit(tag_leve("v1", "2024-01-01T00:00:00Z")) == "2024-01-01T00:00:00Z"
    assert data_do_commit(tag_anotada("v1", "2024-02-01T00:00:00Z")) == "2024-02-01T00:00:00Z"
    # Tag que aponta para uma arvore ou blob: sem data.
    assert data_do_commit({"name": "x", "target": {}}) is None
    assert data_do_commit({"name": "x", "target": None}) is None


def test_para_na_primeira_tag_anterior_a_janela_e_guarda_ela_como_base():
    client = FakeClient(
        [
            [tag_leve("v3", "2024-06-01T00:00:00Z"), tag_anotada("v2", "2024-02-01T00:00:00Z")],
            [tag_leve("v1", "2023-12-01T00:00:00Z"), tag_leve("v0", "2023-01-01T00:00:00Z")],
            [tag_leve("nunca-lida", "2022-01-01T00:00:00Z")],
        ]
    )
    tags = coletar_tags_repositorio(client, "org/a", JANELA)

    assert [t["tag_name"] for t in tags] == ["v1", "v2", "v3"]
    assert tags[0]["published_at"] == "2023-12-01T00:00:00Z"
    assert client.cursores == [None, "1"]


def test_descarta_tag_sem_data_e_termina_quando_as_paginas_acabam():
    client = FakeClient(
        [[tag_leve("v2", "2024-06-01T00:00:00Z"), {"name": "arvore", "target": {}}, tag_leve("v1", "2024-02-01T00:00:00Z")]]
    )
    tags = coletar_tags_repositorio(client, "org/a", JANELA)
    assert [t["tag_name"] for t in tags] == ["v1", "v2"]


def test_repositorio_que_nao_existe_mais_fica_sem_tags():
    client = FakeClient(GraphQLError([{"type": "NOT_FOUND", "message": "nao existe"}]))
    assert coletar_tags_repositorio(client, "org/a", JANELA) == []


def test_outros_erros_graphql_sao_propagados():
    client = FakeClient(GraphQLError([{"type": "FORBIDDEN", "message": "proibido"}]))
    with pytest.raises(GraphQLError):
        coletar_tags_repositorio(client, "org/a", JANELA)


def test_coletar_tags_usa_cache_e_refaz_cache_de_outra_janela(tmp_path):
    paginas = [[tag_leve("v1", "2024-06-01T00:00:00Z")]]
    coletar_tags(FakeClient(paginas), ["org/a"], JANELA, tmp_path)

    client = FakeClient(paginas)
    resultado = coletar_tags(client, ["org/a"], JANELA, tmp_path)
    assert client.cursores == []
    assert resultado["org/a"][0]["tag_name"] == "v1"

    client = FakeClient(paginas)
    coletar_tags(client, ["org/a"], Janela("2024-01-01", "2024-06-30"), tmp_path)
    assert client.cursores == [None]


def test_coletar_tags_informa_progresso(tmp_path):
    chamadas = []
    coletar_tags(
        FakeClient([[]]), ["org/a"], JANELA, tmp_path, progresso=lambda f, t: chamadas.append((f, t))
    )
    assert chamadas == [(1, 1)]
    assert (tmp_path / "tags" / "org__a.json").exists()
