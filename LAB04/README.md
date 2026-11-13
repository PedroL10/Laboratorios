# LAB04 — Testes de hipótese por dentro

Estudo por simulação que compara dois testes de hipótese em um cenário de Engenharia de
Software, usando uma pequena amostra de dados reais para calibrar a simulação.

- **Dashboard publicado:** https://pedrol10.github.io/Laboratorios/
- **GitHub Projects:** https://github.com/users/PedroL10/projects/6

## Resultado em uma frase

Com tempos até o merge parecidos com os reais, o t de Welch tem mais poder que o
Mann-Whitney e mantém o erro tipo I abaixo de 5%, por isso é o teste recomendado; a vantagem
passa para o Mann-Whitney quando os dados têm cauda muito pesada.

Enunciado completo: [LAB04.pdf](LAB04.pdf). Pergunta, hipóteses, parâmetros da simulação e
expectativa do grupo: [cenario.md](cenario.md).

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

O comando leva poucos segundos e gera o dashboard em `dashboard/index.html`. Para ver, abra
esse arquivo no navegador (é preciso internet para carregar a biblioteca de gráficos).

O dashboard tem as 7 seções pedidas no enunciado: cenário, dados (G1), como os testes
funcionam (G2), erro tipo I (G3), poder (G4), dados reais e conclusão.

A amostra real já está versionada em [dados/prs.csv](dados/prs.csv), então esse comando
não acessa a internet. Para refazer a coleta (cerca de 1 minuto):

```bash
python -m lab04.coleta
```

## Testes

```bash
python -m pytest
```

## Publicação

A cada push que altere a pasta `LAB04`, o workflow
[lab04-dashboard.yml](../.github/workflows/lab04-dashboard.yml) roda os testes, executa
`python -m lab04` e publica a pasta `dashboard/` no GitHub Pages. Também dá para rodá-lo à mão
na aba **Actions** do repositório.

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| [dashboard/](dashboard/) | Dashboard gerado pelo código |
| [dados/](dados/) | Amostra real e registro de como foi coletada |
| [cenario.md](cenario.md) | Pergunta, hipóteses, parâmetros da simulação e expectativa do grupo |
| [lab04/](lab04/) | Código do estudo |
| [resultados/](resultados/) | Tabelas geradas pelo código |
| [tests/](tests/) | Testes automatizados |

## Reprodutibilidade

Todo número aleatório deve vir de `criar_rng()`, em [lab04/config.py](lab04/config.py).
Nunca use `numpy.random.seed` nem crie outro gerador no código.

## Commits

A correção só considera commits que citam a Issue: `#NUMERO Verbo + objeto curto`.
