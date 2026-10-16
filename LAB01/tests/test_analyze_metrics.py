"""Testes de regressao para os calculos da Sprint 3."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analyze_metrics import analyze, parse_args  # noqa: E402


REFERENCE_AT = datetime(2026, 8, 24, tzinfo=timezone.utc)


def repo(**overrides):
    base = {
        "name_with_owner": "org/repo",
        "created_at": "2020-08-24T00:00:00Z",
        "pushed_at": "2026-08-14T00:00:00Z",
        "primary_language": "Python",
        "releases_total": "10",
        "issues_total": "20",
        "issues_closed_total": "15",
        "pull_requests_merged_total": "30",
    }
    base.update(overrides)
    return base


class AnalyzeMetricsTests(unittest.TestCase):
    def test_rq08_separa_repositorios_sem_linguagem(self):
        metrics = analyze(
            [
                repo(name_with_owner="org/com-linguagem"),
                repo(
                    name_with_owner="org/sem-linguagem",
                    primary_language="",
                    releases_total="0",
                    pull_requests_merged_total="2",
                    pushed_at="2025-08-24T00:00:00Z",
                ),
            ],
            REFERENCE_AT,
        )

        rq08 = metrics["RQ08_sem_linguagem"]
        self.assertEqual(rq08["sem_linguagem"]["quantidade_repos"], 1)
        self.assertEqual(rq08["sem_linguagem"]["mediana_releases"], 0)
        self.assertEqual(rq08["sem_linguagem"]["mediana_dias_sem_update"], 365)
        self.assertEqual(rq08["com_linguagem"]["quantidade_repos"], 1)

    def test_rq07_descarta_grupos_com_menos_de_dez_repositorios(self):
        repos = [repo(name_with_owner=f"org/python-{index}") for index in range(10)]
        repos.append(repo(name_with_owner="org/rust", primary_language="Rust"))

        metrics = analyze(repos, REFERENCE_AT)

        self.assertEqual(set(metrics["RQ07_por_linguagem"]), {"Python"})

    def test_parse_args_aceita_data_de_referencia(self):
        _, _, reference_at = parse_args(["--reference-at", "2026-08-24T00:00:00Z"])

        self.assertEqual(reference_at, REFERENCE_AT)


if __name__ == "__main__":
    unittest.main()
