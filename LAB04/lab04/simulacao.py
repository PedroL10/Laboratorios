"""Gera dados simulados a partir da distribuição real que melhor se ajusta a cada grupo."""

import numpy as np

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
