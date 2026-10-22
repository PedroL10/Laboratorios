"""Testes dos scripts de analise das RQ 05 e RQ 06 (com um dataset sintetico)."""

from __future__ import annotations

import csv

import pytest

from analise import rq05, rq06
from pipeline.dataset import COLUNAS
from tests.test_rq01_04 import dataset_sintetico


@pytest.fixture
def entrada(tmp_path):
    caminho = tmp_path / "amostra_metricas.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(dataset_sintetico(120, seed=3))
    return caminho


def test_rq05_grava_tabela_e_figura(entrada, tmp_path):
    saida = tmp_path / "rq05"
    resultado = rq05.gerar(entrada, saida)

    assert set(resultado) == {"a", "b"}
    assert resultado["a"]["n"] == 120
    assert -1 <= resultado["a"]["rho"] <= 1
    assert (saida / "figuras" / "dispersao.png").exists()
    tabela = (saida / "spearman.md").read_text(encoding="utf-8")
    assert "CFR (a) proxy de CI" in tabela and "CFR (b) proxy de entrega" in tabela


def test_rq05_main(entrada, tmp_path, capsys):
    rq05.main(["--entrada", str(entrada), "--saida", str(tmp_path / "out")])
    assert "CFR variante (a): rho=" in capsys.readouterr().out


def test_rq06_testa_4_fatores_x_4_metricas_com_holm(entrada, tmp_path):
    saida = tmp_path / "rq06"
    resultados = rq06.gerar(entrada, saida)

    assert len(resultados) == 16
    assert {r["fator"] for r in resultados} == {"linguagem", "popularidade", "contribuidores", "idade"}
    assert all("p_valor_corrigido" in r for r in resultados if r["p_valor"] is not None)
    for nome in ["testes.md", "testes.csv", "medianas.md", "figuras/efeitos.png"]:
        assert (saida / nome).exists(), nome


def test_rq06_junta_linguagens_raras_em_outras(entrada, monkeypatch):
    monkeypatch.setattr(rq06, "MIN_POR_LINGUAGEM", 20)
    repositorios = rq06.carregar_repositorios(str(entrada))
    grupos = rq06._grupos_do_fator(repositorios, "linguagem")
    # Python (~48) e TypeScript (~36) ficam; Go, Rust e "sem linguagem" (~12 cada) viram Outras.
    assert set(grupos) == {"Python", "TypeScript", "Outras"}
    for grupo in ("Python", "TypeScript"):
        assert grupos.count(grupo) >= 20


def test_rq06_inclui_tipo_do_projeto_quando_ha_rotulos(entrada, tmp_path):
    rotulos = tmp_path / "rotulos.csv"
    with rotulos.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["full_name", "tipo_projeto", "tag_name"])
        escritor.writeheader()
        for i in range(30):
            tipo = ["biblioteca/framework", "aplicacao/servico", "ferramenta CLI"][i % 3]
            escritor.writerow({"full_name": f"org/r{i}", "tipo_projeto": tipo, "tag_name": "v1"})
            escritor.writerow({"full_name": f"org/r{i}", "tipo_projeto": "", "tag_name": "v2"})

    resultados = rq06.gerar(entrada, tmp_path / "rq06", rotulos)

    tipo = [r for r in resultados if r["fator"] == "tipo_projeto"]
    assert len(tipo) == 4
    assert tipo[0]["teste"] == "kruskal-wallis"
    assert tipo[0]["n"] == 30


def test_rq06_main(entrada, tmp_path, capsys):
    rq06.main(["--entrada", str(entrada), "--saida", str(tmp_path / "out")])
    assert "linguagem x deployment_frequency" in capsys.readouterr().out
