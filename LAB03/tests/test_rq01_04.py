"""Testes do script de analise das RQ 01 a 04 (com um dataset sintetico)."""

from __future__ import annotations

import csv
import random

import pytest

from analise import rq01_04
from pipeline.dataset import COLUNAS, classificacao_c1


def dataset_sintetico(n: int = 40, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    linhas = []
    for i in range(n):
        linha = {coluna: "" for coluna in COLUNAS}
        linha.update(
            {
                "full_name": f"org/r{i}",
                "deployment_frequency": rng.lognormvariate(0, 1),
                "lead_time_release_dias": rng.lognormvariate(2.5, 1),
                "lead_time_commit_dias": rng.lognormvariate(1.5, 1),
                "cfr_ci": rng.uniform(0, 0.5),
                "cfr_entrega": rng.uniform(0, 0.3),
                "tempo_recuperacao_horas": "" if i % 10 == 0 else rng.lognormvariate(2, 1.5),
                "n_episodios": 5,
                "n_episodios_censurados": 1,
                "proporcao_censurados": 1 / 6,
                "n_releases_censuradas": 1,
                "n_ignoradas_compare_404": 1 if i == 0 else 0,
                "fatias_no_teto": 2 if i < 3 else 0,
            }
        )
        linha.update(classificacao_c1(linha))
        linhas.append(linha)
    return linhas


@pytest.fixture
def entrada(tmp_path):
    caminho = tmp_path / "amostra_metricas.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(dataset_sintetico())
    return caminho


def test_gerar_grava_tabelas_e_figuras(entrada, tmp_path):
    saida = tmp_path / "rq01_04"
    resultado = rq01_04.gerar(entrada, saida)

    for nome in ["descritiva.csv", "descritiva.md", "censura.md", "classificacao_c1.csv",
                 "classificacao_c1.md", "figuras/distribuicoes.png", "figuras/classificacao_c1.png"]:
        assert (saida / nome).exists(), nome

    por_coluna = {d["coluna"]: d for d in resultado["descritiva"]}
    assert por_coluna["deployment_frequency"]["n"] == 40
    assert por_coluna["tempo_recuperacao_horas"]["n"] == 36
    geral = resultado["classificacao"][-1]
    assert geral["metrica"] == "Geral (C1)"
    assert sum(geral[f"{c}_n"] for c in ["Elite", "High", "Medium", "Low"]) == 40


def test_censura_soma_os_indicadores(entrada):
    censura = dict(rq01_04.tabela_censura(rq01_04.carregar(entrada)))
    assert censura["Episodios censurados - sem recuperacao ate o fim da janela"] == "40"
    assert censura["Proporcao de episodios censurados (todos os repositorios)"] == "0,167"
    assert censura["Releases ignoradas no lead time - compare 404 (tag apagada ou reescrita)"] == "1"
    assert censura["Repositorios com algum dia acima de 1.000 runs (runs incompletos)"] == "3"
    assert censura["Repositorios sem tempo de recuperacao (nenhum episodio encerrado)"] == "4"


def test_figura_sem_dados_nao_quebra(tmp_path):
    vazio = [{coluna: "" for coluna in COLUNAS}]
    rq01_04.figura_distribuicoes(vazio, tmp_path / "f.png")
    assert (tmp_path / "f.png").exists()


def test_main_imprime_resumo(entrada, tmp_path, capsys):
    rq01_04.main(["--entrada", str(entrada), "--saida", str(tmp_path / "out")])
    assert "RQ 01 Deployment frequency: mediana=" in capsys.readouterr().out
