"""Constantes visuais e gráficos do estudo.

Mantém a mesma cor para cada teste em todos os gráficos (G2, G3, G4).
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from lab04.config import ALFA

CORES = {
    "welch": "#1f77b4",
    "mann_whitney": "#ff7f0e",
}

NOMES_TESTES = {
    "welch": "t de Welch",
    "mann_whitney": "Mann-Whitney",
}

# Cores do G1, diferentes das cores dos testes para não confundir.
COR_REAL = "#6b7280"
COR_SIMULADO = "#2ca02c"
COR_REJEICAO = "#d62728"

NOMES_GRUPOS = {"sem_bot": "Sem bot (antes)", "com_bot": "Com bot (depois)"}
LARGURA_FAIXA_HORAS = 20


def grafico_dados(reais: dict, simulados: dict) -> go.Figure:
    """G1: histograma dos dados reais ao lado dos simulados, um painel por grupo."""
    grupos = list(NOMES_GRUPOS)
    maximo = max(max(np.max(reais[g]), np.max(simulados[g])) for g in grupos)
    faixas = {"start": 0, "end": maximo + LARGURA_FAIXA_HORAS, "size": LARGURA_FAIXA_HORAS}
    figura = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        subplot_titles=[NOMES_GRUPOS[g] for g in grupos],
    )
    for coluna, grupo in enumerate(grupos, start=1):
        for nome, valores, cor in (
            ("Dados reais", reais[grupo], COR_REAL),
            ("Dados simulados", simulados[grupo], COR_SIMULADO),
        ):
            figura.add_trace(
                go.Histogram(
                    x=valores,
                    xbins=faixas,
                    name=nome,
                    marker_color=cor,
                    opacity=0.6,
                    legendgroup=nome,
                    showlegend=coluna == 1,
                ),
                row=1,
                col=coluna,
            )
        figura.update_xaxes(title_text="Tempo até o merge (horas)", row=1, col=coluna)
    figura.update_xaxes(matches="x")  # mesma escala de horas nos dois painéis
    figura.update_yaxes(title_text="Número de PRs", row=1, col=1)
    figura.update_layout(
        title="G1 — Dados reais × simulados, por grupo",
        barmode="overlay",
        legend_title="Origem",
    )
    return figura


def _area(x: np.ndarray, y: np.ndarray, nome: str, legenda: bool, grupo: str, **preenchimento):
    """Área preenchida sob a curva, usada para a região de rejeição e para o p-valor."""
    return go.Scatter(
        x=np.concatenate([[x[0]], x, [x[-1]]]),
        y=np.concatenate([[0], y, [0]]),
        fill="toself",
        mode="none",
        name=nome,
        legendgroup=grupo,
        showlegend=legenda,
        hoverinfo="skip",
        **preenchimento,
    )


def _transparente(cor_hex: str, opacidade: float) -> str:
    r, g, b = (int(cor_hex[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacidade})"


def grafico_estatistica_h0(resultados: dict) -> go.Figure:
    """G2: distribuição de cada estatística sob H0, com a região de rejeição e o p-valor como área.

    `resultados` mapeia o teste ("welch", "mann_whitney") ao dicionário retornado por
    aplicar_welch e aplicar_mannwhitney. Sob H0, a estatística do t de Welch segue uma t de
    Student com os graus de liberdade de Welch, e o z do Mann-Whitney segue, aproximadamente,
    uma normal padrão.
    """
    testes = ["welch", "mann_whitney"]
    distribuicoes = {
        "welch": stats.t(resultados["welch"]["graus_liberdade"]),
        "mann_whitney": stats.norm(),
    }
    eixos_x = {
        "welch": "Estatística t (adimensional)",
        "mann_whitney": "Estatística z do Mann-Whitney (adimensional)",
    }
    figura = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"{NOMES_TESTES[t]}: observado = {resultados[t]['estatistica_padronizada']:.2f}, "
            f"p = {resultados[t]['p_valor']:.3f}".replace(".", ",")
            for t in testes
        ],
    )
    for coluna, teste in enumerate(testes, start=1):
        distribuicao = distribuicoes[teste]
        observada = resultados[teste]["estatistica_padronizada"]
        critico = distribuicao.ppf(1 - ALFA / 2)
        limite = max(4.0, abs(observada) + 0.5)
        x = np.linspace(-limite, limite, 801)
        densidade = distribuicao.pdf(x)
        legenda = coluna == 1

        for lado in (x <= -critico, x >= critico):
            figura.add_trace(
                _area(x[lado], densidade[lado], f"Região de rejeição (α = {ALFA:.0%})",
                      legenda, "rejeicao", fillcolor=_transparente(COR_REJEICAO, 0.35)),
                row=1, col=coluna,
            )
            legenda = False
        for indice, lado in enumerate((x <= -abs(observada), x >= abs(observada))):
            figura.add_trace(
                _area(x[lado], densidade[lado], f"p-valor do exemplo ({NOMES_TESTES[teste]})",
                      indice == 0, f"p-{teste}", fillcolor="rgba(0,0,0,0)",
                      fillpattern={"shape": "/", "fgcolor": CORES[teste], "solidity": 0.5}),
                row=1, col=coluna,
            )
        figura.add_trace(
            go.Scatter(
                x=x, y=densidade, mode="lines", line={"color": CORES[teste], "width": 2},
                name=f"Distribuição sob H₀ ({NOMES_TESTES[teste]})",
            ),
            row=1, col=coluna,
        )
        figura.add_vline(x=observada, line_dash="dash", line_color="black", row=1, col=coluna)
        figura.update_xaxes(title_text=eixos_x[teste], row=1, col=coluna)
    figura.update_yaxes(title_text="Densidade de probabilidade", row=1, col=1)
    figura.update_layout(
        title="G2 — Distribuição da estatística sob H₀ (dados reais como exemplo; tracejado = valor observado)"
    )
    return figura
