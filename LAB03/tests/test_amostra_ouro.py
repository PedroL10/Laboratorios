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
