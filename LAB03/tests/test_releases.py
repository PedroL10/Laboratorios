"""Testes da coleta de releases. As respostas da API sao simuladas."""

from __future__ import annotations

import json

from pipeline.releases import (
    coletar_releases,
    coletar_releases_repositorio,
    releases_na_janela,
    releases_principais,
)


def release_api(tag: str, published_at: str, draft: bool = False, prerelease: bool = False) -> dict:
    return {
        "id": hash(tag) % 10_000,
        "tag_name": tag,
        "target_commitish": "main",
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published_at,
    }


class FakeClient:
    """`respostas` mapeia full_name -> lista de releases (na ordem "mais nova primeiro")."""

    def __init__(self, respostas: dict[str, list[dict]]):
        self.respostas = respostas
        self.consultados: list[str] = []

    def get_paginated(self, path, params=None, items_key=None, max_pages=None):
        full_name = path.removeprefix("/repos/").removesuffix("/releases")
        self.consultados.append(full_name)
        yield from self.respostas[full_name]


def test_coletar_releases_repositorio_ordena_da_mais_antiga_para_a_mais_nova():
    client = FakeClient(
        {
            "org/a": [
                release_api("v2", "2024-02-01T00:00:00Z"),
                release_api("v1", "2024-01-01T00:00:00Z"),
            ]
        }
    )
    releases = coletar_releases_repositorio(client, "org/a")
    assert [r["tag_name"] for r in releases] == ["v1", "v2"]


def test_releases_principais_filtra_draft_e_prerelease():
    releases = [
        release_api("v1", "2024-01-01T00:00:00Z"),
        release_api("v2-rc1", "2024-01-05T00:00:00Z", prerelease=True),
        release_api("v2", "2024-01-10T00:00:00Z"),
        release_api("v3-draft", "2024-01-15T00:00:00Z", draft=True),
    ]
    assert [r["tag_name"] for r in releases_principais(releases)] == ["v1", "v2"]


def test_releases_na_janela_filtra_pelo_intervalo():
    releases = [
        release_api("antes", "2023-12-31T23:59:59Z"),
        release_api("dentro", "2024-06-01T00:00:00Z"),
        release_api("depois", "2025-01-01T00:00:00Z"),
    ]
    janela = releases_na_janela(releases, "2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")
    assert [r["tag_name"] for r in janela] == ["dentro"]


def test_coletar_releases_usa_cache_e_nao_consulta_de_novo(tmp_path):
    client = FakeClient({"org/a": [release_api("v1", "2024-01-01T00:00:00Z")]})
    coletar_releases(client, ["org/a"], tmp_path)
    assert client.consultados == ["org/a"]

    cliente_2 = FakeClient({"org/a": [release_api("v1", "2024-01-01T00:00:00Z")]})
    resultado = coletar_releases(cliente_2, ["org/a"], tmp_path)

    assert cliente_2.consultados == []
    assert resultado["org/a"][0]["tag_name"] == "v1"


def test_coletar_releases_grava_um_json_por_repositorio(tmp_path):
    client = FakeClient(
        {
            "org/a": [release_api("v1", "2024-01-01T00:00:00Z")],
            "org/b": [release_api("v1", "2024-02-01T00:00:00Z")],
        }
    )
    coletar_releases(client, ["org/a", "org/b"], tmp_path)

    caminho = tmp_path / "releases" / "org__a.json"
    assert json.loads(caminho.read_text(encoding="utf-8"))[0]["tag_name"] == "v1"


def test_coletar_releases_so_busca_os_pendentes(tmp_path):
    client = FakeClient({"org/a": [release_api("v1", "2024-01-01T00:00:00Z")]})
    coletar_releases(client, ["org/a"], tmp_path)

    client_2 = FakeClient(
        {
            "org/a": [release_api("v1", "2024-01-01T00:00:00Z")],
            "org/b": [release_api("v1", "2024-02-01T00:00:00Z")],
        }
    )
    resultado = coletar_releases(client_2, ["org/a", "org/b"], tmp_path)

    assert client_2.consultados == ["org/b"]
    assert list(resultado) == ["org/a", "org/b"]


def test_coletar_releases_informa_progresso(tmp_path):
    client = FakeClient(
        {
            "org/a": [release_api("v1", "2024-01-01T00:00:00Z")],
            "org/b": [release_api("v1", "2024-02-01T00:00:00Z")],
        }
    )
    chamadas = []
    coletar_releases(
        client, ["org/a", "org/b"], tmp_path, progresso=lambda feitos, total: chamadas.append((feitos, total))
    )
    assert chamadas == [(1, 2), (2, 2)]
