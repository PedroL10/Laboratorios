"""Analisa RQ3 (estrutura do codigo) do LAB02 a partir de trials/metricas_estaticas.csv.

Uso:
    python scripts/analyze_rq3.py

Le trials/metricas_estaticas.csv, compara LOC, complexidade ciclomatica media
e duplicacao entre os tratamentos IA e MANUAL, normalizando a complexidade e
a duplicacao por LOC (metrica de controle, conforme docs/desenho_experimento.md
secao 3), e roda o teste de Wilcoxon pareado por kata para cada metrica.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

LAB_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = LAB_ROOT / "trials" / "metricas_estaticas.csv"
DEFAULT_OUTPUT = LAB_ROOT / "resultados" / "analise_rq3.json"

METRICS = ["loc", "complexity_mean", "complexity_per_loc", "duplicate_percentage"]


def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["complexity_per_loc"] = df["complexity_total"] / df["loc"]
    return df


def describe_by_treatment(df: pd.DataFrame, column: str) -> dict:
    summary = {}
    for treatment, group in df.groupby("treatment"):
        values = group[column]
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        summary[treatment] = {
            "n": int(values.count()),
            "median": float(values.median()),
            "iqr": float(q3 - q1),
            "q1": float(q1),
            "q3": float(q3),
            "min": float(values.min()),
            "max": float(values.max()),
        }
    return summary


def find_outliers(df: pd.DataFrame, column: str) -> list[dict]:
    outliers = []
    for treatment, group in df.groupby("treatment"):
        values = group[column]
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flagged = group[(values < low) | (values > high)]
        for _, row in flagged.iterrows():
            outliers.append(
                {
                    "participant_id": row["participant_id"],
                    "kata_id": row["kata_id"],
                    "treatment": treatment,
                    column: float(row[column]),
                    "bounds": [float(low), float(high)],
                }
            )
    return outliers


def paired_by_kata(df: pd.DataFrame, column: str) -> tuple[list[str], list[float], list[float]]:
    """Agrega por kata+tratamento (mediana) e pareia IA vs MANUAL por kata.

    Mesma logica de pareamento usada em analyze_rq1_rq2.py: o kata e a
    unidade pareada, pois cada participante so resolve cada kata em um
    tratamento.
    """
    per_kata_treatment = df.groupby(["kata_id", "treatment"])[column].median()
    katas_with_both = [
        kata
        for kata in df["kata_id"].unique()
        if (kata, "IA") in per_kata_treatment.index and (kata, "MANUAL") in per_kata_treatment.index
    ]
    katas_with_both.sort()
    ia_values = [float(per_kata_treatment[(k, "IA")]) for k in katas_with_both]
    manual_values = [float(per_kata_treatment[(k, "MANUAL")]) for k in katas_with_both]
    return katas_with_both, ia_values, manual_values


def run_wilcoxon(ia_values: list[float], manual_values: list[float]) -> dict:
    if len(ia_values) < 2:
        return {"error": "N insuficiente para o teste de Wilcoxon (minimo 2 pares)."}
    try:
        statistic, p_value = wilcoxon(ia_values, manual_values)
        return {
            "n_pairs": len(ia_values),
            "statistic": float(statistic),
            "p_value": float(p_value),
            "significant_0.05": bool(p_value < 0.05),
        }
    except ValueError as exc:
        return {"error": str(exc), "n_pairs": len(ia_values)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_metrics(args.input)

    participants_present = sorted(df["participant_id"].unique().tolist())
    expected_participants = ["P1", "P2", "P3"]
    missing_participants = [p for p in expected_participants if p not in participants_present]

    result = {"n_trials": int(len(df)), "participants_present": participants_present}

    for metric in METRICS:
        katas, ia_values, manual_values = paired_by_kata(df, metric)
        result[metric] = {
            "description_by_treatment": describe_by_treatment(df, metric),
            "outliers": find_outliers(df, metric),
            "paired_katas": katas,
            "wilcoxon": run_wilcoxon(ia_values, manual_values),
        }

    if missing_participants:
        result["warning"] = (
            f"Participantes ausentes no dataset: {', '.join(missing_participants)}. "
            "Este resultado e preliminar ate os 12 trials estarem completos."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nResultado gravado em {args.output}")


if __name__ == "__main__":
    main()
