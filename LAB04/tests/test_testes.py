import pytest
from scipy import stats

from lab04.config import ALFA, criar_rng
from lab04.testes import (
    aplicar_mannwhitney,
    aplicar_welch,
    comparar_testes,
    explicar,
    interpretar,
    taxas_rejeicao,
)


def test_aplicar_welch_detecta_diferenca_clara():
    rng = criar_rng()
    grupo_a = rng.normal(0, 1, 200)
    grupo_b = rng.normal(5, 1, 200)
    resultado = aplicar_welch(grupo_a, grupo_b)
    assert resultado["p_valor"] < ALFA


def test_aplicar_mannwhitney_nao_rejeita_quando_nao_ha_diferenca():
    rng = criar_rng()
    grupo_a = rng.normal(0, 1, 200)
    grupo_b = rng.normal(0, 1, 200)
    resultado = aplicar_mannwhitney(grupo_a, grupo_b)
    assert resultado["p_valor"] >= ALFA


def test_interpretar_sinaliza_rejeicao():
    texto = interpretar({"teste": "welch", "p_valor": 0.001})
    assert "rejeita H0 (há diferença" in texto


def test_interpretar_sinaliza_nao_rejeicao():
    texto = interpretar({"teste": "welch", "p_valor": 0.9})
    assert "não rejeita H0" in texto


def test_comparar_testes_salva_e_retorna_as_duas_interpretacoes():
    tabela, interpretacoes = comparar_testes(criar_rng())
    assert set(tabela["teste"]) == {"welch", "mann_whitney"}
    assert len(interpretacoes) == 2


def test_aplicar_mannwhitney_padroniza_u_em_torno_de_zero_sem_diferenca():
    rng = criar_rng()
    resultado = aplicar_mannwhitney(rng.normal(0, 1, 200), rng.normal(0, 1, 200))
    assert abs(resultado["estatistica_padronizada"]) < 2


def test_aplicar_welch_informa_graus_de_liberdade():
    rng = criar_rng()
    resultado = aplicar_welch(rng.normal(0, 1, 30), rng.normal(0, 5, 30))
    assert 29 <= resultado["graus_liberdade"] < 58


def test_explicar_diz_o_que_cada_teste_comparou_e_a_decisao():
    sem_bot, com_bot = [1.0, 2, 3, 4], [10.0, 20, 30, 40]
    welch = explicar(aplicar_welch(sem_bot, com_bot), sem_bot, com_bot)
    mann_whitney = explicar(aplicar_mannwhitney(sem_bot, com_bot), sem_bot, com_bot)
    assert "médias" in welch and "2,5 h sem bot" in welch
    assert "0% dos pares" in mann_whitney
    assert "rejeita H₀" in welch


def test_taxas_rejeicao_vetorizada_bate_com_os_testes_um_a_um():
    rng = criar_rng()
    grupo_a = stats.gamma.rvs(1.1, 0, 50, size=(1, 30), random_state=rng)
    grupo_b = stats.gamma.rvs(1.1, 0, 50, size=(1, 30), random_state=rng) * 2
    welch = stats.ttest_ind(grupo_a, grupo_b, axis=1, equal_var=False).pvalue[0]
    mann_whitney = stats.mannwhitneyu(grupo_a, grupo_b, axis=1, alternative="two-sided").pvalue[0]
    assert welch == pytest.approx(aplicar_welch(grupo_a[0], grupo_b[0])["p_valor"])
    assert mann_whitney == pytest.approx(aplicar_mannwhitney(grupo_a[0], grupo_b[0])["p_valor"])


def test_taxas_rejeicao_sem_efeito_fica_perto_de_5_por_cento():
    taxas = taxas_rejeicao(stats.norm, (10, 1), 30, 1.0, criar_rng(), n_simulacoes=4000)
    assert taxas["welch"] == pytest.approx(0.05, abs=0.015)
    assert taxas["mann_whitney"] == pytest.approx(0.05, abs=0.015)


def test_taxas_rejeicao_com_efeito_grande_detecta_quase_sempre():
    taxas = taxas_rejeicao(stats.gamma, (1.1, 0, 50), 30, 4.0, criar_rng(), n_simulacoes=2000)
    assert taxas["welch"] > 0.9
    assert taxas["mann_whitney"] > 0.9


def test_estatisticas_padronizadas_reproduzem_o_p_valor():
    rng = criar_rng()
    sem_bot, com_bot = rng.gamma(1.1, 40, 30), rng.gamma(1.1, 60, 30)
    welch = aplicar_welch(sem_bot, com_bot)
    mann_whitney = aplicar_mannwhitney(sem_bot, com_bot)
    p_welch = 2 * stats.t.sf(abs(welch["estatistica_padronizada"]), welch["graus_liberdade"])
    p_mann_whitney = 2 * stats.norm.sf(abs(mann_whitney["estatistica_padronizada"]))
    assert p_welch == pytest.approx(welch["p_valor"])
    assert p_mann_whitney == pytest.approx(mann_whitney["p_valor"])
