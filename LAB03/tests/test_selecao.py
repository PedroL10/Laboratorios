"""Testes da busca de candidatos. A API de busca e simulada sobre uma populacao ficticia."""

from __future__ import annotations

import csv
import re

from pipeline.selecao import (
    CANDIDATE_FIELDS,
    buscar_candidatos,
    montar_faixa,
    resumir_repositorio,
    salvar_csv,
)


def repo(nome: str, estrelas: int) -> dict:
    return {
        "full_name": f"org/{nome}",
        "name": nome,
        "owner": {"login": "org"},
        "stargazers_count": estrelas,
        "language": "Python",
        "created_at": "2020-01-01T00:00:00Z",
        "default_branch": "main",
        "archived": False,
        "fork": False,
        "html_url": f"https://github.com/org/{nome}",
    }


class FakeSearchClient:
    """Imita GET /search/repositories: filtra pela faixa, ordena por estrelas
    (desc), pagina e corta em 1.000 resultados, como a API real."""

    def __init__(self, populacao: list[dict], teto_api: int = 1000):
        self.populacao = populacao
        self.teto_api = teto_api
        self.consultas: list[str] = []

    def get(self, path, params):
        assert path == "/search/repositories"
        q = params["q"]
        if params["page"] == 1:
            self.consultas.append(q)

        if m := re.fullmatch(r"stars:>(\d+)", q):
            lo, hi = int(m[1]) + 1, float("inf")
        else:
            m = re.fullmatch(r"stars:(\d+)\.\.(\d+)", q)
            lo, hi = int(m[1]), int(m[2])

        filtrados = sorted(
            (r for r in self.populacao if lo <= r["stargazers_count"] <= hi),
            key=lambda r: -r["stargazers_count"],
        )
        visiveis = filtrados[: self.teto_api]
        inicio = (params["page"] - 1) * params["per_page"]
        return {
            "total_count": len(filtrados),
            "incomplete_results": False,
            "items": visiveis[inicio : inicio + params["per_page"]],
        }


def populacao_decrescente(n: int, estrelas_max: int = 50_000) -> list[dict]:
    return [repo(f"r{i}", estrelas_max - i) for i in range(n)]


def sem_pausa(_segundos: float) -> None:
    pass


def test_montar_faixa_primeira_fatia_usa_maior_que():
    assert montar_faixa(1000, None) == "stars:>1000"


def test_montar_faixa_com_teto_usa_intervalo():
    assert montar_faixa(1000, 52310) == "stars:1001..52310"


def test_resumir_repositorio_mantem_campos_do_csv():
    resumo = resumir_repositorio(repo("x", 1500))
    assert list(resumo.keys()) == CANDIDATE_FIELDS
    assert resumo["owner"] == "org"
    assert resumo["full_name"] == "org/x"


def test_poucos_repositorios_cabem_em_uma_fatia():
    client = FakeSearchClient(populacao_decrescente(250))
    candidatos, fatias = buscar_candidatos(client, 1000, 2000, sleep=sem_pausa)

    assert len(candidatos) == 250
    assert client.consultas == ["stars:>1000"]
    assert fatias[0]["total_count"] == 250


def test_busca_fatia_quando_passa_do_teto_de_1000():
    client = FakeSearchClient(populacao_decrescente(2500))
    candidatos, fatias = buscar_candidatos(client, 1000, 2000, sleep=sem_pausa)

    assert len(candidatos) == 2000
    # 1a fatia: 50000..49001 (menor = 49001). A 2a comeca nesse limite e repete
    # o repo de 49001, entao traz 999 novos (1.999 no total) e e preciso uma 3a.
    assert client.consultas == ["stars:>1000", "stars:1001..49001", "stars:1001..48002"]
    # A 3a fatia so tem os 502 repos restantes da populacao (1 repetido).
    assert [f["novos"] for f in fatias] == [1000, 999, 501]


def test_candidatos_sem_repeticao_e_ordenados_por_estrelas():
    client = FakeSearchClient(populacao_decrescente(2500))
    candidatos, _ = buscar_candidatos(client, 1000, 2500, sleep=sem_pausa)

    nomes = [c["full_name"] for c in candidatos]
    estrelas = [c["stargazers_count"] for c in candidatos]
    assert len(nomes) == len(set(nomes)) == 2500
    assert estrelas == sorted(estrelas, reverse=True)


def test_empate_no_limite_da_fatia_nao_perde_repositorios():
    # 1.000 repos acima e 10 repos empatados no limite: a 1a fatia so ve parte deles.
    populacao = populacao_decrescente(995, estrelas_max=60_000)
    populacao += [repo(f"empate{i}", 30_000) for i in range(10)]
    client = FakeSearchClient(populacao)

    candidatos, _ = buscar_candidatos(client, 1000, 5000, sleep=sem_pausa)

    nomes = {c["full_name"] for c in candidatos}
    assert {f"org/empate{i}" for i in range(10)} <= nomes
    assert len(candidatos) == 1005


def test_fatia_inteira_com_mesmas_estrelas_nao_entra_em_loop():
    # Mais de 1.000 repos com exatamente 2.000 estrelas: impossivel ver todos,
    # mas a busca precisa descer de faixa em vez de repetir a consulta.
    populacao = [repo(f"igual{i}", 2000) for i in range(1200)]
    populacao += [repo(f"menor{i}", 1500 - i) for i in range(5)]
    client = FakeSearchClient(populacao)

    candidatos, _ = buscar_candidatos(client, 1000, 5000, sleep=sem_pausa)

    assert client.consultas == ["stars:>1000", "stars:1001..2000", "stars:1001..1999"]
    assert {f"org/menor{i}" for i in range(5)} <= {c["full_name"] for c in candidatos}


def test_pausa_entre_requisicoes_respeita_cota_da_busca():
    pausas: list[float] = []
    client = FakeSearchClient(populacao_decrescente(1500))
    buscar_candidatos(client, 1000, 1500, pausa=2.0, sleep=pausas.append)

    # 10 paginas na 1a fatia + 6 na 2a = 16 requisicoes -> 15 pausas
    assert pausas == [2.0] * 15


def test_salvar_csv_cria_pasta_e_escreve_cabecalho(tmp_path):
    destino = tmp_path / "dados" / "candidatos.csv"
    salvar_csv([resumir_repositorio(repo("x", 1500))], destino, CANDIDATE_FIELDS)

    with destino.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    assert linhas[0]["full_name"] == "org/x"
    assert linhas[0]["stargazers_count"] == "1500"
