"""Testes da coleta de commits entre releases. As respostas da API sao simuladas."""

from __future__ import annotations

import pytest
import requests

from pipeline.commits import (
    CacheCompares,
    MOTIVO_COMPARE_404,
    MOTIVO_PRIMEIRA_RELEASE,
    coletar_commits_entre_releases,
    comparar_commits,
    datas_de_autor,
    mensagens_de_commit,
    montar_releases_com_commits,
)
from pipeline.criterio_inclusao import Janela
from metricas.lead_time import lead_time_repositorio

JANELA = Janela("2024-01-01", "2024-12-31")


def release(tag: str, published_at: str) -> dict:
    return {"tag_name": tag, "published_at": published_at}


def commit_api(data: str, mensagem: str = "") -> dict:
    return {"commit": {"author": {"date": data}, "message": mensagem}}


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


def test_mensagens_de_commit_extrai_a_mensagem_do_commit():
    commits = [commit_api("2024-01-01T00:00:00Z", "fix: crash"), commit_api("2024-01-02T00:00:00Z", "feat: x")]
    assert mensagens_de_commit(commits) == ["fix: crash", "feat: x"]


def test_mensagens_de_commit_sem_campo_message_devolve_vazio():
    assert mensagens_de_commit([{"commit": {"author": {"date": "d"}}}]) == [""]


def test_montar_releases_com_commits_ignora_a_primeira_release():
    client = FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z", "fix: crash")]})
    releases = [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases)

    assert len(resultado) == 1
    assert resultado[0]["tag_name"] == "v2"
    assert resultado[0]["tag_anterior"] == "v1"
    assert resultado[0]["commits"] == ["2024-01-05T00:00:00Z"]
    assert resultado[0]["mensagens_commits"] == ["fix: crash"]
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 1, MOTIVO_COMPARE_404: 0}


def test_release_anterior_fora_da_janela_e_usada_como_base_do_compare():
    client = FakeClient(
        {
            "v1...v2": [commit_api("2024-01-05T00:00:00Z")],
            "v2...v3": [commit_api("2024-02-05T00:00:00Z")],
        }
    )
    releases = [
        release("v1", "2023-12-01T00:00:00Z"),
        release("v2", "2023-12-20T00:00:00Z"),
        release("v3", "2024-02-10T00:00:00Z"),
    ]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases, JANELA)

    # v1 e v2 estao fora da janela: so v3 e calculada, comparada com v2.
    assert [(r["tag_anterior"], r["tag_name"]) for r in resultado] == [("v2", "v3")]
    assert [chave for chave, _ in client.consultas] == ["v2...v3"]
    # A primeira release da historia (v1) nao esta na janela: nada a ignorar.
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 0, MOTIVO_COMPARE_404: 0}


def test_primeira_release_da_historia_dentro_da_janela_e_ignorada_e_contada():
    client = FakeClient({"v1...v2": [commit_api("2024-03-01T00:00:00Z")]})
    releases = [release("v1", "2024-02-01T00:00:00Z"), release("v2", "2024-03-10T00:00:00Z")]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases, JANELA)

    assert [r["tag_name"] for r in resultado] == ["v2"]
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 1, MOTIVO_COMPARE_404: 0}


def test_repositorio_com_uma_unica_release_nao_tem_lead_time():
    client = FakeClient({})
    releases = [release("v1", "2024-02-01T00:00:00Z")]

    resultado, motivos = montar_releases_com_commits(client, "org/a", releases, JANELA)

    assert resultado == []
    assert client.consultas == []
    assert motivos == {MOTIVO_PRIMEIRA_RELEASE: 1, MOTIVO_COMPARE_404: 0}


def test_release_sem_commits_novos_entra_com_lista_vazia():
    client = FakeClient({"v1...v1-republicada": []})
    releases = [
        release("v1", "2024-02-01T00:00:00Z"),
        release("v1-republicada", "2024-02-02T00:00:00Z"),
    ]

    resultado, _ = montar_releases_com_commits(client, "org/a", releases, JANELA)

    assert resultado[0]["commits"] == []
    # Sem commits novos, a release fica sem lead time (nao vira zero).
    assert lead_time_repositorio(resultado)["n_releases_variante_a"] == 0


def test_releases_depois_da_janela_nao_sao_comparadas():
    client = FakeClient({"v1...v2": [commit_api("2024-12-01T00:00:00Z")]})
    releases = [release("v1", "2024-11-01T00:00:00Z"), release("v2", "2025-01-02T00:00:00Z")]

    resultado, _ = montar_releases_com_commits(client, "org/a", releases, JANELA)

    assert resultado == []
    assert client.consultas == []


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


def test_cache_de_outra_janela_e_refeito(tmp_path):
    repositorios = {
        "org/a": [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]
    }
    coletar_commits_entre_releases(
        FakeClient({"v1...v2": []}), repositorios, tmp_path, janela=Janela("2023-01-01", "2023-12-31")
    )

    client = FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z")]})
    resultado = coletar_commits_entre_releases(client, repositorios, tmp_path, janela=JANELA)

    assert client.consultas == [("v1...v2", 1)]
    assert resultado["org/a"]["janela"] == "2024-01-01..2024-12-31"
    assert resultado["org/a"]["releases"][0]["commits"] == ["2024-01-05T00:00:00Z"]


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


def test_variantes_reaproveitam_pares_ja_comparados_e_tem_cache_proprio(tmp_path):
    repositorios = {
        "org/a": [release("v1", "2024-01-01T00:00:00Z"), release("v2", "2024-01-10T00:00:00Z")]
    }
    coletar_commits_entre_releases(
        FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z")]}), repositorios, tmp_path, janela=JANELA
    )

    # Mesma lista em outra variante (ex.: tags = releases): nenhum compare novo.
    client = FakeClient({})
    resultado = coletar_commits_entre_releases(
        client, repositorios, tmp_path, janela=JANELA, subdir="commits_variante_tag"
    )
    assert client.consultas == []
    assert resultado["org/a"]["releases"][0]["commits"] == ["2024-01-05T00:00:00Z"]
    assert (tmp_path / "commits_variante_tag" / "org__a.json").exists()

    # Uma pre-release no meio cria pares novos: so eles vao a API.
    com_pre = {
        "org/a": [
            release("v1", "2024-01-01T00:00:00Z"),
            release("v2-rc1", "2024-01-05T00:00:00Z"),
            release("v2", "2024-01-10T00:00:00Z"),
        ]
    }
    client = FakeClient({"v1...v2-rc1": [], "v2-rc1...v2": []})
    coletar_commits_entre_releases(client, com_pre, tmp_path, janela=JANELA, subdir="commits_variante_pre")
    assert sorted(chave for chave, _ in client.consultas) == ["v1...v2-rc1", "v2-rc1...v2"]


def test_compare_404_fica_no_cache_de_pares():
    compares = CacheCompares()
    client = FakeClient({"v1...v2": http_error_404()})
    assert compares.obter(client, "org/a", "v1", "v2") == {"status": 404}
    assert compares.obter(FakeClient({}), "org/a", "v1", "v2") == {"status": 404}
    assert len(client.consultas) == 1


def test_pares_comparados_sao_gravados_mesmo_se_a_coleta_parar_no_meio(tmp_path):
    erro = requests.HTTPError("HTTP 500", response=requests.Response())
    erro.response.status_code = 500
    client = FakeClient({"v1...v2": [commit_api("2024-01-05T00:00:00Z")], "v2...v3": erro})
    repositorios = {
        "org/a": [
            release("v1", "2024-01-01T00:00:00Z"),
            release("v2", "2024-01-10T00:00:00Z"),
            release("v3", "2024-01-20T00:00:00Z"),
        ]
    }
    with pytest.raises(requests.HTTPError):
        coletar_commits_entre_releases(client, repositorios, tmp_path, janela=JANELA)

    salvo = CacheCompares(tmp_path / "compares" / "org__a.json")
    assert "v1...v2" in salvo.pares


def test_cache_de_pares_e_gravado_periodicamente(tmp_path, monkeypatch):
    import pipeline.commits as commits_mod

    monkeypatch.setattr(commits_mod, "SALVAR_COMPARES_A_CADA", 2)
    caminho = tmp_path / "org__a.json"
    compares = CacheCompares(caminho)
    client = FakeClient({"v1...v2": [], "v2...v3": []})
    compares.obter(client, "org/a", "v1", "v2")
    assert not caminho.exists()
    compares.obter(client, "org/a", "v2", "v3")
    assert caminho.exists()
