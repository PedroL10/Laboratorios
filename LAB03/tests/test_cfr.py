"""Testes da heuristica de CFR variante (b). Os exemplos vem do enunciado (RQ 03)."""

from __future__ import annotations

from metricas.cfr import (
    avaliar_heuristica,
    cfr_repositorio,
    classificar_releases,
    eh_corretiva,
    eh_patch_only,
    tem_commit_com_palavra_chave,
)


def release(tag_name: str, tag_anterior: str | None, published_at: str, *mensagens: str) -> dict:
    return {
        "tag_name": tag_name,
        "tag_anterior": tag_anterior,
        "published_at": published_at,
        "mensagens_commits": list(mensagens),
    }


def test_eh_patch_only_detecta_mudanca_so_no_patch():
    assert eh_patch_only("2.3.0", "2.3.1") is True


def test_eh_patch_only_rejeita_mudanca_de_minor_ou_major():
    assert eh_patch_only("2.3.0", "2.4.0") is False
    assert eh_patch_only("2.3.0", "3.0.0") is False


def test_eh_patch_only_sem_release_anterior_e_falso():
    assert eh_patch_only(None, "2.3.1") is False


def test_eh_patch_only_com_tag_fora_do_semver_e_falso():
    assert eh_patch_only("release-antiga", "2.3.1") is False
    assert eh_patch_only("2.3.0", "v-sem-padrao") is False


def test_tem_commit_com_palavra_chave_e_case_insensitive():
    assert tem_commit_com_palavra_chave(["Fix: crash ao abrir arquivo"]) is True
    assert tem_commit_com_palavra_chave(["HOTFIX urgente"]) is True
    assert tem_commit_com_palavra_chave(["Revert \"feature X\""]) is True


def test_tem_commit_com_palavra_chave_sem_pista_e_falso():
    assert tem_commit_com_palavra_chave(["feat: nova tela de login"]) is False
    assert tem_commit_com_palavra_chave([]) is False


def test_exemplo_do_enunciado_v2_3_0_para_v2_3_1_e_corretiva():
    # v2.3.0 (10/05) e seguida por v2.3.1 (12/05), so muda o patch e contem
    # o commit "fix: crash ao abrir arquivo". Logo, v2.3.1 e corretiva.
    r = release("2.3.1", "2.3.0", "2024-05-12T00:00:00Z", "fix: crash ao abrir arquivo")
    assert eh_corretiva(r) is True


def test_exemplo_do_enunciado_v2_4_0_para_v2_5_0_nao_e_corretiva():
    # v2.4.0 (01/06) e seguida por v2.5.0 (20/06): muda o minor e nao tem
    # palavra-chave nas mensagens. Logo, v2.5.0 nao e corretiva.
    r = release("2.5.0", "2.4.0", "2024-06-20T00:00:00Z", "feat: nova exportacao")
    assert eh_corretiva(r) is False


def test_classificar_releases_adiciona_campo_corretiva_sem_alterar_entrada():
    releases = [release("2.3.1", "2.3.0", "2024-05-12T00:00:00Z", "fix: crash")]
    resultado = classificar_releases(releases)
    assert resultado[0]["corretiva"] is True
    assert "corretiva" not in releases[0]


def test_cfr_repositorio_exemplo_do_enunciado():
    # v2.3.0 falhou (seguida em <=7 dias por v2.3.1, que e corretiva).
    # v2.4.0 nao falhou (seguida por v2.5.0, que nao e corretiva).
    releases = [
        release("2.3.0", "2.2.0", "2024-05-10T00:00:00Z", "feat: tela nova"),
        release("2.3.1", "2.3.0", "2024-05-12T00:00:00Z", "fix: crash ao abrir arquivo"),
        release("2.4.0", "2.3.1", "2024-06-01T00:00:00Z", "feat: exportacao"),
        release("2.5.0", "2.4.0", "2024-06-20T00:00:00Z", "feat: nova exportacao"),
    ]

    resultado = cfr_repositorio(releases, fim_janela="2024-12-31T00:00:00Z")

    assert resultado["cfr_entrega"] == 0.25
    assert resultado["n_releases_avaliadas"] == 4
    assert resultado["n_releases_falhas"] == 1
    assert resultado["n_releases_censuradas"] == 0


def test_cfr_repositorio_release_seguida_apos_mais_de_7_dias_nao_falha():
    releases = [
        release("2.3.0", "2.2.0", "2024-05-10T00:00:00Z", "feat: tela nova"),
        release("2.3.1", "2.3.0", "2024-05-20T00:00:00Z", "fix: crash ao abrir arquivo"),
    ]

    resultado = cfr_repositorio(releases, fim_janela="2024-12-31T00:00:00Z")

    assert resultado["n_releases_falhas"] == 0


def test_cfr_repositorio_ultima_release_sem_proxima_nao_falha():
    releases = [release("1.0.0", None, "2024-01-01T00:00:00Z")]
    resultado = cfr_repositorio(releases, fim_janela="2024-12-31T00:00:00Z")
    assert resultado["n_releases_falhas"] == 0
    assert resultado["n_releases_avaliadas"] == 1


def test_cfr_repositorio_censura_releases_nos_ultimos_7_dias_da_janela():
    releases = [
        release("1.0.0", None, "2024-12-30T00:00:00Z"),
    ]
    resultado = cfr_repositorio(releases, fim_janela="2024-12-31T00:00:00Z")
    assert resultado["n_releases_censuradas"] == 1
    assert resultado["n_releases_avaliadas"] == 0
    assert resultado["cfr_entrega"] is None


def test_cfr_repositorio_sem_releases_devolve_none():
    resultado = cfr_repositorio([], fim_janela="2024-12-31T00:00:00Z")
    assert resultado == {
        "cfr_entrega": None,
        "n_releases_avaliadas": 0,
        "n_releases_falhas": 0,
        "n_releases_censuradas": 0,
    }


def test_avaliar_heuristica_exemplo_do_enunciado():
    # 40 marcadas como corretivas pela heuristica, 30 confirmadas pelo
    # consenso (precisao 75%); consenso tem 50 corretivas no total (recall 60%).
    rotulos_heuristica = [True] * 40 + [False] * 60
    rotulos_consenso = [True] * 30 + [False] * 10 + [True] * 20 + [False] * 40

    resultado = avaliar_heuristica(rotulos_heuristica, rotulos_consenso)

    assert resultado["precisao"] == 0.75
    assert resultado["recall"] == 0.6
    assert round(resultado["f1"], 2) == 0.67


def test_avaliar_heuristica_tamanhos_diferentes_leva_a_erro():
    import pytest

    with pytest.raises(ValueError):
        avaliar_heuristica([True], [True, False])


def test_avaliar_heuristica_sem_positivos_devolve_none():
    resultado = avaliar_heuristica([False, False], [False, False])
    assert resultado == {"precisao": None, "recall": None, "f1": None}
