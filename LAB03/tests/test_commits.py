"""Testes da coleta de commits entre releases. As respostas da API sao simuladas."""

from __future__ import annotations

import pytest
import requests

from pipeline.commits import (
    MOTIVO_COMPARE_404,
    MOTIVO_PRIMEIRA_RELEASE,
    coletar_commits_entre_releases,
    comparar_commits,
    datas_de_autor,
    montar_releases_com_commits,
)


def release(tag: str, published_at: str) -> dict:
    return {"tag_name": tag, "published_at": published_at}


def commit_api(data: str) -> dict:
    return {"commit": {"author": {"date": data}}}


def http_error_404() -> requests.HTTPError:
    response = requests.Response()
    response.status_code = 404
    return requests.HTTPError("HTTP 404", response=response)


class FakeClient:
    """`respostas` mapeia "base...head" -> lista de commits ou uma excecao."""

    def __init__(self, respostas: dict):
        self.respostas = respostas
        self.consultas: list[tuple[str, int]] = []

    def get(self, path, params=None):
        chave = path.rsplit("/compare/", 1)[1]
        self.consultas.append((chave, params["page"]))
        resposta = self.respostas[chave]
        if isinstance(resposta, Exception):
            raise resposta
        pagina = params["page"]
        inicio = (pagina - 1) * params["per_page"]
        commits = resposta[inicio : inicio + params["per_page"]]
        return {"commits": commits}


def test_datas_de_autor_extrai_a_data_do_commit():
    commits = [commit_api("2024-01-01T00:00:00Z"), commit_api("2024-01-02T00:00:00Z")]
    assert datas_de_autor(commits) == ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"]


def test_comparar_commits_segue_paginacao_ate_esgotar(monkeypatch):
    import pipeline.commits as commits_mod

    monkeypatch.setattr(commits_mod, "COMMITS_POR_PAGINA", 2)
    client = FakeClient({"v1...v2": [commit_api("d1"), commit_api("d2"), commit_api("d3")]})

    resultado = comparar_commits(client, "org/a", "v1", "v2")

    assert len(resultado) == 3
    assert client.consultas == [("v1...v2", 1), ("v1...v2", 2)]


def test_montar_releases_com_commits_ignora_a_primeira_release():
    client = FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z")]})
    releases = [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases)

    assert len(resultado) == 1
    assert resultado[0]["tag_name"] == "v2"
    assert resultado[0]["commits"] == ["2024-01-05T00:00:00Z"]
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 1, MOTIVO_COMPARE_404: 0}


def test_montar_releases_com_commits_sem_releases_nao_conta_primeira():
    resultado, motivos = montar_releases_com_commits(FakeClient({}), "org/a", [])
    assert resultado == []
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 0, MOTIVO_COMPARE_404: 0}


def test_compare_404_e_ignorado_e_contado():
    client = FakeClient(
        {
            "v1...v2": http_error_404(),
            "v2...v3": [commit_api("2024-02-05T00:00:00Z")],
        }
    )
    releases = [
        release("v1", "2024-01-01T00:00:00Z"),
        release("v2", "2024-01-10T00:00:00Z"),
        release("v3", "2024-02-10T00:00:00Z"),
    ]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases)

    assert [r["tag_name"] for r in resultado] == ["v3"]
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 1, MOTIVO_COMPARE_404: 1}


def test_erro_http_diferente_de_404_e_propagado():
    response = requests.Response()
    response.status_code = 500
    erro = requests.HTTPError("HTTP 500", response=response)
    client = FakeClient({"v1...v2": erro})
    releases = [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]

    with pytest.raises(requests.HTTPError):
        montar_releases_com_commits(client, "org/a", releases)


def test_coletar_commits_entre_releases_usa_cache(tmp_path):
    client = FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z")]})
    repositorios = {
        "org/a": [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]
    }

    coletar_commits_entre_releases(client, repositorios, tmp_path)
    assert client.consultas

    client_2 = FakeClient({})
    resultado = coletar_commits_entre_releases(client_2, repositorios, tmp_path)

    assert client_2.consultas == []
    assert resultado["org/a"]["releases"][0]["tag_name"] == "v2"


def test_coletar_commits_entre_releases_informa_progresso(tmp_path):
    client = FakeClient({"v1...v2": [], "v3...v4": []})
    repositorios = {
        "org/a": [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")],
        "org/b": [release("v3", "2024-02-01T00:00:00Z"), release("v4", "2024-02-10T00:00:00Z")],
    }
    chamadas = []
    coletar_commits_entre_releases(
        client, repositorios, tmp_path, progresso=lambda feitos, total: chamadas.append((feitos, total))
    )
    assert chamadas == [(1, 2), (2, 2)]
