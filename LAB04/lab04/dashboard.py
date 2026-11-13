"""Gera o dashboard do estudo como uma única página HTML: dashboard/index.html.

Cada seção segue a ordem pedida no enunciado. A biblioteca Plotly.js, usada pelos gráficos,
é carregada uma vez, por CDN.
"""

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from plotly.offline import get_plotlyjs_version

from lab04.config import ALFA, N_SIMULACOES, SEMENTE
from lab04.graficos import NOMES_TESTES, grafico_dados, grafico_estatistica_h0
from lab04.testes import aplicar_mannwhitney, aplicar_welch

RAIZ = Path(__file__).parent.parent
PASTA_DASHBOARD = RAIZ / "dashboard"
ARQUIVO_DADOS = RAIZ / "dados" / "prs.csv"
PASTA_RESULTADOS = RAIZ / "resultados"

LINK_REPOSITORIO = "https://github.com/PedroL10/Laboratorios/tree/master/LAB04"
# Preencher com os links do quadro do GitHub Projects e do dashboard publicado.
LINK_PROJECTS = ""
LINK_DASHBOARD = ""

ESTILO = """
:root {
  --fundo: #f7f8fa; --cartao: #ffffff; --texto: #1d2330; --suave: #5b6475;
  --borda: #e2e5ea; --destaque: #1f4e8c; --aviso: #fff6e0;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--fundo); color: var(--texto);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
header { background: var(--destaque); color: #fff; padding: 28px 16px; }
header h1 { margin: 0 0 6px; font-size: 1.7rem; }
header p { margin: 0; opacity: 0.9; }
.links { margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px 20px; }
.links a { color: #fff; font-weight: 600; }
.links span { opacity: 0.75; }
nav { background: var(--cartao); border-bottom: 1px solid var(--borda); padding: 10px 16px;
  position: sticky; top: 0; z-index: 10; overflow-x: auto; white-space: nowrap; }
nav a { color: var(--destaque); text-decoration: none; margin-right: 18px; font-size: 0.95rem; }
main { max-width: 1040px; margin: 0 auto; padding: 24px 16px 48px; }
section { background: var(--cartao); border: 1px solid var(--borda); border-radius: 10px;
  padding: 20px 22px; margin-bottom: 22px; }
section h2 { margin-top: 0; color: var(--destaque); font-size: 1.3rem; }
section h3 { font-size: 1.05rem; margin: 24px 0 4px; }
.texto { max-width: 760px; }
.pendente { background: var(--aviso); border-radius: 6px; padding: 10px 14px; color: var(--suave); }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.95rem; }
th, td { border: 1px solid var(--borda); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: var(--fundo); }
footer { text-align: center; color: var(--suave); font-size: 0.85rem; padding-bottom: 24px; }
"""


def link_ou_aviso(rotulo: str, url: str) -> str:
    """Mostra o link, ou avisa que ele ainda não foi definido."""
    if url:
        return f'<a href="{escape(url)}">{escape(rotulo)}</a>'
    return f"<span>{escape(rotulo)}: a definir</span>"


def figura_html(figura: go.Figure) -> str:
    """Converte uma figura Plotly em um trecho HTML, sem repetir a biblioteca."""
    return figura.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


def numero(valor: float, casas: int = 1) -> str:
    """Formata um número com vírgula decimal."""
    return f"{valor:.{casas}f}".replace(".", ",")


def carregar_reais() -> dict[str, np.ndarray]:
    dados = pd.read_csv(ARQUIVO_DADOS)
    return {g: d["horas_ate_merge"].to_numpy() for g, d in dados.groupby("grupo")}


def secao(identificador: str, titulo: str, conteudo: str) -> str:
    return f'<section id="{identificador}"><h2>{escape(titulo)}</h2>{conteudo}</section>'


def pendente(o_que_falta: str) -> str:
    return f'<p class="pendente">Em construção: {escape(o_que_falta)}</p>'


def secao_cenario() -> str:
    """Seção 1: pergunta, hipóteses, origem dos dados reais e número de observações."""
    dados = pd.read_csv(ARQUIVO_DADOS)
    por_grupo = dados["grupo"].value_counts()
    return f"""
<div class="texto">
<p><strong>Pergunta:</strong> o tempo até o merge dos PRs do HPX mudou depois que o
projeto adotou o bot de revisão CodeRabbit?</p>
<table>
<tr><th></th><th>t de Welch</th><th>Mann-Whitney</th></tr>
<tr><th>H₀</th><td>As médias do tempo até o merge são iguais antes e depois do bot.</td>
<td>Um PR de um período tem a mesma chance de demorar mais ou menos que um PR do outro.</td></tr>
<tr><th>H₁</th><td>As médias são diferentes.</td>
<td>Os PRs de um período tendem a demorar mais que os do outro.</td></tr>
</table>
<p>O teste é bicaudal, com α = {numero(ALFA, 2)}, porque o bot pode tanto acelerar quanto atrasar o
merge. Os dados reais são {len(dados)} PRs mergeados do repositório
<a href="https://github.com/TheHPXProject/hpx">TheHPXProject/hpx</a>, coletados pela API do
GitHub: {por_grupo.get("sem_bot", 0)} abertos antes da adoção do bot (março a maio de 2026) e
{por_grupo.get("com_bot", 0)} depois (julho a setembro de 2026).</p>
</div>"""


def secao_dados() -> str:
    """Seção 2: G1 e a forma dos dados reais e simulados."""
    simulados = pd.read_csv(PASTA_RESULTADOS / "dados_simulados_exemplo.csv")
    forma = pd.read_csv(PASTA_RESULTADOS / "forma_distribuicao.csv").set_index("grupo")
    ajustes = pd.read_csv(PASTA_RESULTADOS / "ajustes_distribuicao.csv")
    melhor = ajustes.loc[ajustes.groupby("grupo")["aic"].idxmin()].set_index("grupo")["distribuicao"]
    com = forma.loc["com_bot"]
    figura = grafico_dados(carregar_reais(), {g: simulados[g].to_numpy() for g in simulados})
    return f"""{figura_html(figura)}
<div class="texto">
<p>Os dados reais são assimétricos à direita: a maioria dos PRs é mergeada em poucos dias,
mas alguns levam semanas. No grupo com bot, a média ({numero(com["media_h"])} h) fica bem acima
da mediana ({numero(com["mediana_h"])} h), sinal da cauda longa. Há poucos outliers
({int(forma.loc["todos", "outliers_tukey"])} pelo critério de Tukey), porque a coleta só
incluiu PRs mergeados em até 30 dias.</p>
<p>Os dados simulados vêm da distribuição de menor AIC em cada grupo
({melhor["sem_bot"].capitalize()} sem bot e {melhor["com_bot"].capitalize()} com bot) e
reproduzem essa assimetria. A normal foi o pior ajuste nos dois grupos, por isso não foi usada.</p>
</div>"""


def secao_testes() -> str:
    """Seção 3: G2 com os dados reais como exemplo e o teste aplicado a um conjunto simulado."""
    reais = carregar_reais()
    resultados = {
        "welch": aplicar_welch(reais["sem_bot"], reais["com_bot"]),
        "mann_whitney": aplicar_mannwhitney(reais["sem_bot"], reais["com_bot"]),
    }
    welch, mann_whitney = resultados["welch"], resultados["mann_whitney"]
    t_critico = stats.t(welch["graus_liberdade"]).ppf(1 - ALFA / 2)
    z_critico = stats.norm.ppf(1 - ALFA / 2)

    def decisao(resultado: dict) -> str:
        return "dentro" if resultado["p_valor"] < ALFA else "fora"

    exemplo = pd.read_csv(PASTA_RESULTADOS / "testes_exemplo.csv")
    linhas = "".join(
        f"<tr><td>{NOMES_TESTES[r.teste]}</td><td>{numero(r.estatistica, 2)}</td>"
        f"<td>{numero(r.p_valor, 4)}</td><td>{escape(r.interpretacao)}</td></tr>"
        for r in exemplo.itertuples()
    )
    return f"""{figura_html(grafico_estatistica_h0(resultados))}
<div class="texto">
<p>O t de Welch compara as médias dos dois grupos, sem supor variâncias iguais. O
Mann-Whitney compara as posições dos 60 tempos quando eles são ordenados, sem usar os valores
em horas. Sob H₀, a estatística de cada teste segue a curva do gráfico. Como o teste é
bicaudal, a região de rejeição são as duas caudas que somam 5%: |t| &gt; {numero(t_critico, 2)}
e |z| &gt; {numero(z_critico, 2)}.</p>
<p>O exemplo são os dados reais. O t de Welch deu t = {numero(welch["estatistica"], 2)} e
p = {numero(welch["p_valor"], 3)}, {decisao(welch)} da região de rejeição. O Mann-Whitney deu
z = {numero(mann_whitney["estatistica_padronizada"], 2)} e
p = {numero(mann_whitney["p_valor"], 3)}, {decisao(mann_whitney)} dela. O p-valor é a área das
duas caudas além do valor observado: a chance de ver uma diferença pelo menos tão grande se
H₀ fosse verdadeira. Ele não é a probabilidade de H₀ ser verdadeira.</p>
</div>
<h3>Os testes aplicados a um conjunto simulado</h3>
<p class="texto">Conjunto gerado a partir dos ajustes de cada grupo, que têm médias diferentes.
Por isso, aqui H₀ é falsa, e o esperado é que os testes a rejeitem.</p>
<table><tr><th>Teste</th><th>Estatística</th><th>p-valor</th><th>Interpretação</th></tr>{linhas}</table>"""


def montar_secoes() -> list[tuple[str, str, str]]:
    """Retorna as seções do dashboard na ordem do enunciado: (id, título, conteúdo HTML)."""
    return [
        ("cenario", "1. Cenário", secao_cenario()),
        ("dados", "2. Os dados", secao_dados()),
        ("testes", "3. Como os testes funcionam", secao_testes()),
        ("erro-tipo-1", "4. Erro tipo I", pendente("G3, erro tipo I em cada situação.")),
        ("poder", "5. Poder", pendente("G4, curvas de poder.")),
        ("dados-reais", "6. Dados reais", pendente("tabela com os testes aplicados aos dados reais.")),
        ("conclusao", "7. Conclusão", pendente("expectativa × resultado e recomendação.")),
    ]


def montar_pagina(secoes: list[tuple[str, str, str]]) -> str:
    """Monta o HTML completo da página."""
    menu = "".join(f'<a href="#{i}">{escape(t)}</a>' for i, t, _ in secoes)
    corpo = "".join(secao(i, t, c) for i, t, c in secoes)
    links = "".join(
        [
            link_ou_aviso("Repositório", LINK_REPOSITORIO),
            link_ou_aviso("GitHub Projects", LINK_PROJECTS),
            link_ou_aviso("Dashboard publicado", LINK_DASHBOARD),
        ]
    )
    simulacoes = f"{N_SIMULACOES:,}".replace(",", ".")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LAB04 Testes de Hipótese</title>
<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>
<style>{ESTILO}</style>
</head>
<body>
<header>
<h1>Testes de hipótese por dentro: t de Welch × Mann-Whitney</h1>
<p>Tempo até o merge de PRs, antes e depois de um bot de revisão.</p>
<div class="links">{links}</div>
</header>
<nav>{menu}</nav>
<main>{corpo}</main>
<footer>Gerado por <code>python -m lab04</code> · semente {SEMENTE} ·
{simulacoes} simulações por configuração</footer>
</body>
</html>
"""


def gerar_dashboard() -> Path:
    """Gera dashboard/index.html e retorna o caminho do arquivo."""
    PASTA_DASHBOARD.mkdir(exist_ok=True)
    arquivo = PASTA_DASHBOARD / "index.html"
    arquivo.write_text(montar_pagina(montar_secoes()), encoding="utf-8")
    return arquivo
