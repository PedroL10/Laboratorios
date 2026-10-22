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
