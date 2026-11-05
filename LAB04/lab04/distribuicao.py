"""Descreve a forma da distribuição dos dados reais e compara ajustes candidatos."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).parent.parent
ARQUIVO_DADOS = RAIZ / "dados" / "prs.csv"
PASTA_RESULTADOS = RAIZ / "resultados"

# As distribuições positivas começam em zero, como um tempo de merge.
CANDIDATAS = {
    "normal": (stats.norm, {}),
    "lognormal": (stats.lognorm, {"floc": 0}),
    "gamma": (stats.gamma, {"floc": 0}),
    "weibull": (stats.weibull_min, {"floc": 0}),
}


def carregar_grupos() -> dict[str, np.ndarray]:
    """Retorna as horas até o merge de cada grupo e de todos os PRs juntos."""
    dados = pd.read_csv(ARQUIVO_DADOS)
    grupos = {g: d["horas_ate_merge"].to_numpy() for g, d in dados.groupby("grupo")}
    grupos["todos"] = dados["horas_ate_merge"].to_numpy()
    return grupos


def contar_outliers(valores: np.ndarray) -> int:
    """Conta os valores fora das cercas de Tukey (1,5 IQR além dos quartis)."""
    q1, q3 = np.percentile(valores, [25, 75])
    margem = 1.5 * (q3 - q1)
    return int(np.sum((valores < q1 - margem) | (valores > q3 + margem)))


def resumir(horas: np.ndarray) -> dict:
    """Calcula as medidas de forma em horas e na escala logarítmica."""
    logs = np.log(horas)
    q1, q3 = np.percentile(horas, [25, 75])
    return {
        "n": len(horas),
        "media_h": horas.mean(),
        "mediana_h": np.median(horas),
        "dp_h": horas.std(ddof=1),
        "q1_h": q1,
        "q3_h": q3,
        "coef_variacao": horas.std(ddof=1) / horas.mean(),
        "assimetria": stats.skew(horas, bias=False),
        "outliers_tukey": contar_outliers(horas),
        "shapiro_p": stats.shapiro(horas).pvalue,
        "media_log": logs.mean(),
        "dp_log": logs.std(ddof=1),
        "assimetria_log": stats.skew(logs, bias=False),
        "shapiro_p_log": stats.shapiro(logs).pvalue,
    }


def comparar_ajustes(horas: np.ndarray) -> pd.DataFrame:
    """Ajusta as candidatas por máxima verossimilhança e ordena pelo AIC (menor é melhor)."""
    linhas = []
    for nome, (distribuicao, fixos) in CANDIDATAS.items():
        parametros = distribuicao.fit(horas, **fixos)
        n_livres = len(parametros) - len(fixos)
        log_verossimilhanca = distribuicao.logpdf(horas, *parametros).sum()
        linhas.append(
            {
                "distribuicao": nome,
                "forma": parametros[0] if len(parametros) == 3 else np.nan,
                "escala": parametros[-1],
                "aic": 2 * n_livres - 2 * log_verossimilhanca,
            }
        )
    ajustes = pd.DataFrame(linhas).sort_values("aic", ignore_index=True)
    ajustes["delta_aic"] = ajustes["aic"] - ajustes["aic"].min()
    return ajustes


def analisar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera as tabelas de forma e de ajustes e as salva em resultados/."""
    grupos = carregar_grupos()
    forma = pd.DataFrame({nome: resumir(horas) for nome, horas in grupos.items()}).T
    forma = forma.rename_axis("grupo").reset_index()
    ajustes = pd.concat(
        comparar_ajustes(horas).assign(grupo=nome) for nome, horas in grupos.items()
    )
    ajustes = ajustes[["grupo", "distribuicao", "forma", "escala", "aic", "delta_aic"]]

    PASTA_RESULTADOS.mkdir(exist_ok=True)
    forma.to_csv(PASTA_RESULTADOS / "forma_distribuicao.csv", index=False, float_format="%.4f")
    ajustes.to_csv(PASTA_RESULTADOS / "ajustes_distribuicao.csv", index=False, float_format="%.4f")
    return forma, ajustes
