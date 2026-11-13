import numpy as np
import pytest

from lab04.config import ALFA, criar_rng
from lab04.graficos import CORES, grafico_dados, grafico_estatistica_h0
from lab04.testes import aplicar_mannwhitney, aplicar_welch


def grupos(rng):
    return {"sem_bot": rng.gamma(1.1, 40, 30), "com_bot": rng.gamma(1.1, 60, 30)}


def test_grafico_dados_tem_real_e_simulado_em_cada_grupo():
    rng = criar_rng()
    figura = grafico_dados(grupos(rng), grupos(rng))
    assert len(figura.data) == 4
    assert {t.name for t in figura.data} == {"Dados reais", "Dados simulados"}
    assert figura.layout.title.text.startswith("G1")


def test_grafico_estatistica_h0_usa_a_cor_de_cada_teste():
    dados = grupos(criar_rng())
    resultados = {
        "welch": aplicar_welch(dados["sem_bot"], dados["com_bot"]),
        "mann_whitney": aplicar_mannwhitney(dados["sem_bot"], dados["com_bot"]),
    }
    figura = grafico_estatistica_h0(resultados)
    curvas = [t for t in figura.data if t.mode == "lines"]
    assert [c.line.color for c in curvas] == [CORES["welch"], CORES["mann_whitney"]]
    assert figura.layout.title.text.startswith("G2")


def test_area_do_p_valor_no_g2_soma_o_p_valor():
    dados = grupos(criar_rng())
    resultados = {
        "welch": aplicar_welch(dados["sem_bot"], dados["com_bot"]),
        "mann_whitney": aplicar_mannwhitney(dados["sem_bot"], dados["com_bot"]),
    }
    figura = grafico_estatistica_h0(resultados)
    for teste, eixo in (("welch", "x"), ("mann_whitney", "x2")):
        areas = [t for t in figura.data if t.legendgroup == f"p-{teste}"]
        assert len(areas) == 2
        total = 0.0
        for area in areas:
            x, y = np.array(area.x[1:-1]), np.array(area.y[1:-1])
            total += np.trapezoid(y, x)
        # A curva vai só até um limite finito, então a área calculada fica um pouco abaixo.
        assert total == pytest.approx(resultados[teste]["p_valor"], abs=0.01)


def test_regiao_de_rejeicao_tem_alfa_de_area():
    dados = grupos(criar_rng())
    resultados = {
        "welch": aplicar_welch(dados["sem_bot"], dados["com_bot"]),
        "mann_whitney": aplicar_mannwhitney(dados["sem_bot"], dados["com_bot"]),
    }
    figura = grafico_estatistica_h0(resultados)
    areas = [t for t in figura.data if t.legendgroup == "rejeicao"][:2]
    total = sum(np.trapezoid(np.array(a.y[1:-1]), np.array(a.x[1:-1])) for a in areas)
    assert total == pytest.approx(ALFA, abs=0.01)


def test_grafico_dados_usa_a_mesma_escala_de_horas_nos_dois_paineis():
    rng = criar_rng()
    figura = grafico_dados(grupos(rng), grupos(rng))
    assert figura.layout.xaxis2.matches == "x"
