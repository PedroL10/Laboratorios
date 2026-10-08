"""Testes do filtro de GitHub Actions. As respostas da API sao simuladas."""

from __future__ import annotations

import pytest
import requests

from pipeline.filtro_actions import (
    MOTIVO_SEM_WORKFLOWS,
    carregar_verificados,
    filtrar_actions,
    usa_actions,
    verificar_actions,
)


def http_error(status: int, headers: dict | None = None) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    return requests.HTTPError(f"HTTP {status}", response=response)


class FakeClient:
    """`respostas` mapeia full_name -> total_count de workflows ou uma excecao."""

    def __init__(self, respostas: dict):
        self.respostas = respostas
        self.consultados: list[str] = []

    def get(self, path, params=None):
        full_name = path.removeprefix("/repos/").removesuffix("/actions/workflows")
        self.consultados.append(full_name)
        assert params == {"per_page": 1}
        resposta = self.respostas[full_name]
        if isinstance(resposta, Exception):
            raise resposta
        return {"total_count": resposta, "workflows": []}


def candidatos(*nomes: str) -> list[dict]:
    return [{"full_name": n} for n in nomes]


def test_repositorio_com_workflows_usa_actions():
    linha = verificar_actions(FakeClient({"org/a": 3}), "org/a")
    assert linha == {
        "full_name": "org/a",
        "usa_actions": True,
        "n_workflows": 3,
        "motivo_descarte": "",
    }


def test_repositorio_sem_workflows_e_descartado():
    linha = verificar_actions(FakeClient({"org/a": 0}), "org/a")
    assert linha["usa_actions"] is False
    assert linha["motivo_descarte"] == MOTIVO_SEM_WORKFLOWS


def test_erro_http_vira_motivo_de_descarte():
    linha = verificar_actions(FakeClient({"org/a": http_error(404)}), "org/a")
    assert linha["usa_actions"] is False
    assert linha["n_workflows"] is None
    assert linha["motivo_descarte"] == "erro_http_404"


def test_403_sem_cota_esgotada_e_descarte():
    linha = verificar_actions(
        FakeClient({"org/a": http_error(403, {"X-RateLimit-Remaining": "4000"})}), "org/a"
    )
    assert linha["motivo_descarte"] == "erro_http_403"


def test_cota_esgotada_interrompe_em_vez_de_descartar():
    client = FakeClient({"org/a": http_error(403, {"X-RateLimit-Remaining": "0"})})
    with pytest.raises(requests.HTTPError):
        verificar_actions(client, "org/a")


def test_filtrar_actions_mantem_ordem_e_grava_csv(tmp_path):
    saida = tmp_path / "filtro_actions.csv"
    client = FakeClient({"org/a": 2, "org/b": 0, "org/c": 5})

    resultado = filtrar_actions(client, candidatos("org/a", "org/b", "org/c"), saida)

    assert [r["full_name"] for r in resultado] == ["org/a", "org/b", "org/c"]
    assert [usa_actions(r) for r in resultado] == [True, False, True]
    gravado = carregar_verificados(saida)
    assert set(gravado) == {"org/a", "org/b", "org/c"}
    assert gravado["org/b"]["motivo_descarte"] == MOTIVO_SEM_WORKFLOWS


def test_retomada_nao_consulta_repositorios_ja_verificados(tmp_path):
    saida = tmp_path / "filtro_actions.csv"
    filtrar_actions(FakeClient({"org/a": 2, "org/b": 0}), candidatos("org/a", "org/b"), saida)

    client = FakeClient({"org/a": 2, "org/b": 0, "org/c": 1})
    resultado = filtrar_actions(client, candidatos("org/a", "org/b", "org/c"), saida)

    assert client.consultados == ["org/c"]
    assert [usa_actions(r) for r in resultado] == [True, False, True]
    # O cabecalho nao e repetido ao continuar o arquivo.
    assert saida.read_text(encoding="utf-8").count("full_name") == 1


def test_interrupcao_preserva_o_que_ja_foi_verificado(tmp_path):
    saida = tmp_path / "filtro_actions.csv"
    cota_esgotada = http_error(403, {"X-RateLimit-Remaining": "0"})
    client = FakeClient({"org/a": 2, "org/b": cota_esgotada})

    with pytest.raises(requests.HTTPError):
        filtrar_actions(client, candidatos("org/a", "org/b"), saida)

    assert set(carregar_verificados(saida)) == {"org/a"}


def test_progresso_e_informado(tmp_path):
    chamadas = []
    filtrar_actions(
        FakeClient({"org/a": 1, "org/b": 1}),
        candidatos("org/a", "org/b"),
        tmp_path / "f.csv",
        progresso=lambda feitos, total: chamadas.append((feitos, total)),
    )
    assert chamadas == [(1, 2), (2, 2)]


def test_usa_actions_le_texto_do_csv():
    assert usa_actions({"usa_actions": "True"}) is True
    assert usa_actions({"usa_actions": "False"}) is False
