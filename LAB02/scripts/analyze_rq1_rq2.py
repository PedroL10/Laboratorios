"""Analisa RQ1 (tempo) e RQ2 (defeitos) do LAB02 a partir de trials/dados_trials.csv.

Uso:
    python scripts/analyze_rq1_rq2.py

Le trials/dados_trials.csv, calcula mediana/IQR de time-to-green e da taxa de
sucesso por tratamento (IA vs MANUAL), identifica outliers pela regra do IQR
e roda o teste de Wilcoxon pareado (por kata) para RQ1 e RQ2, conforme o plano
de analise descrito em docs/desenho_experimento.md (secao 11).

Trials censurados usam time_box_seconds (2100s) como tempo efetivo, para nao
favorecer o tratamento com mais falhas.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

LAB_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = LAB_ROOT / "trials" / "dados_trials.csv"
DEFAULT_OUTPUT = LAB_ROOT / "resultados" / "analise_rq1_rq2.json"


def load_trials(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["censored"] = df["censored"].astype(str).str.lower() == "true"
    df["effective_time_seconds"] = df["time_to_green_seconds"].where(
        ~df["censored"], df["time_box_seconds"]
    )
    df["success_rate"] = df["tests_passed"] / df["tests_total"]
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

    O pareamento usa o kata como unidade, nao o participante, porque cada
    participante resolve cada kata em um unico tratamento (desenho
    contrabalanceado entre participantes, nao repetido por individuo).
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
    df = load_trials(args.input)

    participants_present = sorted(df["participant_id"].unique().tolist())
    expected_participants = ["P1", "P2", "P3"]
    missing_participants = [p for p in expected_participants if p not in participants_present]

    rq1_katas, rq1_ia, rq1_manual = paired_by_kata(df, "effective_time_seconds")
    rq2_katas, rq2_ia, rq2_manual = paired_by_kata(df, "success_rate")

    result = {
        "n_trials": int(len(df)),
        "participants_present": participants_present,
        "participants_missing": missing_participants,
        "rq1_time_to_green": {
            "description_by_treatment": describe_by_treatment(df, "effective_time_seconds"),
            "outliers": find_outliers(df, "effective_time_seconds"),
            "paired_katas": rq1_katas,
            "wilcoxon": run_wilcoxon(rq1_ia, rq1_manual),
        },
        "rq2_success_rate": {
            "description_by_treatment": describe_by_treatment(df, "success_rate"),
            "outliers": find_outliers(df, "success_rate"),
            "paired_katas": rq2_katas,
            "wilcoxon": run_wilcoxon(rq2_ia, rq2_manual),
        },
        "rq2_tests_failed": {
            "description_by_treatment": describe_by_treatment(df, "tests_failed"),
        },
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
