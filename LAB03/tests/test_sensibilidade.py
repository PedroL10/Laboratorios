"""Testes da analise de sensibilidade (RQ 07)."""

from __future__ import annotations

import pytest
from sklearn.metrics import cohen_kappa_score

from metricas.sensibilidade import (
    classificar_combinacao,
    comparar_classificacoes,
    interpretar_kappa,
)


def test_cada_combinacao_usa_as_suas_colunas():
    linha = {
        "deployment_frequency": "8", "lead_time_release_dias": "40", "cfr_ci": "0.1",
        "deployment_frequency_pre": "0.5", "lead_time_commit_dias_pre": "3", "cfr_entrega_pre": "0.5",
        "deployment_frequency_tag": "2", "lead_time_commit_dias_tag": "0.5",
        "tempo_recuperacao_horas": "10",
    }
    c1 = classificar_combinacao(linha, "C1")
    assert (c1["categoria_frequencia"], c1["categoria_lead_time"], c1["categoria_cfr"]) == ("Elite", "Low", "Elite")
    c2 = classificar_combinacao(linha, "C2")
    assert (c2["categoria_frequencia"], c2["categoria_lead_time"], c2["categoria_cfr"]) == ("Medium", "High", "Low")
    c3 = classificar_combinacao(linha, "C3")
    # C3 usa a frequencia por tag, o lead time (b) por tag e o CFR (a).
    assert (c3["categoria_frequencia"], c3["categoria_lead_time"], c3["categoria_cfr"]) == ("High", "Elite", "Elite")
    assert c1["categoria_recuperacao"] == c2["categoria_recuperacao"] == c3["categoria_recuperacao"] == "High"


def test_classificacoes_iguais_tem_kappa_1_e_nenhuma_mudanca():
    categorias = ["Elite", "High", "Medium", "Low", "High"]
    resultado = comparar_classificacoes(categorias, categorias)
    assert resultado == {"n": 5, "mudaram": 0, "pct_mudaram": 0.0, "kappa": 1.0}


def test_kappa_ponderado_bate_com_o_sklearn_e_ignora_ausentes():
    x = ["Elite", "High", "Medium", "Low", None, "High"]
    y = ["High", "High", "Medium", "Elite", "Low", None]
    resultado = comparar_classificacoes(x, y)

    assert resultado["n"] == 4
    assert resultado["mudaram"] == 2
    assert resultado["pct_mudaram"] == 0.5
    esperado = cohen_kappa_score([4, 3, 2, 1], [3, 3, 2, 4], labels=[1, 2, 3, 4], weights="linear")
    assert resultado["kappa"] == pytest.approx(esperado)


def test_troca_para_categoria_vizinha_pesa_menos_que_para_a_oposta():
    base = ["Elite", "High", "Medium", "Low"] * 5
    vizinha = ["High", "High", "Medium", "Low"] * 5
    oposta = ["Low", "High", "Medium", "Low"] * 5
    assert comparar_classificacoes(base, vizinha)["kappa"] > comparar_classificacoes(base, oposta)["kappa"]


def test_casos_sem_kappa_definido():
    assert comparar_classificacoes([None], ["High"]) == {"n": 0, "mudaram": 0, "pct_mudaram": None, "kappa": None}
    assert comparar_classificacoes(["High"], ["High"])["kappa"] is None
    # Todos na mesma categoria nas duas: kappa indefinido (0/0).
    assert comparar_classificacoes(["High", "High"], ["High", "High"])["kappa"] is None


@pytest.mark.parametrize(
    ("kappa", "esperado"),
    [(None, None), (-0.1, "pobre"), (0.2, "leve"), (0.4, "razoavel"), (0.6, "moderada"),
     (0.8, "substancial"), (0.81, "quase perfeita")],
)
def test_interpretar_kappa_segue_landis_e_koch(kappa, esperado):
    assert interpretar_kappa(kappa) == esperado
