"""Testes dos metadados da amostra. As respostas da API sao simuladas."""

from __future__ import annotations

from datetime import date

import pytest
import requests

from pipeline.metadados import (
    ERRO_LISTA_MUITO_GRANDE,
    coletar_contribuidores,
    contar_contribuidores,
    enriquecer_amostra,
    idade_dias,
    numero_ultima_pagina,
)
from pipeline.retomada import carregar_processados

URL = "https://api.github.com/repositories/1/contributors?per_page=1&anon=true"


def resposta(status: int = 200, json_body=None, ultima_pagina: int | None = None) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = b"" if json_body is None else requests.compat.json.dumps(json_body).encode()
    if ultima_pagina is not None:
        response.headers["Link"] = (
            f'<{URL}&page=2>; rel="next", <{URL}&page={ultima_pagina}>; rel="last"'
        )
    return response


def http_error(status: int, texto: str = "", headers: dict | None = None) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    response._content = texto.encode()
    response.headers.update(headers or {})
    return requests.HTTPError(f"HTTP {status}", response=response)


class FakeClient:
    """`respostas` mapeia full_name -> Response ou excecao."""

    def __init__(self, respostas: dict):
        self.respostas = respostas
        self.chamadas: list[tuple[str, dict]] = []

    def get_response(self, path, params=None):
        self.chamadas.append((path, params))
        full_name = path.removeprefix("/repos/").removesuffix("/contributors")
        r = self.respostas[full_name]
        if isinstance(r, Exception):
            raise r
        return r


def test_numero_ultima_pagina_le_o_link_last():
    assert numero_ultima_pagina(resposta(ultima_pagina=442)) == 442


def test_numero_ultima_pagina_sem_link_e_none():
    assert numero_ultima_pagina(resposta(json_body=[{"login": "a"}])) is None


def test_conta_pela_ultima_pagina_com_uma_chamada():
    client = FakeClient({"org/a": resposta(json_body=[{}], ultima_pagina=3259)})
    linha = contar_contribuidores(client, "org/a")

    assert linha == {"full_name": "org/a", "n_contribuidores": 3259, "erro_contribuidores": ""}
    assert client.chamadas == [("/repos/org/a/contributors", {"per_page": 1, "anon": "true"})]


def test_um_unico_contribuidor_nao_tem_link():
    client = FakeClient({"org/a": resposta(json_body=[{"login": "dono"}])})
    assert contar_contribuidores(client, "org/a")["n_contribuidores"] == 1


def test_repositorio_vazio_responde_204():
    client = FakeClient({"org/a": resposta(status=204)})
    assert contar_contribuidores(client, "org/a")["n_contribuidores"] == 0


def test_lista_muito_grande_fica_sem_valor_com_motivo():
    erro = http_error(403, '{"message": "The history or contributor list is too large to list contributors"}')
    linha = contar_contribuidores(FakeClient({"org/a": erro}), "org/a")

    assert linha["n_contribuidores"] is None
    assert linha["erro_contribuidores"] == ERRO_LISTA_MUITO_GRANDE


def test_outro_erro_http_vira_motivo():
    linha = contar_contribuidores(FakeClient({"org/a": http_error(404)}), "org/a")
    assert linha["erro_contribuidores"] == "erro_http_404"


def test_cota_esgotada_interrompe():
    erro = http_error(403, "rate limit", {"X-RateLimit-Remaining": "0"})
    with pytest.raises(requests.HTTPError):
        contar_contribuidores(FakeClient({"org/a": erro}), "org/a")


def test_erro_5xx_interrompe():
    with pytest.raises(requests.HTTPError):
        contar_contribuidores(FakeClient({"org/a": http_error(502)}), "org/a")


def test_idade_no_fim_da_janela():
    assert idade_dias("2025-11-24T10:16:47Z", date(2026, 9, 30)) == 310
    assert idade_dias("2016-09-30T00:00:00Z", date(2026, 9, 30)) == 3652


def test_coleta_com_retomada(tmp_path):
    saida = tmp_path / "contribuidores.csv"
    repos = [{"full_name": "org/a"}, {"full_name": "org/b"}]
    coletar_contribuidores(FakeClient({"org/a": resposta(ultima_pagina=5)}), repos[:1], saida)

    client = FakeClient({"org/b": resposta(ultima_pagina=9)})
    progresso = []
    resultado = coletar_contribuidores(
        client, repos, saida, progresso=lambda feitos, total: progresso.append((feitos, total))
    )

    assert [p for p, _ in client.chamadas] == ["/repos/org/b/contributors"]
    assert resultado["org/a"]["n_contribuidores"] == "5"  # lido do CSV
    assert resultado["org/b"]["n_contribuidores"] == 9
    assert progresso == [(1, 2)]
    assert set(carregar_processados(saida)) == {"org/a", "org/b"}


def test_enriquecer_amostra_acrescenta_colunas():
    amostra = [{"full_name": "org/a", "created_at": "2025-11-24T10:16:47Z", "language": "Go"}]
    contribuidores = {"org/a": {"n_contribuidores": 8, "erro_contribuidores": ""}}

    [repo] = enriquecer_amostra(amostra, contribuidores, date(2026, 9, 30))

    assert repo["language"] == "Go"
    assert repo["n_contribuidores"] == 8
    assert repo["erro_contribuidores"] == ""
    assert repo["idade_dias"] == 310
