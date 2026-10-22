"""Classificacao DORA (Elite / High / Medium / Low), usada nas RQ 01 a 04 e na RQ 07.

Cortes fixos da tabela de referencia da disciplina (RQ 07 do enunciado):

| Metrica                       | Elite        | High            | Medium                   | Low         |
| ----------------------------- | ------------ | --------------- | ------------------------ | ----------- |
| Deployment frequency          | >= 7/semana  | >= 1 e < 7/sem. | >= 1/mes e < 1/semana    | < 1/mes     |
| Lead time (mediana)           | < 1 dia      | 1 a < 7 dias    | 7 a < 30 dias            | >= 30 dias  |
| Change failure rate           | <= 15%       | > 15% e <= 30%  | > 30% e <= 45%           | > 45%       |
| Tempo de recuperacao (mediana)| < 1 hora     | 1 h a < 1 dia   | 1 dia a < 1 semana       | >= 1 semana |

"1 por mes" e convertido para releases por semana com o mes medio do ano
(365,25 / 12 = 30,44 dias): 7 / 30,44 = 0,23 release por semana.

**Classificacao geral:** cada metrica vale 4 (Elite), 3 (High), 2 (Medium) ou
1 (Low); a categoria geral e a mediana desses valores, arredondada para baixo.
Ex.: (4, 3, 3, 1) -> mediana 3 -> High.

Uma metrica sem valor (None) fica sem categoria. Na classificacao geral, a
mediana e tirada so das metricas disponiveis, e `n_metricas` informa quantas
foram: um repositorio sem nenhum episodio de falha, por exemplo, nao tem tempo
de recuperacao. Quem analisa decide se exige as quatro.
"""

from __future__ import annotations

import math
import statistics

ELITE = "Elite"
HIGH = "High"
MEDIUM = "Medium"
LOW = "Low"

PONTOS = {ELITE: 4, HIGH: 3, MEDIUM: 2, LOW: 1}
CATEGORIA_POR_PONTOS = {pontos: categoria for categoria, pontos in PONTOS.items()}

DIAS_POR_MES = 365.25 / 12
UMA_POR_MES_EM_SEMANAS = 7 / DIAS_POR_MES


def classificar_frequencia(releases_por_semana: float | None) -> str | None:
    if releases_por_semana is None:
        return None
    if releases_por_semana >= 7:
        return ELITE
    if releases_por_semana >= 1:
        return HIGH
    if releases_por_semana >= UMA_POR_MES_EM_SEMANAS:
        return MEDIUM
    return LOW


def classificar_lead_time(dias: float | None) -> str | None:
    if dias is None:
        return None
    if dias < 1:
        return ELITE
    if dias < 7:
        return HIGH
    if dias < 30:
        return MEDIUM
    return LOW


def classificar_cfr(cfr: float | None) -> str | None:
    """`cfr` e uma proporcao entre 0 e 1 (0,15 = 15%)."""
    if cfr is None:
        return None
    if cfr <= 0.15:
        return ELITE
    if cfr <= 0.30:
        return HIGH
    if cfr <= 0.45:
        return MEDIUM
    return LOW


def classificar_recuperacao(horas: float | None) -> str | None:
    if horas is None:
        return None
    if horas < 1:
        return ELITE
    if horas < 24:
        return HIGH
    if horas < 24 * 7:
        return MEDIUM
    return LOW


def categoria_geral(categorias: list[str | None]) -> str | None:
    """Mediana dos pontos das categorias disponiveis, arredondada para baixo."""
    pontos = [PONTOS[c] for c in categorias if c is not None]
    if not pontos:
        return None
    return CATEGORIA_POR_PONTOS[math.floor(statistics.median(pontos))]


def classificar_repositorio(
    deployment_frequency: float | None,
    lead_time_dias: float | None,
    cfr: float | None,
    tempo_recuperacao_horas: float | None,
) -> dict:
    """Categoria de cada metrica e a categoria geral de um repositorio.

    As variantes de lead time e CFR usadas dependem da combinacao de definicoes
    (C1, C2, C3 da RQ 07): quem chama escolhe quais valores passar.
    """
    categorias = {
        "categoria_frequencia": classificar_frequencia(deployment_frequency),
        "categoria_lead_time": classificar_lead_time(lead_time_dias),
        "categoria_cfr": classificar_cfr(cfr),
        "categoria_recuperacao": classificar_recuperacao(tempo_recuperacao_horas),
    }
    disponiveis = [c for c in categorias.values() if c is not None]
    return {
        **categorias,
        "categoria_geral": categoria_geral(disponiveis),
        "n_metricas": len(disponiveis),
    }
