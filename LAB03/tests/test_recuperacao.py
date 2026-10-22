"""Testes do tempo de recuperacao (RQ 04)."""

from __future__ import annotations

import pytest

from metricas.recuperacao import episodios_do_workflow, recuperacao_repositorio


def run(conclusion, inicio, fim=None, workflow_id=1) -> dict:
    """Run do dia 2024-03-01 com inicio/fim no formato HH:MM."""
    return {
        "workflow_id": workflow_id,
        "conclusion": conclusion,
        "created_at": f"2024-03-01T{inicio}:00Z",
        "run_started_at": f"2024-03-01T{inicio}:00Z",
        "updated_at": f"2024-03-01T{fim or inicio}:00Z",
    }


def test_exemplo_do_enunciado_um_episodio_de_1h20():
    runs = [
        run("success", "09:00", "09:05"),
        run("failure", "10:00", "10:05"),
        run("failure", "10:30", "10:35"),
        run("success", "11:15", "11:20"),
    ]
    resultado = recuperacao_repositorio(runs)
    assert resultado["tempo_recuperacao_horas"] == pytest.approx(1 + 20 / 60)
    assert resultado["n_episodios"] == 1
    assert resultado["n_episodios_censurados"] == 0


def test_runs_fora_de_ordem_sao_ordenados_pelo_inicio():
    runs = [
        run("success", "11:15", "11:20"),
        run("failure", "10:00", "10:05"),
        run("success", "09:00", "09:05"),
    ]
    assert episodios_do_workflow(runs)["duracoes_horas"] == [pytest.approx(1 + 20 / 60)]


def test_falha_nunca_recuperada_e_censurada():
    runs = [run("success", "09:00"), run("failure", "10:00"), run("failure", "11:00")]
    resultado = recuperacao_repositorio(runs)
    assert resultado["tempo_recuperacao_horas"] is None
    assert resultado["n_episodios"] == 0
    assert resultado["n_episodios_censurados"] == 1
    assert resultado["proporcao_censurados"] == 1.0


def test_cancelled_nao_abre_nem_fecha_episodio():
    runs = [
        run("success", "09:00"),
        run("cancelled", "09:30"),
        run("failure", "10:00"),
        run("cancelled", "10:30"),
        run(None, "10:45"),  # em andamento
        run("success", "11:00", "11:30"),
    ]
    assert episodios_do_workflow(runs)["duracoes_horas"] == [pytest.approx(1.5)]


def test_timed_out_e_startup_failure_contam_como_falha():
    runs = [
        run("success", "09:00"),
        run("timed_out", "10:00"),
        run("success", "11:00"),
        run("startup_failure", "12:00"),
        run("success", "13:00", "13:30"),
    ]
    assert episodios_do_workflow(runs)["duracoes_horas"] == [1.0, pytest.approx(1.5)]


def test_workflow_que_comeca_a_janela_falhando_nao_tem_inicio_observado():
    runs = [run("failure", "09:00"), run("failure", "09:30"), run("success", "10:00")]
    resultado = recuperacao_repositorio(runs)
    assert resultado["n_episodios"] == 0
    assert resultado["n_episodios_sem_inicio"] == 1
    assert resultado["proporcao_censurados"] is None


def test_episodios_sao_calculados_dentro_de_cada_workflow():
    # O sucesso do workflow 2 nao encerra a falha do workflow 1.
    runs = [
        run("success", "09:00", workflow_id=1),
        run("failure", "10:00", workflow_id=1),
        run("success", "10:30", workflow_id=2),
        run("success", "12:00", "12:00", workflow_id=1),
        run("success", "08:00", workflow_id=2),
        run("failure", "13:00", workflow_id=2),
    ]
    resultado = recuperacao_repositorio(runs)
    assert resultado["tempo_recuperacao_horas"] == 2.0
    assert resultado["n_episodios"] == 1
    assert resultado["n_episodios_censurados"] == 1
    assert resultado["proporcao_censurados"] == 0.5


def test_mediana_de_todos_os_episodios_do_repositorio():
    runs = [
        run("success", "01:00"),
        run("failure", "02:00"),
        run("success", "03:00"),  # 1 h
        run("failure", "04:00"),
        run("success", "07:00"),  # 3 h
        run("success", "00:00", workflow_id=2),
        run("failure", "08:00", workflow_id=2),
        run("success", "18:00", workflow_id=2),  # 10 h
    ]
    assert recuperacao_repositorio(runs)["tempo_recuperacao_horas"] == 3.0


def test_sem_run_started_at_usa_created_at():
    runs = [
        {"workflow_id": 1, "conclusion": "success", "created_at": "2024-03-01T09:00:00Z",
         "run_started_at": None, "updated_at": "2024-03-01T09:00:00Z"},
        {"workflow_id": 1, "conclusion": "failure", "created_at": "2024-03-01T10:00:00Z",
         "run_started_at": None, "updated_at": "2024-03-01T10:00:00Z"},
        {"workflow_id": 1, "conclusion": "success", "created_at": "2024-03-01T11:00:00Z",
         "run_started_at": None, "updated_at": "2024-03-01T12:00:00Z"},
    ]
    assert recuperacao_repositorio(runs)["tempo_recuperacao_horas"] == 2.0


def test_repositorio_sem_runs():
    assert recuperacao_repositorio([]) == {
        "tempo_recuperacao_horas": None,
        "n_episodios": 0,
        "n_episodios_censurados": 0,
        "proporcao_censurados": None,
        "n_episodios_sem_inicio": 0,
    }
