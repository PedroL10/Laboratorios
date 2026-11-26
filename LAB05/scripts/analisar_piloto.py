"""Análise exploratória da coleta piloto e estimativa de poder por simulação (LAB05).

1. Resume a latência do piloto (dados/coleta_piloto.csv).
2. Ajusta uma lognormal à latência por requisição.
3. Simula rodadas de 5 requisições nos dois períodos e estima o poder de cada teste
   candidato para a hipótese principal (docs/gqm_hipoteses_ameacas.md), com o mesmo
   raciocínio do LAB04.

Uso, de dentro de LAB05:
    python scripts/analisar_piloto.py
"""

import pathlib

import numpy as np
import pandas as pd
from scipy import stats

SEMENTE = 42
ALFA = 0.05
N_SIMULACOES = 5_000
TAMANHO_RODADA = 5
RODADAS_COMERCIAL = 90  # ~10 dias úteis x 9 horas
RODADAS_FORA = 150  # ~10 dias úteis x 15 horas
FATORES_EFEITO = (1.0, 1.1, 1.2, 1.3, 1.5)  # horário comercial X vezes mais lento
SIGMAS_RODADA = (0.0, 0.3)  # variação entre rodadas, que o piloto não permite estimar

PASTA = pathlib.Path(__file__).resolve().parent.parent
ARQUIVO_PILOTO = PASTA / "dados" / "coleta_piloto.csv"
PASTA_RESULTADOS = PASTA / "resultados"


def descrever(latencias: pd.Series) -> pd.DataFrame:
    """Estatística descritiva da latência por requisição, em ms."""
    resumo = {
        "n": len(latencias),
        "minimo_ms": latencias.min(),
        "p25_ms": latencias.quantile(0.25),
        "mediana_ms": latencias.median(),
        "media_ms": latencias.mean(),
        "p75_ms": latencias.quantile(0.75),
        "p95_ms": latencias.quantile(0.95),
        "maximo_ms": latencias.max(),
        "desvio_padrao_ms": latencias.std(),
        "coef_variacao": latencias.std() / latencias.mean(),
        "assimetria": stats.skew(latencias),
    }
    return pd.DataFrame([resumo]).round(3)


def ajustar_lognormal(latencias: pd.Series) -> tuple[float, float]:
    """Devolve (sigma, mediana) da lognormal ajustada com loc = 0."""
    sigma, _, escala = stats.lognorm.fit(latencias, floc=0)
    return sigma, escala


def simular_rodadas(rng, n_rodadas, sigma, mediana, sigma_rodada, fator):
    """Medianas de rodadas simuladas, com forma (N_SIMULACOES, n_rodadas)."""
    efeito_rodada = rng.normal(0.0, sigma_rodada, size=(N_SIMULACOES, n_rodadas, 1))
    log_lat = np.log(mediana * fator) + efeito_rodada + rng.normal(
        0.0, sigma, size=(N_SIMULACOES, n_rodadas, TAMANHO_RODADA)
    )
    return np.median(np.exp(log_lat), axis=2)


def estimar_poder(sigma: float, mediana: float) -> pd.DataFrame:
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for sigma_rodada in SIGMAS_RODADA:
        for fator in FATORES_EFEITO:
            comercial = simular_rodadas(rng, RODADAS_COMERCIAL, sigma, mediana, sigma_rodada, fator)
            fora = simular_rodadas(rng, RODADAS_FORA, sigma, mediana, sigma_rodada, 1.0)
            p_valores = {
                "welch": stats.ttest_ind(comercial, fora, axis=1, equal_var=False).pvalue,
                "welch_log": stats.ttest_ind(
                    np.log(comercial), np.log(fora), axis=1, equal_var=False
                ).pvalue,
                "mann_whitney": stats.mannwhitneyu(
                    comercial, fora, axis=1, alternative="two-sided"
                ).pvalue,
            }
            for teste, p in p_valores.items():
                linhas.append(
                    {
                        "sigma_rodada": sigma_rodada,
                        "fator_efeito": fator,
                        "teste": teste,
                        "taxa_rejeicao": float(np.mean(p < ALFA)),
                    }
                )
    return pd.DataFrame(linhas)


def main() -> None:
    piloto = pd.read_csv(ARQUIVO_PILOTO)
    latencias = piloto.loc[piloto["status_http"] == 200, "latencia_ms"]
    PASTA_RESULTADOS.mkdir(exist_ok=True)

    descritiva = descrever(latencias)
    sigma, mediana = ajustar_lognormal(latencias)
    descritiva["lognormal_sigma"] = round(sigma, 3)
    descritiva["lognormal_mediana_ms"] = round(mediana, 3)
    descritiva.to_csv(PASTA_RESULTADOS / "piloto_descritiva.csv", index=False)

    poder = estimar_poder(sigma, mediana)
    poder.to_csv(PASTA_RESULTADOS / "poder_simulado.csv", index=False)

    print(descritiva.T.to_string(header=False))
    tabela = poder.pivot_table(
        index=["sigma_rodada", "fator_efeito"], columns="teste", values="taxa_rejeicao"
    )
    print((tabela * 100).round(1).to_string())


if __name__ == "__main__":
    main()
