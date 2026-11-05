"""Parâmetros globais do estudo.

Todo número aleatório do projeto deve vir de `criar_rng`, para que os resultados
possam ser reproduzidos.
"""

import numpy as np

SEMENTE = 42
ALFA = 0.05
N_SIMULACOES = 10_000


def criar_rng() -> np.random.Generator:
    """Retorna um gerador novo, sempre iniciado com a semente fixa do projeto."""
    return np.random.default_rng(SEMENTE)
