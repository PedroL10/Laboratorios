from lab04.config import ALFA, criar_rng
from lab04.testes import aplicar_mannwhitney, aplicar_welch, comparar_testes, interpretar


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
