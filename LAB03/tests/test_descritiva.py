"""Testes da estatistica descritiva (mediana e IQR)."""

from __future__ import annotations

import pytest

from metricas.descritiva import distribuicao_categorias, resumo


def test_resumo_com_quartis_por_interpolacao_linear():
    # Mesmo resultado de numpy.percentile([1, 2, 3, 4, 100], [25, 50, 75]).
    r = resumo([4, 1, 100, 3, 2])
    assert r == {"n": 5, "mediana": 3, "q1": 2.0, "q3": 4.0, "iqr": 2.0, "minimo": 1, "maximo": 100}


def test_resumo_ignora_none():
    assert resumo([None, 1, None, 3])["n"] == 2
    assert resumo([None, 1, None, 3])["mediana"] == 2


def test_resumo_com_um_valor_e_sem_valores():
    assert resumo([5.0]) == {"n": 1, "mediana": 5.0, "q1": 5.0, "q3": 5.0, "iqr": 0.0, "minimo": 5.0, "maximo": 5.0}
    assert resumo([None])["mediana"] is None
    assert resumo([])["n"] == 0


def test_distribuicao_categorias_proporcao_sobre_os_classificados():
    dist = distribuicao_categorias(["Elite", "High", "High", "Low", None, ""])
    assert dist["contagem"] == {"Elite": 1, "High": 2, "Medium": 0, "Low": 1}
    assert dist["proporcao"]["High"] == pytest.approx(0.5)
    assert dist["classificados"] == 4
    assert dist["sem_categoria"] == 2


def test_distribuicao_sem_nenhum_classificado():
    dist = distribuicao_categorias([None, None])
    assert dist["proporcao"]["Elite"] is None
    assert dist["sem_categoria"] == 2
