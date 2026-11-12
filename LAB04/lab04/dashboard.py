"""Gera o dashboard do estudo como uma única página HTML: dashboard/index.html.

Cada seção segue a ordem pedida no enunciado. A biblioteca Plotly.js, usada pelos gráficos,
é carregada uma vez, por CDN.
"""

from html import escape
from pathlib import Path

import pandas as pd
from plotly.offline import get_plotlyjs_version

from lab04.config import ALFA, N_SIMULACOES, SEMENTE

RAIZ = Path(__file__).parent.parent
PASTA_DASHBOARD = RAIZ / "dashboard"
ARQUIVO_DADOS = RAIZ / "dados" / "prs.csv"

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
<p>O teste é bicaudal, com α = {ALFA}, porque o bot pode tanto acelerar quanto atrasar o
merge. Os dados reais são {len(dados)} PRs mergeados do repositório
<a href="https://github.com/TheHPXProject/hpx">TheHPXProject/hpx</a>, coletados pela API do
GitHub: {por_grupo.get("sem_bot", 0)} abertos antes da adoção do bot (março a maio de 2026) e
{por_grupo.get("com_bot", 0)} depois (julho a setembro de 2026).</p>
</div>"""


def montar_secoes() -> list[tuple[str, str, str]]:
    """Retorna as seções do dashboard na ordem do enunciado: (id, título, conteúdo HTML)."""
    return [
        ("cenario", "1. Cenário", secao_cenario()),
        ("dados", "2. Os dados", pendente("G1, dados reais ao lado dos simulados.")),
        ("testes", "3. Como os testes funcionam", pendente("G2, distribuição da estatística sob H₀.")),
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
