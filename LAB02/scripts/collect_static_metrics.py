"""Coleta metricas estaticas de um trial finalizado do LAB02.

Uso:
    python scripts/collect_static_metrics.py --participant P1 --kata K1 \
        --treatment IA --trial-dir trials/P1/K1_IA

O script analisa somente ``solution.py`` do trial. Ele usa Radon para as
metricas de tamanho e complexidade e JSCPD para duplicacao, gravando uma linha
auditavel em ``trials/metricas_estaticas.csv``.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "participant_id",
    "kata_id",
    "treatment",
    "source_path",
    "analyzed_at",
    "loc",
    "lloc",
    "sloc",
    "comments",
    "blank",
    "complexity_function_count",
    "complexity_total",
    "complexity_mean",
    "complexity_max",
    "complexity_rank_worst",
    "duplicate_lines",
    "duplicate_percentage",
    "radon_version",
    "jscpd_version",
]

LAB_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = LAB_ROOT / "trials" / "metricas_estaticas.csv"


def command_output(command: list[str], *, cwd: Path | None = None) -> str:
    """Executa uma ferramenta e retorna stdout; falhas nao sao silenciosas."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Falha ao executar {' '.join(command)}: {details}")
    return result.stdout.strip()


def tool_version(command: list[str]) -> str:
    output = command_output(command).splitlines()
    return output[0].strip() if output else "unknown"


def radon_metrics(source: Path) -> dict[str, object]:
    """Obtem metricas brutas e complexidade do Radon em JSON."""
    raw = json.loads(command_output([sys.executable, "-m", "radon", "raw", "-j", str(source)]))
    complexity = json.loads(
        command_output([sys.executable, "-m", "radon", "cc", "-j", str(source)])
    )
    raw_values = raw[str(source)]
    blocks = complexity[str(source)]
    scores = [int(block["complexity"]) for block in blocks]
    ranks = [str(block["rank"]) for block in blocks]
    return {
        "loc": raw_values["loc"],
        "lloc": raw_values["lloc"],
        "sloc": raw_values["sloc"],
        "comments": raw_values["comments"],
        "blank": raw_values["blank"],
        "complexity_function_count": len(scores),
        "complexity_total": sum(scores),
        "complexity_mean": round(sum(scores) / len(scores), 4) if scores else 0,
        "complexity_max": max(scores, default=0),
        "complexity_rank_worst": max(ranks, default="N/A"),
    }


def find_jscpd_command() -> list[str]:
    """Prefere instalacao local versionada e aceita JSCPD no PATH."""
    local_binary = LAB_ROOT / "node_modules" / ".bin" / "jscpd"
    if local_binary.exists():
        return [str(local_binary)]
    if binary := shutil.which("jscpd"):
        return [binary]
    raise RuntimeError("JSCPD nao encontrado. Execute `npm install` dentro de LAB02.")


def jscpd_metrics(source: Path) -> dict[str, object]:
    """Executa JSCPD em um unico arquivo e le o relatorio JSON gerado."""
    with tempfile.TemporaryDirectory(prefix="lab02-jscpd-") as temp_dir:
        report_dir = Path(temp_dir)
        command_output(
            [
                *find_jscpd_command(),
                "--format",
                "python",
                "--reporters",
                "json",
                "--output",
                str(report_dir),
                str(source),
            ],
            cwd=LAB_ROOT,
        )
        report_path = report_dir / "jscpd-report.json"
        if not report_path.exists():
            raise RuntimeError("JSCPD terminou sem gerar jscpd-report.json.")
        report = json.loads(report_path.read_text(encoding="utf-8"))

    total = report["statistics"]["total"]
    return {
        "duplicate_lines": int(total.get("clonedLines", 0)),
        "duplicate_percentage": float(total.get("percentage", 0)),
    }


def record_exists(output: Path, participant: str, kata: str, treatment: str) -> bool:
    if not output.exists():
        return False
    with output.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if (row["participant_id"], row["kata_id"], row["treatment"]) == (
                participant,
                kata,
                treatment,
            ):
                return True
    return False


def append_record(output: Path, row: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    is_new = not output.exists()
    with output.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--participant", required=True, choices=["P1", "P2", "P3"])
    parser.add_argument("--kata", required=True, choices=["K1", "K2", "K3", "K4"])
    parser.add_argument("--treatment", required=True, choices=["IA", "MANUAL"])
    parser.add_argument("--trial-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trial_dir = args.trial_dir.resolve()
    source = trial_dir / "solution.py"
    output = args.output.resolve()
    if not source.is_file():
        raise SystemExit(f"solution.py nao encontrado em {trial_dir}")
    if record_exists(output, args.participant, args.kata, args.treatment):
        raise SystemExit(
            "Ja existe uma metrica para este participant/kata/treatment; "
            "o registro anterior foi preservado."
        )

    metrics = radon_metrics(source) | jscpd_metrics(source)
    row = {
        "participant_id": args.participant,
        "kata_id": args.kata,
        "treatment": args.treatment,
        "source_path": str(source.relative_to(LAB_ROOT)),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        **metrics,
        "radon_version": tool_version([sys.executable, "-m", "radon", "--version"]),
        "jscpd_version": tool_version([*find_jscpd_command(), "--version"]),
    }
    append_record(output, row)
    print(f"Metricas gravadas em {output}")


if __name__ == "__main__":
    main()
