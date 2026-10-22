"""Testes da comparacao de metricas DORA entre subgrupos (RQ 06)."""

from __future__ import annotations

from scipy.stats import mannwhitneyu

from metricas.subgrupos import (
    agrupar_por_grupo,
    cliff_delta,
    comparar_grupos,
    corrigir_holm,
    epsilon_quadrado,
    agrupar_raros,
    interpretar_cliff_delta,
    interpretar_epsilon_quadrado,
    quartis,
)


def test_quartis_divide_8_valores_em_4_grupos_de_2():
    valores = [10, 20, 30, 40, 50, 60, 70, 80]
    assert quartis(valores) == [1, 1, 2, 2, 3, 3, 4, 4]


def test_quartis_preserva_a_ordem_dos_valores_originais():
    valores = [80, 10, 70, 20]
    # ordenados: 10(0grp)->Q1, 20->Q1 ou Q2 dependendo do n, 70, 80 nos grupos altos
    grupos = quartis(valores)
    # o menor valor (indice 1, valor 10) fica no grupo mais baixo
    assert grupos[1] < grupos[0]


def test_agrupar_por_grupo_ignora_valores_ausentes():
    valores_metrica = [1.0, None, 3.0, 4.0]
    grupos = ["Q1", "Q1", "Q2", "Q2"]
    agrupados = agrupar_por_grupo(valores_metrica, grupos)
    assert agrupados == {"Q1": [1.0], "Q2": [3.0, 4.0]}


def test_interpretar_cliff_delta_segue_romano_et_al():
    assert interpretar_cliff_delta(0.1) == "desprezivel"
    assert interpretar_cliff_delta(0.2) == "pequeno"
    assert interpretar_cliff_delta(0.4) == "medio"
    assert interpretar_cliff_delta(-0.9) == "grande"


def test_cliff_delta_bate_com_mannwhitneyu():
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 8, 9, 10]
    u1 = mannwhitneyu(x, y).statistic
    # x todo menor que y: delta deve ser -1 (relacao inversa perfeita)
    assert cliff_delta(u1, len(x), len(y)) == -1.0


def test_epsilon_quadrado_varia_de_0_a_1():
    assert 0 <= epsilon_quadrado(h=5.0, n=10) <= 1


def test_comparar_grupos_com_2_grupos_usa_mann_whitney():
    grupos = {"Q1": [1, 2, 3], "Q2": [10, 11, 12]}
    resultado = comparar_grupos(grupos)
    assert resultado["teste"] == "mann-whitney"
    assert resultado["efeito"] == -1.0
    assert resultado["n"] == 6


def test_comparar_grupos_com_3_ou_mais_grupos_usa_kruskal_wallis():
    grupos = {"Q1": [1, 2, 3], "Q2": [10, 11, 12], "Q3": [20, 21, 22]}
    resultado = comparar_grupos(grupos)
    assert resultado["teste"] == "kruskal-wallis"
    assert resultado["p_valor"] is not None


def test_comparar_grupos_descarta_grupos_com_menos_de_2_valores():
    grupos = {"Q1": [1, 2, 3], "Q2": [10]}
    resultado = comparar_grupos(grupos)
    assert resultado == {"teste": None, "estatistica": None, "p_valor": None, "efeito": None, "n": 3}


def test_comparar_grupos_com_menos_de_2_grupos_validos_nao_testa():
    resultado = comparar_grupos({"Q1": [1, 2, 3]})
    assert resultado["teste"] is None


def test_corrigir_holm_ordena_e_ajusta_os_menores_p_valores():
    # 3 testes com p = 0.01, 0.02, 0.03: Holm multiplica o menor por 3, o do
    # meio por 2 e o maior por 1, mas a monotonicidade impede o 3o cair
    # abaixo do 2o corrigido (0.03 vira 0.04).
    resultados = [{"p_valor": 0.01}, {"p_valor": 0.02}, {"p_valor": 0.03}]
    corrigidos = corrigir_holm(resultados)
    assert corrigidos[0]["p_valor_corrigido"] == 0.03
    assert corrigidos[1]["p_valor_corrigido"] == 0.04
    assert corrigidos[2]["p_valor_corrigido"] == 0.04
    assert all(c["p_valor_corrigido"] >= c["p_valor"] for c in corrigidos)


def test_corrigir_holm_mantem_monotonicidade():
    resultados = [{"p_valor": 0.001}, {"p_valor": 0.49}, {"p_valor": 0.5}]
    corrigidos = corrigir_holm(resultados)
    valores = [c["p_valor_corrigido"] for c in corrigidos]
    assert valores == sorted(valores)


def test_corrigir_holm_ignora_itens_sem_p_valor():
    resultados = [{"p_valor": 0.01}, {"teste": None, "p_valor": None}]
    corrigidos = corrigir_holm(resultados)
    assert "p_valor_corrigido" not in corrigidos[1]
    assert corrigidos[0]["p_valor_corrigido"] == 0.01


def test_corrigir_holm_marca_significativo_abaixo_de_5_porcento():
    resultados = [{"p_valor": 0.001}, {"p_valor": 0.9}]
    corrigidos = corrigir_holm(resultados)
    assert corrigidos[0]["significativo"] is True
    assert corrigidos[1]["significativo"] is False


def test_interpretar_epsilon_quadrado():
    assert interpretar_epsilon_quadrado(0.005) == "desprezivel"
    assert interpretar_epsilon_quadrado(0.01) == "pequeno"
    assert interpretar_epsilon_quadrado(0.08) == "medio"
    assert interpretar_epsilon_quadrado(0.26) == "grande"


def test_kruskal_wallis_traz_a_interpretacao_do_efeito():
    grupos = {"a": [1, 2, 3], "b": [10, 11, 12], "c": [20, 21, 22]}
    assert comparar_grupos(grupos)["interpretacao_efeito"] == "grande"


def test_agrupar_raros_junta_grupos_pequenos_e_ausentes_em_outras():
    rotulos = ["Python", "Python", "Go", "Python", None, "", "Go", "Rust"]
    assert agrupar_raros(rotulos, minimo=2) == [
        "Python", "Python", "Go", "Python", "Outras", "Outras", "Go", "Outras",
    ]
