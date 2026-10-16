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
