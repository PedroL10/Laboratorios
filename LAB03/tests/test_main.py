"""Testes das mensagens de erro do comando principal."""

from __future__ import annotations

import requests

from pipeline.__main__ import mensagem_de_erro


def http_error(status: int, headers: dict | None = None) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    return requests.HTTPError(f"HTTP {status}", response=response)


def test_mensagem_token_invalido():
    assert "token do GitHub invalido" in mensagem_de_erro(http_error(401))


def test_mensagem_cota_esgotada_informa_horario():
    erro = http_error(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1791479430"})
    mensagem = mensagem_de_erro(erro)
    assert "cota da API esgotada" in mensagem
    assert "continua de onde parou" in mensagem


def test_mensagem_erro_temporario():
    assert "erro temporario do GitHub (504)" in mensagem_de_erro(http_error(504))


def test_outros_erros_mostram_a_mensagem_original():
    assert mensagem_de_erro(http_error(418)) == "HTTP 418"


def test_parametro_somente_selecao():
    from pipeline.__main__ import parse_args

    assert parse_args(["--somente-selecao"]).somente_selecao is True
    assert parse_args([]).somente_selecao is False


def test_etapa_workflow_runs_gera_cfr_ci_e_recuperacao(tmp_path, capsys):
    import csv

    from pipeline.__main__ import etapa_workflow_runs
    from tests.test_workflow_runs import FakeClient, run_api

    runs = [
        run_api(1, "2024-01-05T09:00:00Z", "success"),
        run_api(2, "2024-01-05T10:00:00Z", "failure"),
        run_api(3, "2024-01-05T12:00:00Z", "success"),
        run_api(4, "2024-01-06T12:00:00Z", "cancelled"),
    ]
    amostra = [{"full_name": "org/a", "default_branch": "main"}]
    janela = {"inicio": "2024-01-01", "fim": "2024-03-31"}

    etapa_workflow_runs(FakeClient(runs), amostra, janela, tmp_path / "cache", tmp_path)

    with (tmp_path / "cfr_ci.csv").open(encoding="utf-8") as f:
        cfr_ci = next(csv.DictReader(f))
    assert float(cfr_ci["cfr_ci"]) == 1 / 3
    assert cfr_ci["n_runs_ignorados"] == "1"
    with (tmp_path / "recuperacao.csv").open(encoding="utf-8") as f:
        recuperacao = next(csv.DictReader(f))
    assert float(recuperacao["tempo_recuperacao_horas"]) == 2.0
    assert "[8] Coletando workflow runs" in capsys.readouterr().out


def test_etapa_releases_gera_frequencia_lead_time_e_cfr(tmp_path):
    import csv

    from pipeline.__main__ import etapa_releases_lead_time_e_cfr

    def release(tag, publicada, prerelease=False):
        return {"id": hash(tag), "tag_name": tag, "target_commitish": "main", "draft": False,
                "prerelease": prerelease, "published_at": publicada}

    class Client:
        def get_paginated(self, path, params=None, items_key=None, max_pages=None):
            # Mais nova primeiro, como a API; v0 e de antes da janela.
            yield from [
                release("v1.1.0", "2024-12-31T20:00:00Z"),
                release("v1.1.0-rc1", "2024-06-01T00:00:00Z", prerelease=True),
                release("v1.0.0", "2024-03-15T00:00:00Z"),
                release("v0.9.0", "2023-12-01T00:00:00Z"),
            ]

        def get(self, path, params=None):
            commits = {
                "v0.9.0...v1.0.0": ["2024-03-02T00:00:00Z", "2024-03-14T00:00:00Z"],
                "v1.0.0...v1.1.0": ["2024-12-30T20:00:00Z"],
            }[path.rsplit("/compare/", 1)[1]]
            return {"commits": [{"commit": {"author": {"date": d}, "message": "feat"}} for d in commits]}

    janela = {"inicio": "2024-01-01", "fim": "2024-12-31"}
    etapa_releases_lead_time_e_cfr(
        Client(), [{"full_name": "org/a"}], janela, tmp_path / "cache", tmp_path
    )

    with (tmp_path / "frequencia.csv").open(encoding="utf-8") as f:
        frequencia = next(csv.DictReader(f))
    # v1.0.0 e v1.1.0 (publicada no ultimo dia); pre-release fica de fora.
    assert frequencia["n_releases_janela"] == "2"
    assert float(frequencia["deployment_frequency"]) == 2 / (366 / 7)
    with (tmp_path / "lead_time.csv").open(encoding="utf-8") as f:
        lead_time = next(csv.DictReader(f))
    # v1.0.0 comparada com v0.9.0 (fora da janela): 13 dias; v1.1.0: 1 dia.
    assert lead_time["n_releases_variante_a"] == "2"
    assert float(lead_time["lead_time_release_dias"]) == 7.0
    assert (tmp_path / "cfr.csv").exists()
