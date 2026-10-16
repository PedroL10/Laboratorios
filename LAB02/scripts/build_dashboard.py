"""Gera o dashboard de visualizacao do LAB02 (Passo 6).

Uso:
    python scripts/build_dashboard.py

Le trials/dados_trials.csv e trials/metricas_estaticas.csv e gera boxplots
(com os pontos individuais sobrepostos, dado o N pequeno) comparando IA vs
MANUAL para tempo, taxa de sucesso e as metricas estaticas de RQ3, alem de
um grafico pareado por kata e um dashboard consolidado. As figuras sao
salvas em resultados/graficos/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

LAB_ROOT = Path(__file__).resolve().parent.parent
TRIALS_CSV = LAB_ROOT / "trials" / "dados_trials.csv"
METRICS_CSV = LAB_ROOT / "trials" / "metricas_estaticas.csv"
OUTPUT_DIR = LAB_ROOT / "resultados" / "graficos"

PALETTE = {"IA": "#4C72B0", "MANUAL": "#DD8452"}
TREATMENT_ORDER = ["IA", "MANUAL"]

sns.set_theme(style="whitegrid", font_scale=1.05)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    trials = pd.read_csv(TRIALS_CSV)
    trials["censored"] = trials["censored"].astype(str).str.lower() == "true"
    trials["effective_time_seconds"] = trials["time_to_green_seconds"].where(
        ~trials["censored"], trials["time_box_seconds"]
    )
    trials["success_rate"] = trials["tests_passed"] / trials["tests_total"]

    metrics = pd.read_csv(METRICS_CSV)
    metrics["complexity_per_loc"] = metrics["complexity_total"] / metrics["loc"]
    return trials, metrics


def boxplot_with_points(df: pd.DataFrame, column: str, title: str, ylabel: str, filename: str) -> Path:
    fig, ax = plt.subplots(figsize=(5, 4.5))
    sns.boxplot(
        data=df, x="treatment", y=column, order=TREATMENT_ORDER,
        hue="treatment", palette=PALETTE, legend=False,
        width=0.5, showfliers=False, ax=ax,
    )
    sns.stripplot(
        data=df, x="treatment", y=column, order=TREATMENT_ORDER,
        color="black", size=6, alpha=0.7, jitter=0.08, ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Tratamento")
    ax.set_ylabel(ylabel)
    n_by_treatment = df.groupby("treatment")[column].count()
    labels = [f"{t}\n(n={n_by_treatment.get(t, 0)})" for t in TREATMENT_ORDER]
    ax.set_xticks(range(len(TREATMENT_ORDER)))
    ax.set_xticklabels(labels)
    fig.tight_layout()
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def paired_slope_chart(df: pd.DataFrame, column: str, title: str, ylabel: str, filename: str) -> Path:
    """Mostra, por kata, o valor de IA e de MANUAL ligados por uma linha.

    Torna visivel o pareamento por kata usado no teste de Wilcoxon
    (scripts/analyze_rq1_rq2.py e scripts/analyze_rq3.py).
    """
    pivot = df.groupby(["kata_id", "treatment"])[column].median().unstack("treatment")
    pivot = pivot.dropna(subset=["IA", "MANUAL"]).sort_index()

    fig, ax = plt.subplots(figsize=(5, 4.5))
    x_positions = [0, 1]
    for kata_id, row in pivot.iterrows():
        values = [row["IA"], row["MANUAL"]]
        ax.plot(x_positions, values, marker="o", label=kata_id)
        ax.annotate(kata_id, (x_positions[-1] + 0.03, values[-1]), fontsize=9)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(TREATMENT_ORDER)
    ax.set_xlim(-0.2, 1.3)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def build_summary_dashboard(trials: pd.DataFrame, metrics: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    panels = [
        (trials, "effective_time_seconds", "RQ1 - Tempo (time-to-green)", "segundos"),
        (trials, "success_rate", "RQ2 - Taxa de sucesso", "proporcao de testes"),
        (trials, "tests_failed", "RQ2 - Testes falhando", "quantidade"),
        (metrics, "loc", "RQ3 - LOC", "linhas de codigo"),
        (metrics, "complexity_per_loc", "RQ3 - Complexidade / LOC", "complexidade por linha"),
        (metrics, "duplicate_percentage", "RQ3 - Duplicacao", "% de linhas duplicadas"),
    ]

    for ax, (data, column, title, ylabel) in zip(axes.flat, panels):
        sns.boxplot(
            data=data, x="treatment", y=column, order=TREATMENT_ORDER,
            hue="treatment", palette=PALETTE, legend=False,
            width=0.5, showfliers=False, ax=ax,
        )
        sns.stripplot(
            data=data, x="treatment", y=column, order=TREATMENT_ORDER,
            color="black", size=5, alpha=0.7, jitter=0.08, ax=ax,
        )
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)

    fig.suptitle(
        "LAB02 - Dashboard IA vs MANUAL (dados parciais, ver aviso de N no relatorio)",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUTPUT_DIR / "dashboard_consolidado.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    trials, metrics = load_data()

    participants = sorted(trials["participant_id"].unique().tolist())
    missing = [p for p in ["P1", "P2", "P3"] if p not in participants]

    generated = [
        boxplot_with_points(
            trials, "effective_time_seconds",
            "RQ1 - Tempo ate passar nos testes (time-to-green)",
            "segundos", "rq1_tempo.png",
        ),
        boxplot_with_points(
            trials, "success_rate",
            "RQ2 - Taxa de sucesso ao final do time-box",
            "proporcao de testes passando", "rq2_taxa_sucesso.png",
        ),
        boxplot_with_points(
            metrics, "loc",
            "RQ3 - Linhas de codigo (LOC)",
            "LOC", "rq3_loc.png",
        ),
        boxplot_with_points(
            metrics, "complexity_per_loc",
            "RQ3 - Complexidade ciclomatica normalizada por LOC",
            "complexidade total / LOC", "rq3_complexidade_por_loc.png",
        ),
        boxplot_with_points(
            metrics, "duplicate_percentage",
            "RQ3 - Duplicacao de codigo",
            "% de linhas duplicadas", "rq3_duplicacao.png",
        ),
        paired_slope_chart(
            trials, "effective_time_seconds",
            "RQ1 - Tempo pareado por kata (IA vs MANUAL)",
            "segundos", "rq1_tempo_pareado_por_kata.png",
        ),
        paired_slope_chart(
            metrics, "complexity_per_loc",
            "RQ3 - Complexidade/LOC pareada por kata (IA vs MANUAL)",
            "complexidade total / LOC", "rq3_complexidade_pareada_por_kata.png",
        ),
        build_summary_dashboard(trials, metrics),
    ]

    print(f"{len(generated)} graficos gerados em {OUTPUT_DIR}:")
    for path in generated:
        print(f"  - {path.name}")

    if missing:
        print(
            f"\nAviso: participantes ausentes no dataset: {', '.join(missing)}. "
            "Os graficos refletem apenas os trials disponiveis ate o momento."
        )


if __name__ == "__main__":
    main()
