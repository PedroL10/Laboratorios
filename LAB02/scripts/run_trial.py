"""Cronometra um trial do LAB02 e grava o registro descrito na secao 10
de docs/manual_execucao_trials.md.

Uso:
    python scripts/run_trial.py --participant P2 --kata K3 --treatment IA \
        --order 1 --trial-dir trials/P2/K3_IA --test-file test_kata_03.py

O script mede o tempo desde o inicio ate o instante em que todos os testes
passam (time-to-green) ou ate o time-box de 35 minutos (2100s) ser atingido.
A cada tentativa, executa o pytest no diretorio do trial e mostra o
resultado. Ao final, pede os dados que so o participante sabe (prompts,
assistente usado, notas) e acrescenta uma linha em trials/dados_trials.csv.
"""

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TIME_BOX_SECONDS = 2100

FIELDS = [
    "participant_id",
    "kata_id",
    "treatment",
    "order",
    "start_time",
    "end_time",
    "duration_seconds",
    "time_to_green_seconds",
    "time_box_seconds",
    "censored",
    "tests_total",
    "tests_passed",
    "tests_failed",
    "prompts_count",
    "python_version",
    "pytest_version",
    "assistant_name",
    "assistant_version",
    "notes",
]

SUMMARY_RE = re.compile(
    r"(?:(?P<failed>\d+) failed, )?(?P<passed>\d+) passed"
    r"(?:, (?P<errors>\d+) error)?"
)


def run_pytest(trial_dir: Path, test_file: str):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", test_file],
        cwd=trial_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode not in (0, 1):
        print(result.stderr)
    return parse_summary(result.stdout)


def parse_summary(output: str):
    match = SUMMARY_RE.search(output)
    if not match:
        return 0, 0
    passed = int(match.group("passed") or 0)
    failed = int(match.group("failed") or 0) + int(match.group("errors") or 0)
    return passed, failed


def tool_version(module_args):
    result = subprocess.run(
        [sys.executable, *module_args, "--version"],
        capture_output=True,
        text=True,
    )
    return (result.stdout or result.stderr).strip().splitlines()[0]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--participant", required=True, help="ex.: P2")
    parser.add_argument("--kata", required=True, help="ex.: K3")
    parser.add_argument("--treatment", required=True, choices=["IA", "MANUAL"])
    parser.add_argument("--order", required=True, type=int)
    parser.add_argument(
        "--trial-dir",
        required=True,
        type=Path,
        help="pasta da copia do trial (contem solution.py e o teste)",
    )
    parser.add_argument(
        "--test-file",
        required=True,
        help="nome do arquivo de teste, ex.: test_kata_03.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "trials" / "dados_trials.csv",
    )
    return parser.parse_args()


def ask(prompt, default=""):
    value = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return value or default


def main():
    args = parse_args()
    trial_dir = args.trial_dir.resolve()
    if not (trial_dir / "solution.py").exists():
        sys.exit(f"solution.py nao encontrado em {trial_dir}")

    python_version = tool_version(["-c", "import sys; print(sys.version)"])
    pytest_version = tool_version(["-m", "pytest"])

    input(
        f"Trial {args.participant}/{args.kata} ({args.treatment}, order={args.order}). "
        "Pressione Enter para iniciar o cronometro..."
    )
    start = time.monotonic()
    start_time = datetime.now(timezone.utc).astimezone()
    print(f"Iniciado em {start_time.isoformat()}. Time-box: {TIME_BOX_SECONDS}s.")

    time_to_green = None
    tests_passed = tests_failed = 0
    censored = True

    while True:
        elapsed = time.monotonic() - start
        remaining = TIME_BOX_SECONDS - elapsed
        if remaining <= 0:
            print("Time-box de 35 minutos atingido. Executando o pytest final...")
            tests_passed, tests_failed = run_pytest(trial_dir, args.test_file)
            break

        input(
            f"[{elapsed:0.0f}s / {TIME_BOX_SECONDS}s] Pressione Enter para rodar o pytest "
            "(ou Ctrl+C para interromper)..."
        )
        tests_passed, tests_failed = run_pytest(trial_dir, args.test_file)
        elapsed = time.monotonic() - start
        if tests_failed == 0 and tests_passed > 0:
            time_to_green = round(elapsed)
            censored = False
            print(f"Todos os testes passaram em {time_to_green}s.")
            break
        if elapsed >= TIME_BOX_SECONDS:
            print("Time-box atingido apos a execucao. Encerrando o trial.")
            break

    end_time = datetime.now(timezone.utc).astimezone()
    duration_seconds = TIME_BOX_SECONDS if censored else time_to_green

    prompts_count = 0
    assistant_name = "none"
    assistant_version = "none"
    if args.treatment == "IA":
        prompts_count = ask("Quantidade de prompts/interacoes com a IA", "0")
        assistant_name = ask("Nome do assistente de IA usado")
        assistant_version = ask("Versao do assistente de IA")
    notes = ask("Observacoes (dificuldades, interrupcoes, desvios)")

    row = {
        "participant_id": args.participant,
        "kata_id": args.kata,
        "treatment": args.treatment,
        "order": args.order,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "time_to_green_seconds": time_to_green if time_to_green is not None else "",
        "time_box_seconds": TIME_BOX_SECONDS,
        "censored": str(censored).lower(),
        "tests_total": tests_passed + tests_failed,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "prompts_count": prompts_count,
        "python_version": python_version,
        "pytest_version": pytest_version,
        "assistant_name": assistant_name,
        "assistant_version": assistant_version,
        "notes": notes,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    is_new = not args.output.exists()
    with args.output.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)

    print(f"Registro gravado em {args.output}")


if __name__ == "__main__":
    main()
