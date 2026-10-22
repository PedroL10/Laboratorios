"""Comparacao das metricas DORA entre subgrupos de repositorios (RQ 06).

RQ 06 pergunta quais caracteristicas dos repositorios estao associadas a um
melhor desempenho DORA. O fluxo e:

1. Separar os repositorios em grupos por um fator (ex.: quartis de estrelas,
   linguagem, tipo do projeto) com `quartis` + `agrupar_por_grupo`.
2. Comparar a distribuicao de uma metrica DORA entre esses grupos com
   `comparar_grupos` - Mann-Whitney se forem 2 grupos, Kruskal-Wallis se
   forem 3 ou mais - e seu tamanho de efeito (Cliff's delta ou epsilon ao
   quadrado).
3. Corrigir os p-valores de todas as combinacoes fator x metrica para
   comparacoes multiplas com `corrigir_holm`, porque testar muitos fatores e
   metricas ao nivel de 5% torna provavel algum "significativo" por acaso.
"""

from __future__ import annotations

from scipy.stats import kruskal, mannwhitneyu


def quartis(valores: list[float]) -> list[int]:
    """Converte uma lista de valores numericos em grupos 1 a 4 pelos quartis.

    Usa os mesmos indices de `valores` na saida: `quartis(valores)[i]` e o
    grupo do repositorio cujo valor esta em `valores[i]`. Empates na fronteira
    de um quartil ficam no grupo mais baixo (quartil calculado pela posicao
    ordenada, nao pelo valor).
    """
    ordenados = sorted(range(len(valores)), key=lambda i: valores[i])
    n = len(valores)
    grupos = [0] * n
    for posicao, indice in enumerate(ordenados):
        quartil = min(4, posicao * 4 // n + 1)
        grupos[indice] = quartil
    return grupos


def agrupar_por_grupo(valores_metrica: list[float], grupos: list) -> dict:
    """Agrupa `valores_metrica` pelo rotulo correspondente em `grupos`.

    `grupos[i]` e o rotulo (quartil, linguagem, tipo de projeto...) do
    repositorio cujo valor de metrica esta em `valores_metrica[i]`. Pares com
    valor de metrica ausente (`None`) sao descartados.
    """
    agrupados: dict = {}
    for valor, grupo in zip(valores_metrica, grupos):
        if valor is None:
            continue
        agrupados.setdefault(grupo, []).append(valor)
    return agrupados


def epsilon_quadrado(h: float, n: int) -> float:
    """Tamanho de efeito do Kruskal-Wallis: e2 = H / (n - 1). Varia de 0 a 1."""
    return h / (n - 1)


def cliff_delta(u1: float, n1: int, n2: int) -> float:
    """Tamanho de efeito do Mann-Whitney: delta = 2*U1/(n1*n2) - 1. Varia de -1 a +1.

    `u1` e a estatistica U devolvida por `scipy.stats.mannwhitneyu(x, y)` (U
    do primeiro grupo passado).
    """
    return 2 * u1 / (n1 * n2) - 1


def interpretar_cliff_delta(delta: float) -> str:
    """Interpretacao usual (Romano et al., 2006) do modulo de Cliff's delta."""
    absoluto = abs(delta)
    if absoluto < 0.147:
        return "desprezivel"
    if absoluto < 0.33:
        return "pequeno"
    if absoluto < 0.474:
        return "medio"
    return "grande"


def comparar_grupos(grupos: dict) -> dict:
    """Compara a distribuicao de uma metrica entre os grupos de `grupos`.

    `grupos` e um dicionario rotulo -> lista de valores (saida de
    `agrupar_por_grupo`). Usa Mann-Whitney se houver exatamente 2 grupos,
    Kruskal-Wallis se houver 3 ou mais. Grupos com menos de 2 valores nao
    permitem teste e sao descartados antes de comparar.
    """
    amostras = [valores for valores in grupos.values() if len(valores) >= 2]
    n = sum(len(valores) for valores in amostras)

    if len(amostras) < 2:
        return {"teste": None, "estatistica": None, "p_valor": None, "efeito": None, "n": n}

    if len(amostras) == 2:
        n1, n2 = len(amostras[0]), len(amostras[1])
        resultado = mannwhitneyu(amostras[0], amostras[1])
        delta = cliff_delta(resultado.statistic, n1, n2)
        return {
            "teste": "mann-whitney",
            "estatistica": resultado.statistic,
            "p_valor": resultado.pvalue,
            "efeito": delta,
            "interpretacao_efeito": interpretar_cliff_delta(delta),
            "n": n,
        }

    resultado = kruskal(*amostras)
    return {
        "teste": "kruskal-wallis",
        "estatistica": resultado.statistic,
        "p_valor": resultado.pvalue,
        "efeito": epsilon_quadrado(resultado.statistic, n),
        "n": n,
    }


def corrigir_holm(resultados: list[dict], chave_p_valor: str = "p_valor") -> list[dict]:
    """Correcao de Holm-Bonferroni para comparacoes multiplas.

    `resultados` e uma lista de dicionarios, um por combinacao fator x
    metrica, cada um com a chave `chave_p_valor`. Devolve uma copia de
    `resultados` com `p_valor_corrigido` e `significativo` (ao nivel de 5%,
    apos a correcao) adicionados em cada item; itens sem p-valor (teste nao
    aplicavel) sao devolvidos como estao, sem entrar na correcao.

    A correcao de Holm ordena os p-valores do menor para o maior e aplica um
    fator de ajuste que diminui a cada posicao: o i-esimo menor p-valor (base
    1) e multiplicado por `(m - i + 1)`, onde `m` e o numero total de testes.
    Isso e menos conservador que Bonferroni simples (que multiplica todos por
    `m`), mas ainda controla a taxa de falsos positivos entre os `m` testes.
    """
    com_p_valor = [
        (indice, r) for indice, r in enumerate(resultados) if r.get(chave_p_valor) is not None
    ]
    m = len(com_p_valor)

    corrigidos = [dict(r) for r in resultados]
    ordenados_por_p = sorted(com_p_valor, key=lambda par: par[1][chave_p_valor])

    maior_ajustado_ate_agora = 0.0
    for posicao, (indice_original, r) in enumerate(ordenados_por_p):
        fator = m - posicao
        ajustado = min(1.0, r[chave_p_valor] * fator)
        # Holm e monotono: o p-valor corrigido nao pode cair abaixo do anterior.
        ajustado = max(ajustado, maior_ajustado_ate_agora)
        maior_ajustado_ate_agora = ajustado
        corrigidos[indice_original]["p_valor_corrigido"] = ajustado
        corrigidos[indice_original]["significativo"] = ajustado < 0.05

    return corrigidos
