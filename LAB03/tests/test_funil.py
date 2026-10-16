"""Testes do funil de selecao. Os dados de entrada imitam os CSVs das etapas anteriores."""

from __future__ import annotations

from pipeline.funil import (
    MOTIVO_NAO_AVALIADO,
    descrever_motivo,
    funil_markdown,
    funil_para_csv,
    montar_amostra,
    montar_funil,
    salvar_markdown,
)


def candidato(nome: str, estrelas: int = 5000) -> dict:
    return {"full_name": f"org/{nome}", "stargazers_count": str(estrelas), "language": "Go"}


def filtro(nome: str, usa: bool, motivo: str = "") -> dict:
    return {"full_name": f"org/{nome}", "usa_actions": str(usa), "motivo_descarte": motivo}


def criterio(nome: str, releases, runs_push=None, runs_validos=None, motivo="") -> dict:
    """Linha do criterio como vem do CSV (valores em texto, vazio = nao contado)."""
    return {
        "full_name": f"org/{nome}",
        "n_releases_janela": "" if releases is None else str(releases),
        "n_runs_push": "" if runs_push is None else str(runs_push),
        "n_runs_validos": "" if runs_validos is None else str(runs_validos),
        "runs_no_teto": "False",
        "incluido": str(not motivo),
        "motivo_descarte": motivo,
    }


def cenario():
    """10 candidatos -> 7 com Actions -> 5 avaliados -> 3 com releases -> 2 na amostra."""
    candidatos = [candidato(n) for n in "abcdefghij"]
    filtro_actions = [filtro(n, True) for n in "abcdefg"]
    filtro_actions += [filtro("h", False, "sem_workflows"), filtro("i", False, "sem_workflows")]
    filtro_actions += [filtro("j", False, "erro_http_404")]
    avaliados = [
        criterio("a", 10, 300, 280),
        criterio("b", 2, motivo="menos_de_5_releases"),
        criterio("c", 8, 60, 40, motivo="menos_de_50_runs_validos"),
        criterio("d", None, motivo="erro_http_404"),
        criterio("e", 6, 90, 90),
    ]
    return candidatos, filtro_actions, avaliados


def test_contagens_de_cada_etapa():
    funil = montar_funil(*cenario(), 1000, 5, 50)

    assert [e["repositorios"] for e in funil] == [10, 7, 5, 3, 2]
    assert [e["descartados"] for e in funil] == [0, 3, 2, 2, 1]


def test_motivos_de_descarte_por_etapa():
    funil = montar_funil(*cenario(), 1000, 5, 50)

    assert funil[0]["motivos_descarte"] == {}
    assert funil[1]["motivos_descarte"] == {"erro_http_404": 1, "sem_workflows": 2}
    assert funil[2]["motivos_descarte"] == {MOTIVO_NAO_AVALIADO: 2}
    # erro ao listar releases conta na etapa de releases
    assert funil[3]["motivos_descarte"] == {"erro_http_404": 1, "menos_de_5_releases": 1}
    assert funil[4]["motivos_descarte"] == {"menos_de_50_runs_validos": 1}


def test_descartados_batem_com_a_soma_dos_motivos():
    for etapa in montar_funil(*cenario(), 1000, 5, 50):
        assert etapa["descartados"] == sum(etapa["motivos_descarte"].values())


def test_descricoes_usam_os_parametros():
    funil = montar_funil(*cenario(), 2000, 3, 80)
    assert "stars:>2000" in funil[0]["descricao"]
    assert ">= 3 releases" in funil[3]["descricao"]
    assert ">= 80 runs validos" in funil[4]["descricao"]


def test_todos_avaliados_nao_gera_motivo_de_nao_avaliado():
    candidatos = [candidato("a")]
    funil = montar_funil(candidatos, [filtro("a", True)], [criterio("a", 9, 70, 70)], 1000, 5, 50)
    assert funil[2]["descartados"] == 0
    assert funil[2]["motivos_descarte"] == {}


def test_funil_para_csv_converte_motivos_em_texto():
    linhas = funil_para_csv(montar_funil(*cenario(), 1000, 5, 50))
    assert linhas[1]["motivos_descarte"] == "erro_http_404: 1; sem_workflows: 2"
    assert linhas[0]["motivos_descarte"] == ""


def test_amostra_junta_metadados_e_contagens_dos_incluidos():
    candidatos, _, avaliados = cenario()
    amostra = montar_amostra(candidatos, avaliados)

    assert [r["full_name"] for r in amostra] == ["org/a", "org/e"]
    assert amostra[0]["language"] == "Go"
    assert amostra[0]["n_releases_janela"] == "10"
    assert amostra[0]["n_runs_validos"] == "280"
    assert "motivo_descarte" not in amostra[0]


def test_descrever_motivo():
    assert descrever_motivo("sem_workflows") == "sem workflows do GitHub Actions"
    assert descrever_motivo("menos_de_5_releases") == "menos de 5 releases na janela"
    assert descrever_motivo("menos_de_50_runs_validos") == "menos de 50 runs validos na janela"
    assert descrever_motivo("erro_http_504") == "erro HTTP 504"
    assert descrever_motivo(MOTIVO_NAO_AVALIADO) == "nao avaliados (amostra ja completa)"
    assert descrever_motivo("outro") == "outro"


def test_markdown_tem_uma_linha_por_etapa_e_resumo(tmp_path):
    texto = funil_markdown(montar_funil(*cenario(), 1000, 5, 50), "2025-10-01..2026-09-30")

    assert "Janela de observacao: 2025-10-01..2026-09-30" in texto
    assert texto.count("\n| ") == 7  # cabecalho + separador + 5 etapas
    assert "| 2 | Usam GitHub Actions | 7 | 3 | erro HTTP 404: 1; sem workflows do GitHub Actions: 2 |" in texto
    assert "| 1 | Candidatos" in texto and "| 10 | - | - |" in texto
    assert "Resumo: 10 -> 7 -> 5 -> 3 -> 2" in texto

    destino = salvar_markdown(texto, tmp_path / "res" / "funil.md")
    assert destino.read_text(encoding="utf-8") == texto
