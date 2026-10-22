"""Testes da correlacao de Spearman entre deployment frequency e CFR (RQ 05)."""

from __future__ import annotations

import pytest

from metricas.correlacao import spearman_frequencia_cfr


def repo(deployment_frequency, cfr) -> dict:
    return {"deployment_frequency": deployment_frequency, "cfr": cfr}


def test_correlacao_perfeita_positiva_da_rho_1():
    repositorios = [repo(f, f) for f in [1, 2, 3, 4, 5]]
    resultado = spearman_frequencia_cfr(repositorios)
    assert resultado["rho"] == pytest.approx(1.0)
    assert resultado["n"] == 5


def test_correlacao_perfeita_negativa_da_rho_menos_1():
    repositorios = [repo(f, -f) for f in [1, 2, 3, 4, 5]]
    resultado = spearman_frequencia_cfr(repositorios)
    assert resultado["rho"] == pytest.approx(-1.0)


def test_repositorios_sem_frequencia_ou_cfr_sao_ignorados():
    repositorios = [
        repo(1, 0.1),
        {"deployment_frequency": None, "cfr": 0.2},
        {"deployment_frequency": 2, "cfr": None},
        repo(3, 0.3),
    ]
    resultado = spearman_frequencia_cfr(repositorios)
    assert resultado["n"] == 2


def test_menos_de_2_pares_validos_nao_calcula_correlacao():
    resultado = spearman_frequencia_cfr([repo(1, 0.1)])
    assert resultado == {"rho": None, "p_valor": None, "n": 1}


def test_sem_repositorios_nao_calcula_correlacao():
    resultado = spearman_frequencia_cfr([])
    assert resultado == {"rho": None, "p_valor": None, "n": 0}


def test_usa_a_variante_de_cfr_pedida_em_chave_cfr():
    repositorios = [
        {"deployment_frequency": 1, "cfr_ci": 0.1, "cfr_entrega": 0.9},
        {"deployment_frequency": 2, "cfr_ci": 0.2, "cfr_entrega": 0.1},
        {"deployment_frequency": 3, "cfr_ci": 0.3, "cfr_entrega": 0.5},
    ]
    resultado_a = spearman_frequencia_cfr(repositorios, chave_cfr="cfr_ci")
    resultado_b = spearman_frequencia_cfr(repositorios, chave_cfr="cfr_entrega")
    assert resultado_a["rho"] == 1.0
    assert resultado_b["rho"] != resultado_a["rho"]
