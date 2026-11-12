# LAB04 — Testes de hipótese por dentro

Estudo por simulação que compara dois testes de hipótese em um cenário de Engenharia de
Software, usando uma pequena amostra de dados reais para calibrar a simulação.

- **Endereço do dashboard:** https://pedrol10.github.io/Laboratorios/
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

Um administrador deve habilitar a publicação uma única vez em
[Settings → Pages](https://github.com/PedroL10/Laboratorios/settings/pages), escolhendo
**GitHub Actions** em **Source**. Também pode fazer isso pela CLI, autenticado com uma
conta que tenha permissão para administrar o Pages:

```bash
gh api --method POST repos/PedroL10/Laboratorios/pages -f build_type=workflow
```

Depois dessa configuração, a cada push na `master` que altere a pasta `LAB04`, o workflow
[lab04-dashboard.yml](../.github/workflows/lab04-dashboard.yml) roda os testes, executa
`python -m lab04` e publica a pasta `dashboard/`.
Para publicar sem um novo commit, execute:

```bash
gh workflow run lab04-dashboard.yml --repo PedroL10/Laboratorios --ref master
```

O endereço só deve ser considerado publicado depois que a etapa `publicar` concluir com
sucesso e o link abrir. A execução local continua disponível enquanto o Pages não estiver
habilitado. A regularização está na [issue #86](https://github.com/PedroL10/Laboratorios/issues/86).

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

Escopos de sprint, responsáveis e evidências de contribuição estão em
[CONTRIBUICOES.md](CONTRIBUICOES.md) e nas issues do GitHub Projects.
