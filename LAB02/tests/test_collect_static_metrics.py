import csv
import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "collect_static_metrics.py"
SPEC = importlib.util.spec_from_file_location("collect_static_metrics", SCRIPT_PATH)
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


def test_radon_metrics_summarizes_functions(monkeypatch, tmp_path):
    source = tmp_path / "solution.py"
    source.write_text("def answer():\n    return 42\n", encoding="utf-8")

    def fake_command(command, *, cwd=None):
        if "raw" in command:
            return '{"' + str(source) + '": {"loc": 2, "lloc": 2, "sloc": 2, "comments": 0, "blank": 0}}'
        return '{"' + str(source) + '": [{"complexity": 1, "rank": "A"}]}'

    monkeypatch.setattr(metrics, "command_output", fake_command)

    assert metrics.radon_metrics(source) == {
        "loc": 2,
        "lloc": 2,
        "sloc": 2,
        "comments": 0,
        "blank": 0,
        "complexity_function_count": 1,
        "complexity_total": 1,
        "complexity_mean": 1.0,
        "complexity_max": 1,
        "complexity_rank_worst": "A",
    }


def test_append_record_creates_header_and_prevents_duplicate(tmp_path):
    output = tmp_path / "metricas.csv"
    row = {field: "" for field in metrics.FIELDS}
    row.update({"participant_id": "P1", "kata_id": "K1", "treatment": "IA"})

    metrics.append_record(output, row)

    with output.open(newline="", encoding="utf-8") as file:
        saved = list(csv.DictReader(file))
    assert saved == [{key: str(value) for key, value in row.items()}]
    assert metrics.record_exists(output, "P1", "K1", "IA")
    assert not metrics.record_exists(output, "P1", "K1", "MANUAL")
