# LAB04 — Testes de hipótese por dentro

Estudo por simulação que compara dois testes de hipótese em um cenário de Engenharia de
Software, usando uma pequena amostra de dados reais para calibrar a simulação.

> **Em construção.** Hoje o repositório tem a amostra real coletada e a análise da forma
> da distribuição. A simulação e o dashboard ainda não foram implementados.

Enunciado completo: [LAB04.pdf](LAB04.pdf).

## Decisões do grupo

| Decisão | Escolha | Motivo |
| --- | --- | --- |
| Par de testes | **P1: t de Welch × Mann-Whitney** | Tempo até o merge costuma ser assimétrico e ter outliers, situação em que os dois testes podem divergir. |
| Cenário | Tempo até o merge de PRs do `hpx`, antes e depois do CodeRabbit | Os dados são públicos e o bot foi adotado em uma data clara. Detalhes em [dados/README.md](dados/README.md). |
| Dashboard | Página HTML gerada com Plotly | Abre sem servidor e pode ser publicada no GitHub Pages. |
| Semente | `42` | Definida em [lab04/config.py](lab04/config.py). |

## Requisitos

- Python 3.12 ou superior (testado com 3.14)

## Instalação

Dentro da pasta `LAB04`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No PowerShell, ative o ambiente com `.venv\Scripts\Activate.ps1`.

## Execução

Um único comando roda o projeto do início ao fim:

```bash
python -m lab04
```

A amostra real já está versionada em [dados/prs.csv](dados/prs.csv), então esse comando
não acessa a internet. Para refazer a coleta (cerca de 1 minuto):

```bash
python -m lab04.coleta
```

## Testes

```bash
python -m pytest
```

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| [dados/](dados/) | Amostra real e registro de como foi coletada |
| [lab04/](lab04/) | Código do estudo |
| [resultados/](resultados/) | Tabelas geradas pelo código |
| [tests/](tests/) | Testes automatizados |

## Reprodutibilidade

Todo número aleatório deve vir de `criar_rng()`, em [lab04/config.py](lab04/config.py).
Nunca use `numpy.random.seed` nem crie outro gerador no código.

## Commits

A correção só considera commits que citam a Issue: `#NUMERO Verbo + objeto curto`.
