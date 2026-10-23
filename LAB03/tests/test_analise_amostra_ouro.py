"""Testes da avaliacao da heuristica frente aos rotulos manuais."""

from __future__ import annotations

import csv
import json

import pytest

from analise.amostra_ouro import avaliar, consenso, fleiss_kappa_dimensao, intervalo_bootstrap, main, relatorio


def dado(repo, tag, anterior, mensagens):
    return {"full_name": repo, "tag_name": tag, "tag_anterior": anterior, "published_at": "2026-01-01T00:00:00Z",
            "link_release": "l", "notas": "", "mensagens_commits": mensagens, "compare_ok": True}


DADOS = [
    dado("org/a", "1.0.1", "1.0.0", ["docs: readme"]),  # heuristica: sim (patch)
    dado("org/a", "1.1.0", "1.0.1", ["feat: x"]),  # heuristica: nao
    dado("org/b", "2.1.0", "2.0.0", ["fix: crash"]),  # heuristica: sim (palavra)
    dado("org/b", "3.0.0", "2.1.0", ["feat: y"]),  # heuristica: nao
]


def rotulos(corretivas, tipo="biblioteca/framework"):
    return [
        {"full_name": d["full_name"], "tag_name": d["tag_name"], "corretiva": c, "tipo_projeto": tipo,
         "releases_representam_entrega_real": "sim"}
        for d, c in zip(DADOS, corretivas)
    ]


def test_consenso_por_maioria_e_empate():
    assert consenso(["sim", "sim", "nao"]) == "sim"
    assert consenso(["sim", "nao", "incerto"]) is None
    assert consenso(["sim"]) == "sim"
    assert consenso(["", ""]) is None


def test_um_avaliador_e_a_referencia():
    # Referencia: so 1.0.1 nao e corretiva de verdade (so docs); 2.1.0 e.
    r = avaliar(DADOS, {"pedro": rotulos(["nao", "nao", "sim", "nao"])})
    assert r["n_avaliadas"] == 4 and r["n_corretivas"] == 1
    assert r["confusao"] == {"vp": 1, "fp": 1, "fn": 0, "vn": 2}
    assert r["heuristica"]["precisao"] == 0.5 and r["heuristica"]["recall"] == 1.0
    assert r["so_patch"]["recall"] == 0.0 and r["so_palavra"]["f1"] == 1.0
    assert r["kappas"] is None
    assert "kappa de Fleiss) nao pode ser calculada" in relatorio(r)


def test_releases_sem_rotulo_ficam_fora():
    r = avaliar(DADOS, {"pedro": rotulos(["", "nao", "sim", "nao"])})
    assert r["n_avaliadas"] == 3 and r["n_sem_referencia"] == 1


def test_tres_avaliadores_usam_maioria_e_calculam_fleiss():
    r = avaliar(DADOS, {
        "a": rotulos(["sim", "nao", "sim", "nao"]),
        "b": rotulos(["sim", "nao", "sim", "nao"], tipo="ferramenta CLI"),
        "c": rotulos(["nao", "nao", "sim", "nao"]),
    })
    assert r["n_corretivas"] == 2
    assert r["heuristica"]["f1"] == 1.0
    assert set(r["kappas"]) == {"corretiva", "tipo_projeto", "entrega_real"}
    assert r["kappas"]["corretiva"] < 1
    assert r["kappas"]["entrega_real"] is None  # todos responderam "sim"
    assert "kappa de Fleiss" in relatorio(r)


def test_fleiss_com_itens_insuficientes_ou_uma_so_categoria():
    assert fleiss_kappa_dimensao([["sim", "sim", ""]]) is None
    assert fleiss_kappa_dimensao([["sim", "sim", "sim"], ["sim", "sim", "sim"]]) is None


def test_intervalo_bootstrap_contem_o_valor_observado():
    heuristica = [True, True, False, False, True, False] * 5
    referencia = [True, False, False, True, True, False] * 5
    ic = intervalo_bootstrap(heuristica, referencia)
    assert ic["precisao"][0] <= 2 / 3 <= ic["precisao"][1]


def test_main_grava_o_relatorio(tmp_path, capsys):
    caminho_dados = tmp_path / "dados.json"
    caminho_dados.write_text(json.dumps(DADOS), encoding="utf-8")
    caminho_rotulos = tmp_path / "amostra_ouro_pedro.csv"
    with caminho_rotulos.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(rotulos(["sim"] * 4)[0]))
        escritor.writeheader()
        escritor.writerows(rotulos(["nao", "nao", "sim", "nao"]))

    main(["--rotulos", str(caminho_rotulos), "--dados", str(caminho_dados), "--saida", str(tmp_path / "out")])

    assert "4 releases avaliadas" in capsys.readouterr().out
    texto = (tmp_path / "out" / "validacao.md").read_text(encoding="utf-8")
    assert "Avaliador(es): pedro" in texto
