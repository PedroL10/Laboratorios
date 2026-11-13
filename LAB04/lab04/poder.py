"""Q2 e Q3 (parte do poder): quando há efeito, com que frequência cada teste o detecta?

Para cada situação, multiplica os tempos de um dos grupos por fatores crescentes, começando
em 1 (sem efeito), e conta a proporção de rejeições de H0 em N_SIMULACOES repetições.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from lab04.config import ALFA, N_SIMULACOES, criar_rng
from lab04.erro_tipo1 import construir_situacoes
from lab04.graficos import CORES, NOMES_TESTES
from lab04.testes import taxas_rejeicao

RAIZ = Path(__file__).parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"

# Fator que multiplica o tempo até o merge do grupo com bot. Nos dados reais, a média do
# grupo com bot é 1,68 vez a do grupo sem bot.
FATORES_EFEITO = (1.0, 1.25, 1.5, 1.75, 2.0, 2.5)

# Um traço por situação, para distinguir as curvas da mesma cor (mesmo teste).
TRACOS = ("solid", "dash", "dot")


def calcular_poder(
    rng: np.random.Generator,
    fatores: tuple[float, ...] = FATORES_EFEITO,
    n_simulacoes: int = N_SIMULACOES,
) -> pd.DataFrame:
    """Calcula a proporção de rejeições de cada teste em cada situação e tamanho de efeito."""
    linhas = []
    for situacao, config in construir_situacoes().items():
        for fator in fatores:
            taxas = taxas_rejeicao(
                config["distribuicao"], config["parametros"], config["n"], fator, rng, n_simulacoes
            )
            for teste, taxa in taxas.items():
                linhas.append(
                    {"situacao": situacao, "fator_efeito": fator, "teste": teste, "taxa_rejeicao": taxa}
                )
    return pd.DataFrame(linhas)


def grafico_poder(tabela: pd.DataFrame) -> go.Figure:
    """G4: curvas de poder dos dois testes, uma por situação, no mesmo gráfico."""
    figura = go.Figure()
    for situacao, traco in zip(tabela["situacao"].unique(), TRACOS):
        for teste in ["welch", "mann_whitney"]:
            dados = tabela[(tabela["situacao"] == situacao) & (tabela["teste"] == teste)]
            figura.add_trace(
                go.Scatter(
                    x=dados["fator_efeito"],
                    y=dados["taxa_rejeicao"],
                    mode="lines+markers",
                    name=f"{NOMES_TESTES[teste]}, {situacao}",
                    line={"color": CORES[teste], "dash": traco},
                )
            )
    figura.add_hline(
        y=ALFA,
        line_dash="dash",
        line_color="black",
        annotation_text=f"α = {ALFA:.0%}",
        annotation_position="bottom right",
    )
    figura.update_layout(
        title="G4 — Poder dos testes por tamanho do efeito",
        xaxis_title="Tamanho do efeito (fator multiplicativo no tempo até o merge, ×)",
        yaxis_title="Proporção de rejeições de H0 (p < 0,05)",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1],
        legend_title="Teste e situação",
    )
    return figura


def main() -> None:
    tabela = calcular_poder(criar_rng())
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    tabela.to_csv(PASTA_RESULTADOS / "poder.csv", index=False, float_format="%.4f")
    print(tabela.pivot_table(index=["situacao", "fator_efeito"], columns="teste").round(3))


if __name__ == "__main__":
    main()
