"""Gera dados simulados calibrados pelos dados reais.

- `gerar_simulados_por_grupo`: um conjunto que imita cada grupo real (G1 e teste de exemplo).
- `gerar_pares`: muitos pares de grupos da mesma distribuição, com um efeito controlado
  (erro tipo I e poder).
"""

import numpy as np

from lab04.config import N_SIMULACOES
from lab04.distribuicao import CANDIDATAS, carregar_grupos, comparar_ajustes


def ajustar_melhor_distribuicao(horas: np.ndarray) -> tuple[str, object, tuple]:
    """Reajusta a distribuição com menor AIC para a amostra e devolve seus parâmetros completos."""
    melhor_nome = comparar_ajustes(horas).loc[0, "distribuicao"]
    distribuicao, fixos = CANDIDATAS[melhor_nome]
    parametros = distribuicao.fit(horas, **fixos)
    return melhor_nome, distribuicao, parametros


def gerar_simulados(horas: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Simula n valores a partir da distribuição que melhor se ajusta à amostra real."""
    _, distribuicao, parametros = ajustar_melhor_distribuicao(horas)
    return distribuicao.rvs(*parametros, size=n, random_state=rng)


def gerar_simulados_por_grupo(rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Simula um conjunto de dados por grupo real (sem_bot/com_bot), do mesmo tamanho da amostra."""
    grupos = carregar_grupos()
    return {
        nome: gerar_simulados(horas, len(horas), rng)
        for nome, horas in grupos.items()
        if nome != "todos"
    }


def gerar_pares(
    distribuicao,
    parametros: tuple,
    n: int,
    fator_efeito: float,
    rng: np.random.Generator,
    n_simulacoes: int = N_SIMULACOES,
) -> tuple[np.ndarray, np.ndarray]:
    """Gera n_simulacoes pares de grupos com n valores cada, um par por linha.

    Os dois grupos vêm da mesma distribuição, e os tempos do segundo grupo são multiplicados
    por fator_efeito. Com fator 1, H0 é verdadeira; com fator 2, o segundo grupo demora o
    dobro. Multiplicar os valores equivale a multiplicar a escala da distribuição.
    """
    grupo_a = distribuicao.rvs(*parametros, size=(n_simulacoes, n), random_state=rng)
    grupo_b = distribuicao.rvs(*parametros, size=(n_simulacoes, n), random_state=rng)
    return grupo_a, grupo_b * fator_efeito
