"""Testes do dataset final e do dicionario de dados."""

from __future__ import annotations

import csv

import pytest

from pipeline import __main__ as principal
from pipeline.dataset import (
    COLUNAS,
    DICIONARIO,
    dicionario_markdown,
    gerar_dataset,
    main,
    montar_dataset,
)
from pipeline.selecao import salvar_csv

COLUNAS_AMOSTRA = [
    "full_name", "owner", "name", "stargazers_count", "language", "created_at",
    "default_branch", "archived", "fork", "html_url", "n_releases_janela", "n_runs_push",
    "n_runs_validos", "runs_no_teto", "n_contribuidores", "erro_contribuidores", "idade_dias",
]


def test_toda_coluna_gerada_pelo_pipeline_esta_no_dicionario():
    geradas = set(COLUNAS_AMOSTRA)
    for campos in (
        principal.FREQUENCIA_FIELDS,
        principal.LEAD_TIME_FIELDS,
        principal.CFR_FIELDS,
        principal.CFR_CI_FIELDS,
        principal.RECUPERACAO_FIELDS,
        principal.VARIANTES_FIELDS,
    ):
        geradas |= set(campos)
    assert geradas <= set(COLUNAS)


def test_colunas_do_dicionario_sao_unicas_e_completas():
    assert len(COLUNAS) == len(set(COLUNAS))
    for coluna, tipo, unidade, descricao in DICIONARIO:
        assert tipo and unidade and descricao, coluna


def test_colunas_usadas_pelas_analises_existem():
    # analise/rq05.py e analise/rq06.py leem estas colunas do dataset.
    for coluna in [
        "deployment_frequency", "cfr_ci", "cfr_entrega", "lead_time_release_dias",
        "tempo_recuperacao_horas", "language", "stargazers_count", "n_contribuidores", "idade_dias",
    ]:
        assert coluna in COLUNAS


def test_montar_dataset_junta_por_full_name_e_classifica_c1():
    amostra = [
        {"full_name": "org/a", "language": "Python", "n_releases_janela": "9"},
        {"full_name": "org/b", "language": "Go", "n_releases_janela": "6"},
    ]
    frequencia = [
        {"full_name": "org/b", "deployment_frequency": "0.1", "n_releases_janela": "5"},
        {"full_name": "org/a", "deployment_frequency": "8", "n_releases_janela": "417"},
    ]
    metricas = [
        {"full_name": "org/a", "lead_time_release_dias": "3", "cfr_ci": "0.2", "tempo_recuperacao_horas": "200"},
    ]

    dataset = montar_dataset(amostra, [frequencia, metricas])

    assert [linha["full_name"] for linha in dataset] == ["org/a", "org/b"]
    assert list(dataset[0]) == COLUNAS
    a, b = dataset
    # O arquivo de metricas prevalece sobre a coluna repetida da amostra.
    assert a["n_releases_janela"] == "417"
    assert a["language"] == "Python"
    # (Elite, High, High, Low) -> High
    assert a["categoria_geral"] == "High"
    assert a["n_metricas"] == 4
    # org/b so tem frequencia: o resto fica vazio e a categoria usa 1 metrica.
    assert b["cfr_ci"] == ""
    assert b["categoria_frequencia"] == "Low"
    assert b["categoria_cfr"] is None
    assert b["n_metricas"] == 1


def test_dicionario_markdown_tem_uma_linha_por_coluna():
    texto = dicionario_markdown()
    assert texto.count("\n| `") == len(DICIONARIO)
    assert "| `cfr_ci` | proporcao (0 a 1) |" in texto


@pytest.fixture
def pastas(tmp_path):
    dados, resultados = tmp_path / "dados", tmp_path / "resultados"
    dados.mkdir()
    resultados.mkdir()
    salvar_csv([{"full_name": "org/a", "language": "Python"}], resultados / "amostra.csv", ["full_name", "language"])
    salvar_csv(
        [{"full_name": "org/a", "deployment_frequency": 2.0}],
        dados / "frequencia.csv",
        ["full_name", "deployment_frequency"],
    )
    return tmp_path, dados, resultados


def test_gerar_dataset_grava_csv_e_dicionario_e_avisa_arquivos_faltando(pastas, capsys):
    _, dados, resultados = pastas
    dataset = gerar_dataset(dados, resultados)

    assert len(dataset) == 1
    with (resultados / "amostra_metricas.csv").open(encoding="utf-8") as f:
        linha = next(csv.DictReader(f))
    assert linha["deployment_frequency"] == "2.0"
    assert linha["categoria_frequencia"] == "High"
    assert linha["lead_time_release_dias"] == ""
    assert (resultados / "dicionario_dados.md").exists()
    assert "lead_time.csv nao existe" in capsys.readouterr().out


def test_comando_isolado_monta_o_dataset_sem_token(pastas, monkeypatch, capsys):
    raiz, _, _ = pastas
    (raiz / "config.yaml").write_text(
        f"dados_dir: {raiz / 'dados'}\nresultados_dir: {raiz / 'resultados'}\n", encoding="utf-8"
    )
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    assert main(["--config", str(raiz / "config.yaml")]) == 0
    assert "Dataset de 1 repositorios" in capsys.readouterr().out
