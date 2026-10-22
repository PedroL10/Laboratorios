"""Testes da deployment frequency (RQ 01)."""

from __future__ import annotations

import pytest

from metricas.frequencia import deployment_frequency, semanas_da_janela


def test_janela_de_12_meses_tem_cerca_de_52_1_semanas():
    assert semanas_da_janela("2025-10-01", "2026-09-30") == pytest.approx(365 / 7)
    assert round(semanas_da_janela("2025-10-01", "2026-09-30"), 1) == 52.1


def test_janela_inclui_o_primeiro_e_o_ultimo_dia():
    assert semanas_da_janela("2024-01-01", "2024-01-07") == 1.0


def test_janela_invertida_e_erro():
    with pytest.raises(ValueError):
        semanas_da_janela("2024-01-08", "2024-01-01")


def test_releases_por_semana():
    semanas = semanas_da_janela("2025-10-01", "2026-09-30")
    assert deployment_frequency(365, semanas) == pytest.approx(7.0)
    assert deployment_frequency(0, semanas) == 0.0
    assert deployment_frequency(12, semanas) == pytest.approx(12 / (365 / 7))
