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
from lab04.erro_tipo1 import construir_situacoes, grafico_erro_tipo1
from lab04.graficos import NOMES_TESTES, grafico_dados, grafico_estatistica_h0
from lab04.poder import FATORES_EFEITO, grafico_poder
from lab04.simulacao import ajustar_melhor_distribuicao
from lab04.testes import aplicar_mannwhitney, aplicar_welch

RAIZ = Path(__file__).parent.parent
PASTA_DASHBOARD = RAIZ / "dashboard"
ARQUIVO_DADOS = RAIZ / "dados" / "prs.csv"
PASTA_RESULTADOS = RAIZ / "resultados"

LINK_REPOSITORIO = "https://github.com/PedroL10/Laboratorios/tree/master/LAB04"
LINK_PROJECTS = "https://github.com/users/PedroL10/projects/6"
LINK_DASHBOARD = "https://pedrol10.github.io/Laboratorios/"

ESTILO = """
:root {
  --fundo: #f7f8fa; --cartao: #ffffff; --texto: #1d2330; --suave: #5b6475;
  --borda: #e2e5ea; --destaque: #1f4e8c;
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


def descrever_distribuicao(distribuicao, parametros: tuple) -> str:
    """Expõe os parâmetros do próprio gerador, com unidades e nomes legíveis."""
    origem, escala = parametros[-2:]
    if distribuicao.name == "norm":
        return f"Normal: média {numero(origem, 2)} h; desvio padrão {numero(escala, 2)} h"
    if distribuicao.name == "lognorm":
        return (
            f"Lognormal: σ do log {numero(parametros[0], 2)}; "
            f"escala (mediana com origem zero) {numero(escala, 2)} h; "
            f"origem {numero(origem, 0)} h"
        )
    nomes = {"gamma": "Gamma", "weibull_min": "Weibull"}
    nome = nomes.get(distribuicao.name, distribuicao.name)
    return (
        f"{nome}: forma {numero(parametros[0], 2)}; escala {numero(escala, 2)} h; "
        f"origem {numero(origem, 0)} h"
    )


def secao(identificador: str, titulo: str, conteudo: str) -> str:
    return f'<section id="{identificador}"><h2>{escape(titulo)}</h2>{conteudo}</section>'


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
    reais = carregar_reais()
    figura = grafico_dados(reais, {g: simulados[g].to_numpy() for g in simulados})
    linhas = ""
    for grupo, nome in (("sem_bot", "Sem bot (antes)"), ("com_bot", "Com bot (depois)")):
        _, distribuicao, parametros = ajustar_melhor_distribuicao(reais[grupo])
        descricao = descrever_distribuicao(distribuicao, parametros)
        linhas += f"<tr><th>{nome}</th><td>{escape(descricao)}</td><td>{len(reais[grupo])}</td></tr>"
    return f"""{figura_html(figura)}
<div class="texto">
<p>Os dados reais são assimétricos à direita: a maioria dos PRs é mergeada em poucos dias,
mas alguns levam semanas, e no grupo com bot a média ({numero(com["media_h"])} h) fica bem acima
da mediana ({numero(com["mediana_h"])} h). Há poucos outliers
({int(forma.loc["todos", "outliers_tukey"])} pelo critério de Tukey), porque a coleta só incluiu
PRs mergeados em até 30 dias. Os dados simulados vêm da distribuição de menor AIC em cada grupo
({melhor["sem_bot"].capitalize()} sem bot e {melhor["com_bot"].capitalize()} com bot) e reproduzem
essa assimetria; a normal foi o pior ajuste nos dois grupos.</p>
</div>
<h3>Gerador do G1 e do conjunto simulado de exemplo</h3>
<table>
<tr><th>Grupo</th><th>Distribuição e parâmetros ajustados aos dados reais</th><th>PRs simulados</th></tr>
{linhas}</table>
<p class="texto">Os parâmetros foram estimados por máxima verossimilhança e o menor AIC
selecionou a distribuição de cada grupo. Esses ajustes separados preservam a diferença
observada entre os períodos; para medir erro tipo I e poder, usamos o gerador comum descrito
na seção 4.</p>"""


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
<p>O t de Welch compara as médias dos dois grupos; o Mann-Whitney compara as posições dos 60
tempos ordenados, sem usar os valores em horas. Sob H₀, cada estatística segue a curva do
gráfico e, como o teste é bicaudal, a região de rejeição são as duas caudas que somam 5%
(|t| &gt; {numero(t_critico, 2)} e |z| &gt; {numero(z_critico, 2)}). No exemplo, que são os dados
reais, o t de Welch deu p = {numero(welch["p_valor"], 3)}, {decisao(welch)} da região de rejeição,
e o Mann-Whitney deu p = {numero(mann_whitney["p_valor"], 3)}, {decisao(mann_whitney)} dela. O
p-valor é a área hachurada: a chance de ver uma diferença pelo menos tão grande se H₀ fosse
verdadeira, e não a probabilidade de H₀ ser verdadeira.</p>
</div>
<h3>Os testes aplicados a um conjunto simulado</h3>
<p class="texto">Conjunto gerado a partir dos ajustes de cada grupo, que têm médias diferentes.
Por isso, aqui H₀ é falsa, e o esperado é que os testes a rejeitem.</p>
<table><tr><th>Teste</th><th>Estatística</th><th>p-valor</th><th>Interpretação</th></tr>{linhas}</table>"""


def inteiro(valor: int) -> str:
    """Formata um inteiro com ponto como separador de milhar."""
    return f"{valor:,}".replace(",", ".")


def porcentagem(valor: float, casas: int = 1) -> str:
    return numero(100 * valor, casas) + "%"


def metodo_simulacao() -> str:
    """Descreve o gerador comum das Q1–Q3 a partir da configuração usada nas simulações."""
    situacoes = construir_situacoes()
    linhas = "".join(
        f"<tr><th>{escape(situacao)}</th>"
        f"<td>{escape(descrever_distribuicao(config['distribuicao'], config['parametros']))}</td>"
        f"<td>{config['n']}</td></tr>"
        for situacao, config in situacoes.items()
    )
    fatores = "; ".join(numero(fator, 2) for fator in FATORES_EFEITO)
    forma = pd.read_csv(PASTA_RESULTADOS / "forma_distribuicao.csv").set_index("grupo")
    razao_medias = forma.loc["com_bot", "media_h"] / forma.loc["sem_bot", "media_h"]
    return f"""<h3>Como simulamos Q1, Q2 e Q3</h3>
<p class="texto">O ajuste da amostra real inteira fornece uma distribuição comum aos dois
grupos, para que a diferença de interesse seja controlada pela simulação. Em cada situação,
geramos duas amostras independentes dessa mesma distribuição: com fator 1, H₀ é verdadeira
(Q1); multiplicando os tempos do segundo grupo pelos fatores {fatores}, introduzimos efeitos
crescentes para medir o poder (Q2). Repetimos os dois procedimentos também com amostra pequena
e cauda pesada (Q3), com {inteiro(N_SIMULACOES)} repetições por situação e fator, semente
{SEMENTE} e α = {numero(ALFA, 2)}.</p>
<table>
<tr><th>Situação</th><th>Distribuição base dos dois grupos, antes do efeito</th><th>n por grupo</th></tr>
{linhas}</table>
<p class="texto">Escolhemos um efeito multiplicativo porque o desvio padrão cresce junto com
a média nos dados reais: os coeficientes de variação são
{numero(forma.loc['sem_bot', 'coef_variacao'], 2)} sem bot e
{numero(forma.loc['com_bot', 'coef_variacao'], 2)} com bot, com razão entre médias de
{numero(razao_medias, 2)}. O fator 1 significa efeito zero e o fator 2, tempo duas vezes maior;
a mudança de escala também altera a dispersão. Na amostra pequena, a aproximação do t de
Welch fica mais frágil; na lognormal, a assimetria e os outliers são deliberadamente mais
extremos que os reais, para testar a robustez dos dois testes.</p>"""


def secao_erro_tipo1() -> str:
    """Seção 4: G3 e se cada teste ficou perto de 5% em cada situação."""
    tabela = pd.read_csv(PASTA_RESULTADOS / "erro_tipo1.csv")
    taxa = tabela.set_index(["situacao", "teste"])["taxa_erro_tipo1"]
    real, pequena, pesada = tabela["situacao"].unique()
    margem = 1.96 * np.sqrt(ALFA * (1 - ALFA) / N_SIMULACOES)
    mann_whitney = taxa.xs("mann_whitney", level="teste")
    return f"""{metodo_simulacao()}
{figura_html(grafico_erro_tipo1(tabela))}
<div class="texto">
<p>Cada barra é o erro tipo I: a proporção de rejeições de H₀ em {inteiro(N_SIMULACOES)}
simulações em que H₀ era verdadeira, com a margem da simulação (±{numero(100 * margem, 1)} ponto
percentual) nas barras de erro. Com dados parecidos com os reais, os dois testes ficam perto de
5%, com o t de Welch um pouco conservador ({porcentagem(taxa[real, "welch"])} com 30 PRs por grupo
e {porcentagem(taxa[pequena, "welch"])} com 10). Com cauda pesada, o t de Welch cai para
{porcentagem(taxa[pesada, "welch"])}, porque os outliers inflam o desvio padrão e encolhem a
estatística t. O Mann-Whitney, que só usa a ordem dos valores, fica entre
{porcentagem(mann_whitney.min())} e {porcentagem(mann_whitney.max())} em todas as situações.</p>
</div>"""


def secao_poder() -> str:
    """Seção 5: G4 e qual teste detecta melhor o efeito em cada situação."""
    tabela = pd.read_csv(PASTA_RESULTADOS / "poder.csv")
    taxa = tabela.set_index(["situacao", "fator_efeito", "teste"])["taxa_rejeicao"]
    real, pequena, pesada = tabela["situacao"].unique()
    maior_fator = tabela["fator_efeito"].max()
    return f"""{figura_html(grafico_poder(tabela))}
<div class="texto">
<p>Cada curva mostra a proporção de rejeições de H₀ quando o tempo até o merge do grupo com
bot é multiplicado por um fator; no fator 1, sem efeito, é o erro tipo I. Com dados parecidos
com os reais, o t de Welch detecta mais em todos os fatores: quando o tempo dobra, ele rejeita H₀
em {porcentagem(taxa[real, 2.0, "welch"], 0)} das vezes, contra
{porcentagem(taxa[real, 2.0, "mann_whitney"], 0)} do Mann-Whitney. Com cauda pesada, a vantagem
muda de lado: no fator {numero(maior_fator, 1)}, o Mann-Whitney detecta
{porcentagem(taxa[pesada, maior_fator, "mann_whitney"], 0)} e o t de Welch só
{porcentagem(taxa[pesada, maior_fator, "welch"], 0)}. Com 10 PRs por grupo, os dois ficam
praticamente empatados e com pouco poder (no máximo {porcentagem(taxa[pequena].max(), 0)}).</p>
</div>"""


def secao_dados_reais() -> str:
    """Seção 6: estatística, p-valor, tamanho do efeito e conclusão de cada teste nos dados reais."""
    tabela = pd.read_csv(PASTA_RESULTADOS / "dados_reais.csv").set_index("teste")
    forma = pd.read_csv(PASTA_RESULTADOS / "forma_distribuicao.csv").set_index("grupo")
    welch, mann_whitney = tabela.loc["welch"], tabela.loc["mann_whitney"]

    def conclusao(linha) -> str:
        return "Rejeita H₀" if linha["rejeita_h0"] else "Não rejeita H₀"

    efeito_welch = (
        f"{welch['efeito']}: {numero(welch['valor_efeito'])} h (IC 95%: "
        f"{numero(welch['ic_inferior'])} a {numero(welch['ic_superior'])} h). "
        f"{welch['efeito_padronizado']} = {numero(welch['valor_padronizado'], 2)} ({welch['tamanho_efeito']})."
    )
    efeito_mann_whitney = (
        f"{mann_whitney['efeito']}: {porcentagem(mann_whitney['valor_efeito'], 0)}. "
        f"{mann_whitney['efeito_padronizado']} = {numero(mann_whitney['valor_padronizado'], 2)} "
        f"({mann_whitney['tamanho_efeito']})."
    )
    linhas = "".join(
        f"<tr><td>{NOMES_TESTES[teste]}</td><td>{estatistica}</td>"
        f"<td>{numero(linha['p_valor'], 3)}</td><td>{escape(efeito)}</td><td>{conclusao(linha)}</td></tr>"
        for teste, estatistica, linha, efeito in (
            ("welch", f"t = {numero(welch['estatistica'], 2)}", welch, efeito_welch),
            (
                "mann_whitney",
                f"U = {mann_whitney['estatistica']:.0f} pares em que o PR com bot demorou mais",
                mann_whitney,
                efeito_mann_whitney,
            ),
        )
    )
    diferenca_medianas = forma.loc["com_bot", "mediana_h"] - forma.loc["sem_bot", "mediana_h"]
    return f"""<table>
<tr><th>Teste</th><th>Estatística</th><th>p-valor</th><th>Tamanho do efeito</th><th>Conclusão (α = {numero(ALFA, 2)})</th></tr>
{linhas}</table>
<div class="texto">
<p>Nos dados reais, os testes discordam: o t de Welch rejeita H₀
(p = {numero(welch["p_valor"], 3)}) e o Mann-Whitney não (p = {numero(mann_whitney["p_valor"], 3)}),
mas os dois apontam na mesma direção: os PRs abertos depois do bot demoraram mais. A diferença
de {numero(welch["valor_efeito"])} h na média é pouco mais de um dia, mas o intervalo de confiança
vai de {numero(welch["ic_inferior"])} h a {numero(welch["ic_superior"])} h, então o efeito pode ser
desprezível ou grande. As medianas diferem só {numero(diferenca_medianas)} h, sinal de que parte
da diferença vem de poucos PRs muito demorados. Como a comparação é antes × depois, mesmo um
efeito real não prova que o bot foi a causa.</p>
</div>"""


def secao_conclusao() -> str:
    """Seção 7: expectativa × resultado e a recomendação de qual teste usar."""
    erro = pd.read_csv(PASTA_RESULTADOS / "erro_tipo1.csv").set_index(["situacao", "teste"])[
        "taxa_erro_tipo1"
    ]
    poder = pd.read_csv(PASTA_RESULTADOS / "poder.csv")
    taxa = poder.set_index(["situacao", "fator_efeito", "teste"])["taxa_rejeicao"]
    real, pequena, pesada = poder["situacao"].unique()
    maior_fator = poder["fator_efeito"].max()
    mann_whitney = erro.xs("mann_whitney", level="teste")
    linhas = [
        (
            "Erro tipo I",
            "Resultado já conhecido ao registrar a expectativa: os dois testes perto de 5%, "
            "com o t de Welch conservador na cauda pesada.",
            f"O t de Welch cai para {porcentagem(erro[pesada, 'welch'])} na cauda pesada; "
            f"o Mann-Whitney fica entre {porcentagem(mann_whitney.min())} e "
            f"{porcentagem(mann_whitney.max())} em todas as situações.",
        ),
        (
            "Poder com dados realistas",
            "O Mann-Whitney com mais poder, porque os dados são assimétricos.",
            f"Não confirmado. O t de Welch tem mais poder: quando o tempo dobra, rejeita H₀ em "
            f"{porcentagem(taxa[real, 2.0, 'welch'], 0)} das vezes, contra "
            f"{porcentagem(taxa[real, 2.0, 'mann_whitney'], 0)}.",
        ),
        (
            "Cauda pesada",
            "A maior vantagem do Mann-Whitney.",
            f"Confirmado. No fator {numero(maior_fator, 1)}, o Mann-Whitney detecta "
            f"{porcentagem(taxa[pesada, maior_fator, 'mann_whitney'], 0)} e o t de Welch, "
            f"{porcentagem(taxa[pesada, maior_fator, 'welch'], 0)}.",
        ),
        (
            "Amostra pequena (n = 10)",
            "Os dois perdem poder, e a diferença entre eles diminui.",
            f"Confirmado. Os dois empatam, com no máximo "
            f"{porcentagem(taxa[pequena].max(), 0)} de poder.",
        ),
    ]
    tabela = "".join(
        f"<tr><th>{escape(a)}</th><td>{escape(b)}</td><td>{escape(c)}</td></tr>" for a, b, c in linhas
    )
    return f"""<p class="texto">O registro disponível da expectativa foi commitado em
12/11/2026, depois dos resultados de erro tipo I e antes do código das simulações de poder.
Essa ordem não comprova a ausência de execuções locais anteriores; por isso, o registro não
é tratado como uma previsão anterior a todas as simulações. A linha de erro tipo I abaixo
resume um resultado que já era conhecido ao registrar a expectativa.</p>
<table>
<tr><th></th><th>Registro anterior ao commit do poder</th><th>O que encontramos</th></tr>
{tabela}</table>
<div class="texto">
<p>A expectativa sobre o poder errou porque os tempos reais seguem uma Gamma de forma perto de
1: a cauda é longa, mas não pesada. Nesse caso, a média resume bem uma mudança de escala, e o
Mann-Whitney perde informação ao usar só a ordem dos valores.</p>
<p><strong>Recomendação:</strong> usar o t de Welch neste cenário. Ele mantém o erro tipo I
abaixo de 5% e tem mais poder com dados como os do HPX, e o resultado nos dados reais é
consistente com isso: ele detectou a diferença, e o Mann-Whitney não. A escolha mudaria para o
Mann-Whitney se os tempos tivessem cauda muito pesada, por exemplo sem o limite de 30 dias da
coleta, quando PRs que levam meses dominariam a média, ou se a pergunta fosse sobre o PR típico,
e não sobre o tempo médio.</p>
<p><strong>Principal limitação:</strong> a comparação é antes × depois, em um único repositório,
com 30 PRs por grupo e vários do mesmo autor. O estudo indica qual teste usar, mas não prova
que o bot mudou o tempo até o merge.</p>
</div>"""


def montar_secoes() -> list[tuple[str, str, str]]:
    """Retorna as seções do dashboard na ordem do enunciado: (id, título, conteúdo HTML)."""
    return [
        ("cenario", "1. Cenário", secao_cenario()),
        ("dados", "2. Os dados", secao_dados()),
        ("testes", "3. Como os testes funcionam", secao_testes()),
        ("erro-tipo-1", "4. Erro tipo I", secao_erro_tipo1()),
        ("poder", "5. Poder", secao_poder()),
        ("dados-reais", "6. Dados reais", secao_dados_reais()),
        ("conclusao", "7. Conclusão", secao_conclusao()),
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
{inteiro(N_SIMULACOES)} simulações por configuração</footer>
</body>
</html>
"""


def gerar_dashboard() -> Path:
    """Gera dashboard/index.html e retorna o caminho do arquivo."""
    PASTA_DASHBOARD.mkdir(exist_ok=True)
    arquivo = PASTA_DASHBOARD / "index.html"
    arquivo.write_text(montar_pagina(montar_secoes()), encoding="utf-8")
    return arquivo
