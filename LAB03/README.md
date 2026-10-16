# LAB03 — Mineração de métricas DORA

Pipeline que seleciona repositórios open-source populares que usam GitHub Actions e
calcula, a partir dos dados públicos da API do GitHub, aproximações das métricas DORA
(frequência de deploy, lead time, taxa de falha e tempo de recuperação).

> **Versão inicial (Sprint 1).** Hoje o pipeline faz a seleção da amostra, coleta os
> metadados, as releases e os commits entre releases, e calcula o lead time (RQ 02).
> A coleta de workflow runs, o CFR e o tempo de recuperação entram nas próximas tasks.

Enunciado completo: [03 - Mineração de Métricas DORA.md](03%20-%20Mineração%20de%20Métricas%20DORA.md).
Guia para quem contribui com o código: [manual.md](manual.md).

---

## 1. Requisitos

- Python **3.11 ou superior** (o CI usa 3.12)
- Git
- Um token de acesso pessoal do GitHub (só leitura de repositórios públicos)

## 2. Instalação

```bash
git clone https://github.com/PedroL10/Lab01Exp.git
cd Lab01Exp/LAB03
pip install -r requirements.txt
```

## 3. Token do GitHub

O pipeline lê o token da variável de ambiente `GITHUB_TOKEN`. O token **nunca** fica em
arquivo do repositório.

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** →
   **Fine-grained tokens** → **Generate new token**.
2. Em **Repository access**, escolha **Public repositories (read-only)**. Nenhuma
   permissão extra é necessária.
3. Defina a variável no terminal em que o pipeline vai rodar:

| Terminal | Comando |
| --- | --- |
| Git Bash / Linux / macOS | `export GITHUB_TOKEN="github_pat_..."` |
| PowerShell | `$env:GITHUB_TOKEN = "github_pat_..."` |

## 4. Execução

Dentro da pasta `LAB03`, um único comando roda o pipeline inteiro:

```bash
python -m pipeline --config config.yaml
```

### Etapas

| Etapa | O que faz | Saída |
| --- | --- | --- |
| [1] Busca | Busca repositórios com `stars:>1000`, fatiando por faixas de estrelas (a busca devolve no máximo 1.000 por consulta) | `dados/candidatos.csv`, `dados/fatias_busca.csv` |
| [2] GitHub Actions | Descarta candidatos sem workflows (`total_count = 0`) | `dados/filtro_actions.csv` |
| [3] Critério de inclusão | Mantém quem tem, na janela, ≥ 5 releases publicadas e ≥ 50 workflow runs válidos (push no default branch), do mais para o menos estrelado, até completar `n_repos` | `dados/criterio_inclusao.csv` |
| [4] Funil e amostra | Tabela com quantos repositórios restaram em cada etapa e por quê; lista da amostra final | `resultados/funil_selecao.md`, `resultados/funil_selecao.csv`, `resultados/amostra.csv` |
| [5] Metadados | Número de contribuidores (inclusive anônimos) e idade no fim da janela | `dados/contribuidores.csv`, colunas novas em `resultados/amostra.csv` |
| [6] Releases | Releases de cada repositório da amostra | `cache/releases/*.json` |
| [7] Commits e lead time | Commits entre releases consecutivas e lead time (RQ 02, variantes a e b) | `cache/commits_entre_releases/*.json`, `dados/lead_time.csv` |

As pastas `dados/` e `cache/` não são versionadas: são recriadas pelo pipeline. A pasta
`resultados/` é versionada e guarda a amostra usada pelo grupo.

### Interrupções e retomada

Cada etapa grava o resultado de cada repositório assim que ele sai. Se a execução parar
(cota da API esgotada, erro temporário do GitHub, queda de rede ou `Ctrl+C`), **rode o
mesmo comando de novo**: o pipeline pula o que já foi feito e continua de onde parou.

Quando a parada é por cota ou erro do GitHub, o pipeline explica o que aconteceu, por
exemplo:

```
Erro: cota da API esgotada. Ela renova as 14:35; rode o comando de novo depois disso e a coleta continua de onde parou.
```

Para refazer uma etapa do zero, apague o arquivo dela em `dados/` (ou a pasta em `cache/`).

### Tempo e cota

A API REST permite 5.000 requisições por hora com token. As etapas 1 a 5 cabem com folga
numa hora. As etapas 6 e 7 fazem uma chamada de comparação por release e podem esgotar a
cota mais de uma vez com 100 repositórios: deixe o comando rodando e repita-o quando a
cota renovar.

## 5. Configuração (`config.yaml`)

| Campo | Valor atual | Significado |
| --- | --- | --- |
| `janela.inicio` / `janela.fim` | `2025-10-01` / `2026-09-30` | Janela de observação de 12 meses (inclusive nas duas pontas) |
| `selecao.n_repos` | `100` | Tamanho da amostra (≥ 300 na Sprint 2) |
| `selecao.estrelas_min` | `1000` | A busca usa `stars:>estrelas_min` |
| `selecao.max_candidatos` | `2000` | Quantos candidatos buscar antes dos filtros |
| `selecao.min_releases` | `5` | Mínimo de releases publicadas na janela |
| `selecao.min_workflow_runs` | `50` | Mínimo de workflow runs válidos na janela |
| `cache_dir`, `dados_dir`, `resultados_dir` | `cache`, `dados`, `resultados` | Pastas de saída |

Se mudar a janela ou os critérios, apague `dados/criterio_inclusao.csv` (e as etapas
seguintes) para que sejam recalculados.

## 6. Testes

```bash
python -m pytest
python -m pytest --cov=metricas --cov-report=term-missing --cov-fail-under=80
```

Os testes usam respostas simuladas da API (não precisam de token nem de rede). O CI
(`.github/workflows/lab03-testes.yml`, na raiz do repositório) roda os mesmos testes a
cada push que altera `LAB03/`.

## 7. Estrutura

```
LAB03/
├── pipeline/               # coleta e seleção
│   ├── __main__.py         # comando único e ordem das etapas
│   ├── github_client.py    # cliente próprio da API REST (token, paginação, erros)
│   ├── selecao.py          # [1] busca por faixas de estrelas
│   ├── filtro_actions.py   # [2] filtro de GitHub Actions
│   ├── criterio_inclusao.py # [3] janela e critério de inclusão
│   ├── funil.py            # [4] funil de seleção e amostra
│   ├── metadados.py        # [5] contribuidores e idade
│   ├── releases.py         # [6] releases
│   ├── commits.py          # [7] commits entre releases
│   └── retomada.py         # gravação por repositório e retomada
├── metricas/               # funções de cálculo das métricas (lead_time.py)
├── tests/                  # testes com pytest
├── resultados/             # funil e amostra (versionados)
├── config.yaml
└── requirements.txt
```

A coleta usa só `requests`: o enunciado não permite bibliotecas prontas de acesso à API
do GitHub (como PyGithub).

## 8. Problemas comuns

| Mensagem | Causa | Solução |
| --- | --- | --- |
| `Defina a variavel de ambiente GITHUB_TOKEN` | Token não definido neste terminal | Veja a seção 3 |
| `token do GitHub invalido ou expirado (401)` | Token errado, expirado ou revogado | Gere um novo token |
| `cota da API esgotada` | Limite de 5.000 requisições/hora atingido | Espere o horário indicado e rode de novo |
| `erro temporario do GitHub (5xx)` | Instabilidade da API | Rode de novo |
| `bash: :GITHUB_TOKEN: command not found` | Sintaxe do PowerShell usada no Git Bash | Use `export GITHUB_TOKEN=...` |
| `No module named pipeline` | Comando rodado fora da pasta `LAB03` | `cd LAB03` |
| `No module named yaml` | Dependências não instaladas | `pip install -r requirements.txt` |
