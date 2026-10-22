"""Testes da classificacao DORA, com os valores exatamente nos cortes."""

from __future__ import annotations

import pytest

from metricas.classificacao import (
    ELITE,
    HIGH,
    LOW,
    MEDIUM,
    UMA_POR_MES_EM_SEMANAS,
    categoria_geral,
    classificar_cfr,
    classificar_frequencia,
    classificar_lead_time,
    classificar_recuperacao,
    classificar_repositorio,
)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (10, ELITE),
        (7, ELITE),
        (6.99, HIGH),
        (1, HIGH),
        (0.99, MEDIUM),
        (UMA_POR_MES_EM_SEMANAS, MEDIUM),
        (UMA_POR_MES_EM_SEMANAS - 0.001, LOW),
        (0, LOW),
        (None, None),
    ],
)
def test_classificar_frequencia(valor, esperado):
    assert classificar_frequencia(valor) == esperado


def test_uma_release_por_mes_em_semanas():
    # 12 releases num ano de 52,18 semanas.
    assert UMA_POR_MES_EM_SEMANAS == pytest.approx(12 / (365.25 / 7))


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (0.5, ELITE),
        (1, HIGH),
        (6.99, HIGH),
        (7, MEDIUM),
        (29.99, MEDIUM),
        (30, LOW),
        (None, None),
    ],
)
def test_classificar_lead_time(dias, esperado):
    assert classificar_lead_time(dias) == esperado


@pytest.mark.parametrize(
    ("cfr", "esperado"),
    [
        (0, ELITE),
        (0.15, ELITE),
        (0.1501, HIGH),
        (0.30, HIGH),
        (0.3001, MEDIUM),
        (0.45, MEDIUM),
        (0.4501, LOW),
        (1, LOW),
        (None, None),
    ],
)
def test_classificar_cfr(cfr, esperado):
    assert classificar_cfr(cfr) == esperado


@pytest.mark.parametrize(
    ("horas", "esperado"),
    [
        (0.5, ELITE),
        (1, HIGH),
        (23.99, HIGH),
        (24, MEDIUM),
        (167.99, MEDIUM),
        (168, LOW),
        (None, None),
    ],
)
def test_classificar_recuperacao(horas, esperado):
    assert classificar_recuperacao(horas) == esperado


def test_categoria_geral_exemplo_do_enunciado():
    # (4, 3, 3, 1) -> mediana 3 -> High
    assert categoria_geral([ELITE, HIGH, HIGH, LOW]) == HIGH


def test_categoria_geral_arredonda_a_mediana_para_baixo():
    # (4, 4, 2, 1) -> mediana 3 -> High; (4, 3) -> 3,5 -> High; (2, 1) -> 1,5 -> Low
    assert categoria_geral([ELITE, ELITE, MEDIUM, LOW]) == HIGH
    assert categoria_geral([ELITE, HIGH]) == HIGH
    assert categoria_geral([MEDIUM, LOW]) == LOW


def test_categoria_geral_ignora_metricas_sem_valor():
    assert categoria_geral([ELITE, None, ELITE, None]) == ELITE
    assert categoria_geral([None, None]) is None


def test_classificar_repositorio():
    resultado = classificar_repositorio(
        deployment_frequency=8, lead_time_dias=3, cfr=0.2, tempo_recuperacao_horas=200
    )
    assert resultado == {
        "categoria_frequencia": ELITE,
        "categoria_lead_time": HIGH,
        "categoria_cfr": HIGH,
        "categoria_recuperacao": LOW,
        "categoria_geral": HIGH,
        "n_metricas": 4,
    }


def test_classificar_repositorio_sem_tempo_de_recuperacao():
    resultado = classificar_repositorio(0.5, 10, 0.5, None)
    assert resultado["categoria_recuperacao"] is None
    assert resultado["n_metricas"] == 3
    # (2, 2, 1) -> mediana 2 -> Medium
    assert resultado["categoria_geral"] == MEDIUM
