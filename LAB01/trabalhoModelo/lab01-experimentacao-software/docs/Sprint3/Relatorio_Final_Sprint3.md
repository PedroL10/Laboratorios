# Relatório Sprint 3 — Lab01S03

## O que foi feito

- Implementação do script `lab01s03.py` para análise estatística dos dados coletados na Sprint 2
- Leitura e normalização do arquivo `docs/Sprint2/repositorios.csv` (1000 repositórios)
- Cálculo de **média e mediana** para todas as métricas das RQs:
  - Idade dos repositórios (`idade_dias`)
  - Total de PRs merged (`prs_merged`)
  - Total de releases (`releases`)
  - Dias desde a última atualização (`dias_desde_atualizacao`)
  - Razão de issues fechadas (`razao_issues_fechadas`)
- Contagem e ranqueamento de linguagens primárias (Top 10)
- Geração de 4 gráficos em `docs/Sprint3/figures/`:
  - Gráfico de barras: Top linguagens
  - Histograma: Distribuição de idade
  - Histograma: Distribuição de issues fechadas
  - Boxplot: Distribuição de PRs merged
- Geração automática do relatório final em Markdown com tabelas, métricas e referências aos gráficos
- Aplicação de **regras objetivas de decisão** para confirmar ou rejeitar cada hipótese

---

## Dificuldades encontradas

### Dependência de biblioteca de visualização

O ambiente não possuía `matplotlib` instalado, impedindo a geração dos gráficos na primeira execução.

### Definição de critérios objetivos de decisão

Era necessário estabelecer limiares claros e justificados para confirmar ou rejeitar cada hipótese, sem tornar os critérios arbitrários demais.

### Consistência entre dados calculados e texto gerado

O relatório é gerado automaticamente pelo script, então qualquer inconsistência entre variáveis e texto produziria um documento incorreto.

### Caminhos relativos para os gráficos

O script precisa referenciar os gráficos com caminhos corretos tanto para salvar os arquivos quanto para exibi-los no Markdown gerado.

---

## Soluções aplicadas

- **Instalação de `matplotlib`** via `pip install matplotlib` no ambiente virtual
- **Regras explícitas de decisão** documentadas por RQ (ex: RQ01 confirmada se mediana >= 5 anos)
- **Automação completa da escrita do relatório** a partir das métricas calculadas, eliminando inconsistências manuais
- **`BASE_DIR` e `os.path.join()`** usados para garantir caminhos absolutos e portáveis

---

## Resultados (RQs respondidas)

| RQ | Métrica analisada | Resultado numérico | Hipótese |
|---|---|---|---|
| RQ01 | Mediana da idade dos repositórios | 8,39 anos | ✅ Confirmada |
| RQ02 | Mediana de PRs merged | 739 | ✅ Confirmada |
| RQ03 | Mediana de releases | 40 | ✅ Confirmada |
| RQ04 | Mediana de dias desde atualização | 0 dias | ✅ Confirmada |
| RQ05 | Top linguagens | Python, TypeScript, JavaScript | ✅ Confirmada |
| RQ06 | Mediana da razão de issues fechadas | 87,78% | ✅ Confirmada |

---

## Conclusão da Sprint 3

A sprint finalizou o ciclo analítico do experimento, com visualizações e respostas quantitativas para todas as 6 RQs. Todas as hipóteses foram confirmadas pelos dados. O processo automatizado garante reprodutibilidade total dos resultados.

---

## Artefatos gerados

- `lab01s03.py` — script de análise e visualização
- `docs/Sprint3/figures/top_linguagens.png`
- `docs/Sprint3/figures/distribuicao_idade.png`
- `docs/Sprint3/figures/distribuicao_issues_fechadas.png`
- `docs/Sprint3/figures/boxplot_prs.png`
- `docs/Sprint3/Relatorio_Final_Sprint3.md` — este relatório

---



- Kaio Henrique Oliveira da Silveira Barbosa

## Introdução

Este relatório final consolida os resultados do estudo sobre repositórios populares no GitHub, com base em 1000 repositórios coletados via API GraphQL. O foco é responder as questões de pesquisa (RQs) propostas no projeto.

## Questões de pesquisa e hipóteses

- **RQ01**: Sistemas populares são maduros/antigos?
  - Hipótese: sistemas populares tendem a ser mais antigos.
- **RQ02**: Sistemas populares recebem muita contribuição externa?
  - Hipótese: sistemas populares apresentam alto volume de PRs aceitas.
- **RQ03**: Sistemas populares lançam releases com frequência?
  - Hipótese: sistemas populares lançam releases regularmente.
- **RQ04**: Sistemas populares são atualizados com frequência?
  - Hipótese: sistemas populares são atualizados recentemente.
- **RQ05**: Sistemas populares são escritos nas linguagens mais populares?
  - Hipótese: linguagens predominantes incluem JavaScript, Python, Java e TypeScript.
- **RQ06**: Sistemas populares possuem alto percentual de issues fechadas?
  - Hipótese: percentual de fechamento de issues é alto.

## Objetivo

Responder quantitativamente às 6 RQs com base nos dados coletados nas sprints anteriores, usando análise estatística descritiva e visualizações.

## Metodologia

1. Leitura do arquivo CSV da Sprint 2 (`docs/Sprint2/repositorios.csv`).
2. Limpeza e normalização dos dados numéricos.
3. Cálculo de métricas centrais (média e mediana) por RQ.
4. Geração de gráficos de distribuição e frequência.
5. Interpretação dos resultados e decisão sobre as hipóteses.

### Regras de decisão adotadas

- RQ01: hipótese confirmada se mediana da idade >= 5 anos.
- RQ02: hipótese confirmada se mediana de PRs merged >= 100.
- RQ03: hipótese confirmada se mediana de releases >= 10.
- RQ04: hipótese confirmada se mediana de dias desde atualização <= 30.
- RQ05: hipótese confirmada se ao menos 3 linguagens esperadas (JS/Python/Java/TS) aparecem no top 10.
- RQ06: hipótese confirmada se mediana da razão de issues fechadas >= 80%.

## Resultados

### Tabela de respostas das RQs

| RQ | Métrica analisada | Resultado numérico | Resposta |
|---|---|---|---|
| RQ01 | Mediana da idade dos repositórios | 8.39 anos | Sim |
| RQ02 | Mediana de PRs merged | 739 | Sim |
| RQ03 | Mediana de releases | 40 | Sim |
| RQ04 | Mediana de dias desde atualização | 0 dias | Sim |
| RQ05 | Top linguagens | Python, TypeScript, JavaScript, Não especificada, Go | Sim |
| RQ06 | Mediana da razão de issues fechadas | 87.78% | Sim |

### Tabela de linguagens (Top 10)

| Posição | Linguagem | Quantidade | Percentual |
|---|---|---:|---:|
| 1 | Python | 200 | 20.00% |
| 2 | TypeScript | 160 | 16.00% |
| 3 | JavaScript | 115 | 11.50% |
| 4 | Não especificada | 95 | 9.50% |
| 5 | Go | 77 | 7.70% |
| 6 | Rust | 54 | 5.40% |
| 7 | Java | 47 | 4.70% |
| 8 | C++ | 46 | 4.60% |
| 9 | C | 25 | 2.50% |
| 10 | Jupyter Notebook | 23 | 2.30% |

### Métricas gerais

- Total de repositórios analisados: **1000**
- Faixa de estrelas: **29,574** a **472,576**
- Média de estrelas: **58017**
- Média de idade: **8.19 anos**
- Média de PRs merged: **3956**
- Média de releases: **120.67**
- Média de dias desde atualização: **0.00 dias**
- Média da razão de issues fechadas: **80.57%**

### Gráficos


#### Top Linguagens

![Top Linguagens](figures/top_linguagens.png)

#### Distribuicao Idade

![Distribuicao Idade](figures/distribuicao_idade.png)

#### Distribuicao Issues Fechadas

![Distribuicao Issues Fechadas](figures/distribuicao_issues_fechadas.png)

#### Boxplot Prs

![Boxplot Prs](figures/boxplot_prs.png)


## Discussões (insights)

- A mediana de idade indica o nível de maturidade dos projetos mais populares.
- A distribuição de PRs merged sugere presença de forte colaboração externa em parte dos projetos, mas com assimetria entre eles.
- A distribuição de releases mostra que popularidade não implica necessariamente alta frequência de versões formais.
- O tempo desde a última atualização aponta o quão ativos os projetos estão atualmente.
- A distribuição de linguagens confirma concentração em poucas tecnologias amplamente adotadas.
- A razão de issues fechadas permite avaliar o nível de manutenção/saúde operacional.

## Conclusão e tomadas de decisão (hipóteses)

- **RQ01**: Hipótese confirmada (Mediana de idade = 8.39 anos).
- **RQ02**: Hipótese confirmada (Mediana de PRs merged = 739).
- **RQ03**: Hipótese confirmada (Mediana de releases = 40).
- **RQ04**: Hipótese confirmada (Mediana desde última atualização = 0 dias).
- **RQ05**: Hipótese confirmada (Top linguagens contém Java, JavaScript, Python, TypeScript).
- **RQ06**: Hipótese confirmada (Mediana da razão de issues fechadas = 87.78%).


