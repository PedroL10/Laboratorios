"""Testes dos scripts de analise das RQ 07 e RQ 08 (com um dataset sintetico)."""

from __future__ import annotations

import csv

import pytest

from analise import rq07, rq08
from pipeline.dataset import COLUNAS
from tests.test_rq01_04 import dataset_sintetico


@pytest.fixture
def entrada(tmp_path):
    caminho = tmp_path / "amostra_metricas.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(dataset_sintetico(80, seed=5))
    return caminho


def test_rq07_classifica_nas_3_combinacoes_e_compara_os_3_pares(entrada, tmp_path):
    saida = tmp_path / "rq07"
    resultado = rq07.gerar(entrada, saida)

    assert len(resultado["classificacoes"]) == 80
    assert {"categoria_geral_C1", "categoria_geral_C2", "categoria_geral_C3"} <= set(resultado["classificacoes"][0])
    # 3 pares x 4 dimensoes (geral, frequencia, lead time, CFR)
    assert len(resultado["concordancia"]) == 12
    geral = [c for c in resultado["concordancia"] if c["dimensao"] == "Geral"]
    assert [c["par"] for c in geral] == ["C1 x C2", "C1 x C3", "C2 x C3"]
    assert all(c["n"] == 80 for c in geral)
    for nome in ["classificacoes.csv", "distribuicao.md", "concordancia.md", "concordancia.csv",
                 "figuras/distribuicao.png", "figuras/transicoes.png"]:
        assert (saida / nome).exists(), nome


def test_rq07_main(entrada, tmp_path, capsys):
    rq07.main(["--entrada", str(entrada), "--saida", str(tmp_path / "out")])
    assert "C1 x C2:" in capsys.readouterr().out


def test_rq08_compara_rework_rate_e_cfr_entrega(entrada, tmp_path):
    resultado = rq08.gerar(entrada, tmp_path / "rq08")

    assert resultado["n_pares"] == 80
    assert resultado["rework"]["n"] == 80
    assert -1 <= resultado["rho"] <= 1
    assert "Rework rate" in (tmp_path / "rq08" / "rework.md").read_text(encoding="utf-8")


def test_rq08_sem_variacao_nao_calcula_correlacao():
    repositorios = [{"rework_rate": "0.1", "cfr_entrega": "0.2"}] * 3
    assert rq08.calcular_rq08(repositorios)["rho"] is None


def test_rq08_main(entrada, tmp_path, capsys):
    rq08.main(["--entrada", str(entrada), "--saida", str(tmp_path / "out")])
    assert "Rework rate: mediana=" in capsys.readouterr().out
