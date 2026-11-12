from scipy import stats

from lab04 import dashboard
from lab04.dashboard import gerar_dashboard, link_ou_aviso, montar_pagina, montar_secoes


def test_secoes_seguem_a_ordem_do_enunciado():
    titulos = [titulo for _, titulo, _ in montar_secoes()]
    assert titulos == [
        "1. Cenário",
        "2. Os dados",
        "3. Como os testes funcionam",
        "4. Erro tipo I",
        "5. Poder",
        "6. Dados reais",
        "7. Conclusão",
    ]


def test_cenario_informa_a_origem_e_o_numero_de_observacoes():
    _, _, cenario = montar_secoes()[0]
    assert "TheHPXProject/hpx" in cenario
    assert "60 PRs" in cenario
    assert "H₀" in cenario and "H₁" in cenario


def test_link_ou_aviso_mostra_link_ou_pendencia():
    assert link_ou_aviso("Repositório", "https://x.y") == '<a href="https://x.y">Repositório</a>'
    assert "a definir" in link_ou_aviso("GitHub Projects", "")


def test_pagina_tem_links_no_topo_antes_das_secoes():
    pagina = montar_pagina(montar_secoes())
    assert pagina.index("GitHub Projects") < pagina.index('<section id="cenario">')
    assert pagina.index("Repositório") < pagina.index('<section id="cenario">')


def test_gerar_dashboard_cria_o_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, "PASTA_DASHBOARD", tmp_path)
    arquivo = gerar_dashboard()
    assert arquivo.name == "index.html"
    assert arquivo.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_secoes_2_e_3_trazem_g1_g2_e_o_exemplo_simulado():
    secoes = {identificador: conteudo for identificador, _, conteudo in montar_secoes()}
    assert "G1" in secoes["dados"] and "Em construção" not in secoes["dados"]
    assert "G2" in secoes["testes"] and "Em construção" not in secoes["testes"]
    assert "conjunto simulado" in secoes["testes"]
    assert "não a probabilidade de H₀ ser verdadeira" in secoes["testes"]


def test_secoes_4_a_6_trazem_g3_g4_e_a_tabela_dos_dados_reais():
    secoes = {identificador: conteudo for identificador, _, conteudo in montar_secoes()}
    assert "G3" in secoes["erro-tipo-1"]
    assert "G4" in secoes["poder"]
    assert "Tamanho do efeito" in secoes["dados-reais"]
    for identificador in ("erro-tipo-1", "poder", "dados-reais"):
        assert "Em construção" not in secoes[identificador]


def test_conclusao_compara_expectativa_e_resultado_e_recomenda_um_teste():
    _, _, conclusao = montar_secoes()[-1]
    assert "Registro anterior ao commit do poder" in conclusao
    assert "depois dos resultados de erro tipo I" in conclusao
    assert "não comprova a ausência de execuções locais anteriores" in conclusao
    assert "Resultado já conhecido ao registrar a expectativa" in conclusao
    assert "Recomendação" in conclusao
    assert "Principal limitação" in conclusao


def test_dados_expoem_os_parametros_dos_ajustes_de_cada_grupo():
    dados = dashboard.secao_dados()
    assert "Weibull: forma 1,07; escala 41,35 h" in dados
    assert "Gamma: forma 1,25; escala 54,52 h" in dados
    assert "Gerador do G1 e do conjunto simulado de exemplo" in dados
    assert "gerador comum descrito" in dados


def test_metodo_acompanha_a_configuracao_dos_geradores_e_dos_efeitos(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "construir_situacoes",
        lambda: {
            "Cenário de verificação": {
                "distribuicao": stats.gamma,
                "parametros": (2, 0, 12),
                "n": 17,
            }
        },
    )
    monkeypatch.setattr(dashboard, "FATORES_EFEITO", (1, 1.1, 1.8))
    monkeypatch.setattr(dashboard, "N_SIMULACOES", 500)
    metodo = dashboard.metodo_simulacao()
    assert "Cenário de verificação" in metodo
    assert "Gamma: forma 2,00; escala 12,00 h" in metodo
    assert "<td>17</td>" in metodo
    assert "fatores 1,00; 1,10; 1,80" in metodo
    assert "500 repetições" in metodo
    assert "coeficientes de variação" in metodo
    assert "fator 1 significa efeito zero" in metodo


def test_nenhuma_secao_esta_em_construcao():
    for _, _, conteudo in montar_secoes():
        assert "Em construção" not in conteudo


def test_topo_tem_links_do_repositorio_do_projects_e_do_dashboard():
    pagina = montar_pagina(montar_secoes())
    assert "a definir" not in pagina
    assert "github.com/users/PedroL10/projects/6" in pagina
    assert "pedrol10.github.io/Laboratorios" in pagina
