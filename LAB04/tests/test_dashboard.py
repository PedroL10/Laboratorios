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


def test_gerar_dashboard_cria_o_arquivo():
    arquivo = gerar_dashboard()
    assert arquivo.name == "index.html"
    assert arquivo.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_secoes_2_e_3_trazem_g1_g2_e_o_exemplo_simulado():
    secoes = {identificador: conteudo for identificador, _, conteudo in montar_secoes()}
    assert "G1" in secoes["dados"] and "Em construção" not in secoes["dados"]
    assert "G2" in secoes["testes"] and "Em construção" not in secoes["testes"]
    assert "conjunto simulado" in secoes["testes"]
    assert "não é a probabilidade de H₀ ser verdadeira" in secoes["testes"]
