"""Testes do CFR variante (a), proxy de CI."""

from __future__ import annotations

import pytest

from metricas.cfr_ci import FALHA, IGNORADO, SUCESSO, cfr_ci_repositorio, classificar_conclusao


def runs(**por_conclusao: int) -> list[dict]:
    """runs(success=3, failure=1) -> lista de runs com essas conclusoes."""
    return [{"conclusion": c} for c, n in por_conclusao.items() for _ in range(n)]


@pytest.mark.parametrize(
    ("conclusion", "esperado"),
    [
        ("success", SUCESSO),
        ("failure", FALHA),
        ("timed_out", FALHA),
        ("startup_failure", FALHA),
        ("cancelled", IGNORADO),
        ("skipped", IGNORADO),
        ("neutral", IGNORADO),
        ("action_required", IGNORADO),
        ("stale", IGNORADO),
        (None, IGNORADO),  # execucao em andamento
    ],
)
def test_classificar_conclusao_segue_a_tabela_da_secao_3(conclusion, esperado):
    assert classificar_conclusao(conclusion) == esperado


def test_cfr_ci_e_falhas_sobre_falhas_mais_sucessos():
    resultado = cfr_ci_repositorio(runs(success=6, failure=1, timed_out=1))
    assert resultado == {
        "cfr_ci": 0.25,
        "n_runs_falha": 2,
        "n_runs_sucesso": 6,
        "n_runs_ignorados": 0,
    }


def test_cancelled_e_demais_ignorados_nao_entram_no_calculo():
    resultado = cfr_ci_repositorio(
        runs(success=3, failure=1, cancelled=10, skipped=2, neutral=1) + [{"conclusion": None}]
    )
    assert resultado["cfr_ci"] == 0.25
    assert resultado["n_runs_ignorados"] == 14


def test_sem_runs_validos_nao_tem_cfr():
    assert cfr_ci_repositorio(runs(cancelled=3))["cfr_ci"] is None
    assert cfr_ci_repositorio([])["cfr_ci"] is None
