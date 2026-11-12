"""Q1 e Q3 (parte do erro tipo I): com H0 verdadeira, com que frequência cada teste
'encontra' um efeito que não existe?

Gera N_SIMULACOES pares de amostras a partir da MESMA distribuição (H0 verdadeira),
aplica os dois testes em cada par e conta a proporção de p-valores abaixo de alfa.
Repete em situações que violam os pressupostos do teste paramétrico (Q3).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from lab04.config import ALFA, N_SIMULACOES, criar_rng
from lab04.distribuicao import carregar_grupos
from lab04.graficos import CORES, NOMES_TESTES
from lab04.simulacao import ajustar_melhor_distribuicao
from lab04.testes import aplicar_mannwhitney, aplicar_welch

RAIZ = Path(__file__).parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"


def construir_situacoes() -> dict[str, dict]:
    """Define as situações simuladas sob H0: o ajuste real e duas violações de pressuposto (Q3).

    'Amostra pequena' viola o pressuposto de amostra grande do t de Welch (aproximação
    assintótica da distribuição da estatística). 'Cauda pesada' exagera a assimetria e os
    outliers já observados nos dados reais (ver resultados/forma_distribuicao.csv).
    """
    grupos = carregar_grupos()
    n_real = len(grupos["sem_bot"])
    mediana_real = float(np.median(grupos["todos"]))
    _, distribuicao, parametros = ajustar_melhor_distribuicao(grupos["todos"])

    return {
        "ajuste real (n=30)": {
            "distribuicao": distribuicao,
            "parametros": parametros,
            "n": n_real,
        },
        "amostra pequena (n=10)": {
            "distribuicao": distribuicao,
            "parametros": parametros,
            "n": 10,
        },
        "cauda pesada (lognormal, forma=2.5)": {
            "distribuicao": stats.lognorm,
            "parametros": (2.5, 0, mediana_real),
            "n": n_real,
        },
    }


def simular_taxa_erro_tipo1(
    distribuicao,
    parametros: tuple,
    n: int,
    rng: np.random.Generator,
    n_simulacoes: int = N_SIMULACOES,
) -> dict[str, float]:
    """Gera n_simulacoes pares de amostras sob H0 e retorna a proporção de rejeições de cada teste."""
    rejeicoes = {"welch": 0, "mann_whitney": 0}
    for _ in range(n_simulacoes):
        grupo_a = distribuicao.rvs(*parametros, size=n, random_state=rng)
        grupo_b = distribuicao.rvs(*parametros, size=n, random_state=rng)
        if aplicar_welch(grupo_a, grupo_b)["p_valor"] < ALFA:
            rejeicoes["welch"] += 1
        if aplicar_mannwhitney(grupo_a, grupo_b)["p_valor"] < ALFA:
            rejeicoes["mann_whitney"] += 1
    return {teste: contagem / n_simulacoes for teste, contagem in rejeicoes.items()}


def calcular_erro_tipo1(rng: np.random.Generator) -> pd.DataFrame:
    """Calcula a taxa de erro tipo I dos dois testes em cada situação definida em construir_situacoes."""
    linhas = []
    for situacao, parametros in construir_situacoes().items():
        taxas = simular_taxa_erro_tipo1(
            parametros["distribuicao"], parametros["parametros"], parametros["n"], rng
        )
        for teste, taxa in taxas.items():
            linhas.append({"situacao": situacao, "teste": teste, "taxa_erro_tipo1": taxa})
    return pd.DataFrame(linhas)


def grafico_erro_tipo1(tabela: pd.DataFrame) -> go.Figure:
    """G3: taxa de erro tipo I dos dois testes em cada situação simulada, com linha em 5%."""
    figura = go.Figure()
    for teste in ["welch", "mann_whitney"]:
        dados_teste = tabela[tabela["teste"] == teste]
        figura.add_trace(
            go.Bar(
                x=dados_teste["situacao"],
                y=dados_teste["taxa_erro_tipo1"],
                name=NOMES_TESTES[teste],
                marker_color=CORES[teste],
            )
        )
    figura.add_hline(
        y=ALFA,
        line_dash="dash",
        line_color="black",
        annotation_text=f"alfa = {ALFA:.0%}",
        annotation_position="top left",
    )
    figura.update_layout(
        title="G3 — Erro tipo I por situação simulada (H0 verdadeira)",
        xaxis_title="Situação simulada",
        yaxis_title="Proporção de rejeições de H0 (p < 0,05)",
        yaxis_tickformat=".0%",
        legend_title="Teste",
        barmode="group",
    )
    return figura


def main() -> None:
    tabela = calcular_erro_tipo1(criar_rng())
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    tabela.to_csv(PASTA_RESULTADOS / "erro_tipo1.csv", index=False, float_format="%.4f")

    figura = grafico_erro_tipo1(tabela)
    figura.write_html(PASTA_RESULTADOS / "g3_erro_tipo1.html")

    print(tabela.to_string(index=False))


if __name__ == "__main__":
    main()
