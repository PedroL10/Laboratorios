"""Deployment frequency (RQ 01), em releases por semana.

Para cada repositorio, divide o numero de releases publicadas na janela pelo
numero de semanas da janela. Com a janela de 12 meses (365 dias, inicio e fim
inclusivos), sao 365 / 7 = 52,14 semanas, o "~52,1" do enunciado.

O numero de semanas e calculado a partir das datas da janela, e nao fixado em
52,1, para que uma janela diferente no `config.yaml` continue dando o valor certo.
"""

from __future__ import annotations

from datetime import date

DIAS_POR_SEMANA = 7


def semanas_da_janela(inicio: str | date, fim: str | date) -> float:
    """Numero de semanas entre `inicio` e `fim` (AAAA-MM-DD), inclusive nas duas pontas."""
    dias = (date.fromisoformat(str(fim)) - date.fromisoformat(str(inicio))).days + 1
    if dias <= 0:
        raise ValueError("O inicio da janela deve ser anterior ao fim.")
    return dias / DIAS_POR_SEMANA


def deployment_frequency(n_releases: int, semanas: float) -> float:
    """Releases por semana: releases publicadas na janela / semanas da janela."""
    return n_releases / semanas
