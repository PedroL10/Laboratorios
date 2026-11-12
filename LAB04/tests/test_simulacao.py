import numpy as np
import pytest
from scipy import stats

from lab04.config import criar_rng
from lab04.simulacao import (
    ajustar_melhor_distribuicao,
    gerar_pares,
    gerar_simulados,
    gerar_simulados_por_grupo,
)


def test_ajustar_melhor_distribuicao_acha_a_geradora():
    horas = stats.lognorm.rvs(1.5, scale=20, size=2000, random_state=criar_rng())
    nome, distribuicao, parametros = ajustar_melhor_distribuicao(horas)
    assert nome == "lognormal"
    assert distribuicao is stats.lognorm
    assert parametros[-1] == pytest.approx(20, rel=0.1)


def test_gerar_simulados_respeita_o_tamanho_pedido():
    horas = stats.lognorm.rvs(1.5, scale=20, size=200, random_state=criar_rng())
    simulados = gerar_simulados(horas, 50, criar_rng())
    assert len(simulados) == 50
    assert np.all(simulados >= 0)


def test_gerar_simulados_por_grupo_usa_os_dois_grupos_reais():
    simulados = gerar_simulados_por_grupo(criar_rng())
    assert set(simulados) == {"sem_bot", "com_bot"}
    assert len(simulados["sem_bot"]) == 30
    assert len(simulados["com_bot"]) == 30


def test_gerar_pares_tem_um_par_por_linha():
    grupo_a, grupo_b = gerar_pares(stats.gamma, (1.1, 0, 50), 30, 1.0, criar_rng(), n_simulacoes=100)
    assert grupo_a.shape == (100, 30)
    assert grupo_b.shape == (100, 30)


def test_gerar_pares_sem_efeito_mantem_a_mesma_distribuicao():
    grupo_a, grupo_b = gerar_pares(stats.gamma, (1.1, 0, 50), 30, 1.0, criar_rng(), n_simulacoes=2000)
    assert np.median(grupo_b) / np.median(grupo_a) == pytest.approx(1, abs=0.05)


def test_gerar_pares_multiplica_o_segundo_grupo_pelo_fator():
    grupo_a, grupo_b = gerar_pares(stats.gamma, (1.1, 0, 50), 30, 2.0, criar_rng(), n_simulacoes=2000)
    assert np.median(grupo_b) / np.median(grupo_a) == pytest.approx(2, rel=0.05)
