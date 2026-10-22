"""Testes do processamento em paralelo e da gravacao atomica dos caches."""

from __future__ import annotations

import json
import threading
import time

import pytest

from pipeline.github_client import GitHubClient
from pipeline.retomada import gravar_json, processar_em_paralelo


class ClienteComCopia:
    def __init__(self):
        self.copias = []

    def copia(self):
        nova = object()
        self.copias.append(nova)
        return nova


def test_processa_todos_os_itens_com_um_cliente_por_thread():
    client = ClienteComCopia()
    vistos = {}
    trava = threading.Lock()

    def processar(client_thread, item):
        time.sleep(0.01)
        with trava:
            vistos[item] = (threading.get_ident(), client_thread)

    processar_em_paralelo(list(range(20)), processar, client, trabalhadores=4)

    assert sorted(vistos) == list(range(20))
    # Cada thread usa sempre a mesma copia, e nenhuma usa o cliente original.
    por_thread = {}
    for thread, cliente in vistos.values():
        por_thread.setdefault(thread, set()).add(id(cliente))
    assert all(len(clientes) == 1 for clientes in por_thread.values())
    assert 1 < len(client.copias) <= 4


def test_progresso_conta_os_itens_concluidos():
    chamadas = []
    processar_em_paralelo([1, 2, 3], lambda c, i: None, object(), 2, lambda f, t: chamadas.append((f, t)))
    assert sorted(chamadas) == [(1, 3), (2, 3), (3, 3)]


def test_erro_em_um_item_e_propagado_e_cancela_os_que_nao_comecaram():
    processados = []

    def processar(client, item):
        if item == 0:
            raise RuntimeError("falhou")
        time.sleep(0.05)
        processados.append(item)

    with pytest.raises(RuntimeError, match="falhou"):
        processar_em_paralelo(list(range(50)), processar, object(), trabalhadores=2)
    assert len(processados) < 49


def test_sem_itens_nao_faz_nada():
    processar_em_paralelo([], lambda c, i: pytest.fail("nao devia chamar"), object())


def test_gravar_json_substitui_o_arquivo_sem_deixar_temporarios(tmp_path):
    caminho = tmp_path / "sub" / "dados.json"
    gravar_json(caminho, {"a": 1})
    gravar_json(caminho, {"a": 2})
    assert json.loads(caminho.read_text(encoding="utf-8")) == {"a": 2}
    assert [p.name for p in caminho.parent.iterdir()] == ["dados.json"]


def test_copia_do_cliente_tem_sessao_propria_e_mesmo_token():
    original = GitHubClient(token="t", timeout=5)
    copia = original.copia()
    assert copia.session is not original.session
    assert copia.session.headers["Authorization"] == "Bearer t"
    assert copia.timeout == 5
