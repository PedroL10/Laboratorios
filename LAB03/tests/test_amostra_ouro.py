"""Testes da montagem da planilha da amostra-ouro (secao 6 do enunciado)."""

from __future__ import annotations

from pipeline.amostra_ouro import (
    CAMPOS_PLANILHA,
    gerar_linhas_planilha,
    sortear_amostra_ouro,
    sortear_releases,
)


def repo(full_name: str) -> dict:
    return {"full_name": full_name}


def release(tag_name: str) -> dict:
    return {"tag_name": tag_name}


def test_sortear_amostra_ouro_e_reproduzivel_com_mesma_semente():
    amostra = [repo(f"org/repo{i}") for i in range(200)]
    assert sortear_amostra_ouro(amostra, n=60, seed=42) == sortear_amostra_ouro(
        amostra, n=60, seed=42
    )


def test_sortear_amostra_ouro_devolve_n_repositorios():
    amostra = [repo(f"org/repo{i}") for i in range(200)]
    assert len(sortear_amostra_ouro(amostra, n=60, seed=42)) == 60


def test_sortear_amostra_ouro_com_amostra_menor_que_n_devolve_tudo():
    amostra = [repo("org/a"), repo("org/b")]
    resultado = sortear_amostra_ouro(amostra, n=60, seed=42)
    assert len(resultado) == 2


def test_sortear_releases_e_reproduzivel_por_repositorio():
    releases = [release(f"v{i}") for i in range(20)]
    a = sortear_releases(releases, "org/a", n=5, seed=42)
    b = sortear_releases(releases, "org/a", n=5, seed=42)
    assert a == b


def test_sortear_releases_difere_entre_repositorios():
    releases = [release(f"v{i}") for i in range(20)]
    a = sortear_releases(releases, "org/a", n=5, seed=42)
    b = sortear_releases(releases, "org/b", n=5, seed=42)
    assert a != b


def test_gerar_linhas_planilha_monta_uma_linha_por_release_sorteada():
    amostra_ouro = [repo("org/a")]
    releases_por_repo = {"org/a": [release(f"v{i}") for i in range(10)]}

    linhas = gerar_linhas_planilha(amostra_ouro, releases_por_repo, n_releases_por_repo=5, seed=42)

    assert len(linhas) == 5
    assert set(linhas[0].keys()) == set(CAMPOS_PLANILHA)
    assert linhas[0]["full_name"] == "org/a"
    assert linhas[0]["link_repositorio"] == "https://github.com/org/a"
    assert linhas[0]["link_release"].startswith("https://github.com/org/a/releases/tag/")
    # colunas de julgamento ficam vazias: preenchimento e manual e independente.
    assert linhas[0]["tipo_projeto"] == ""
    assert linhas[0]["releases_representam_entrega_real"] == ""
    assert linhas[0]["corretiva"] == ""


def test_gerar_linhas_planilha_repositorio_sem_releases_gera_uma_linha_vazia():
    amostra_ouro = [repo("org/sem-releases")]
    linhas = gerar_linhas_planilha(amostra_ouro, {}, n_releases_por_repo=5, seed=42)
    assert len(linhas) == 1
    assert linhas[0]["tag_name"] == ""
    assert linhas[0]["link_release"] == ""


# --- pagina de rotulagem -----------------------------------------------------

import json

import pytest
import requests

from pipeline.amostra_ouro import (
    coletar_dados_release,
    dados_para_pagina,
    gerar_pagina,
    main,
    release_anterior,
)


def erro_http(status: int) -> requests.HTTPError:
    resposta = requests.Response()
    resposta.status_code = status
    return requests.HTTPError(f"HTTP {status}", response=resposta)


class ClienteRotulagem:
    def __init__(self, notas=None, commits=None):
        self.notas, self.commits = notas, commits

    def get(self, path, params=None):
        if "/releases/tags/" in path:
            if isinstance(self.notas, Exception):
                raise self.notas
            return {"body": self.notas}
        if isinstance(self.commits, Exception):
            raise self.commits
        return {"commits": [{"commit": {"message": m, "author": {"date": "d"}}} for m in self.commits]}


def test_release_anterior_no_historico():
    historico = [release("v1"), release("v2"), release("v3")]
    assert release_anterior(historico, "v2") == "v1"
    assert release_anterior(historico, "v1") is None


def test_coletar_dados_release_traz_notas_e_mensagens():
    rel = {"tag_name": "v2", "published_at": "2026-01-01T00:00:00Z"}
    dados = coletar_dados_release(ClienteRotulagem("Corrige X", ["fix: x\n\ncorpo"]), "org/a", rel, "v1")
    assert dados["notas"] == "Corrige X"
    assert dados["mensagens_commits"] == ["fix: x"]  # so o titulo
    assert dados["link_release"] == "https://github.com/org/a/releases/tag/v2"
    assert dados["compare_ok"] is True


def test_coletar_dados_release_tolera_404_e_release_sem_anterior():
    rel = {"tag_name": "v1", "published_at": "2026-01-01T00:00:00Z"}
    dados = coletar_dados_release(ClienteRotulagem(erro_http(404), erro_http(404)), "org/a", rel, "v0")
    assert dados["notas"] == "" and dados["compare_ok"] is False
    sem_anterior = coletar_dados_release(ClienteRotulagem(None, []), "org/a", rel, None)
    assert sem_anterior["compare_ok"] is False and sem_anterior["mensagens_commits"] == []


def test_coletar_dados_release_propaga_outros_erros():
    rel = {"tag_name": "v1", "published_at": "2026-01-01T00:00:00Z"}
    with pytest.raises(requests.HTTPError):
        coletar_dados_release(ClienteRotulagem(erro_http(500), []), "org/a", rel, "v0")
    with pytest.raises(requests.HTTPError):
        coletar_dados_release(ClienteRotulagem("", erro_http(500)), "org/a", rel, "v0")


def dado(tag="v2", notas="notas", mensagens=("fix: a\n\ncorpo",)):
    return {"full_name": "org/a", "tag_name": tag, "tag_anterior": "v1", "published_at": "2026-01-01T00:00:00Z",
            "link_release": "l", "notas": notas, "mensagens_commits": list(mensagens), "compare_ok": True}


def test_pagina_mostra_so_a_primeira_linha_dos_commits_e_corta_notas_longas(monkeypatch):
    import pipeline.amostra_ouro as mod

    monkeypatch.setattr(mod, "MAX_COMMITS_NA_PAGINA", 2)
    monkeypatch.setattr(mod, "MAX_CARACTERES_NOTAS", 5)
    resumo = dados_para_pagina([dado(notas="123456789", mensagens=["a\nb", "c", "d"])])[0]
    assert resumo["commits"] == ["a", "c"]
    assert resumo["n_commits"] == 3
    assert resumo["notas"] == "12345" and resumo["notas_cortadas"] is True
    assert "corretiva" not in resumo  # a pagina nao recebe a saida da heuristica


def test_gerar_pagina_embute_os_dados_sem_quebrar_o_script():
    pagina = gerar_pagina([dado(notas="fecha </script><b>x</b>")], "pedro")
    assert "__DADOS__" not in pagina and "__AVALIADOR__" not in pagina
    assert "</script><b>" not in pagina
    bloco = pagina.split('<script id="dados" type="application/json">')[1].split("</script>")[0]
    assert json.loads(bloco)[0]["notas"] == "fecha </script><b>x</b>"


def test_main_reaproveita_dados_existentes_sem_chamar_a_api(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    (tmp_path / "config.yaml").write_text(
        'janela: {inicio: "2026-01-01", fim: "2026-12-31"}\n', encoding="utf-8")
    saida = tmp_path / "ouro"
    saida.mkdir()
    (saida / "dados_rotulagem.json").write_text(json.dumps([dado()]), encoding="utf-8")

    assert main(["--config", str(tmp_path / "config.yaml"), "--saida", str(saida), "--avaliador", "pedro"]) == 0
    assert "Rotulagem da amostra-ouro — pedro" in (saida / "pagina_rotulagem.html").read_text(encoding="utf-8")
