# Relatório Sprint 1 — Lab01S01

## O que foi feito

- Implementação da primeira coleta de dados via API GraphQL do GitHub
- Desenvolvimento do script `lab01s01.py` em Python utilizando:
  - `requests` para consumo da API
  - `python-dotenv` para leitura segura do token via `.env`
  - API GraphQL do GitHub (`https://api.github.com/graphql`)
- Query buscando os 100 repositórios mais estrelados com múltiplas métricas
- Coleta das seguintes métricas por repositório:
  - `nameWithOwner`, `createdAt`, `updatedAt`
  - `primaryLanguage`
  - `pullRequests(states: MERGED) { totalCount }`
  - `releases { totalCount }`
  - `issues { totalCount }`, `closedIssues: issues(states: CLOSED) { totalCount }`
  - `stargazerCount`
- Estratégia de coleta por **lotes de faixas de estrelas** (10 lotes × 10 repositórios = 100 total)
- Implementação de mecanismo de retry com backoff para aumentar robustez

---

## Dificuldades encontradas

### Erro 502 – Limitação de Complexidade da API

Ao tentar solicitar `first: 100` junto com múltiplas métricas aninhadas (pull requests, issues, releases, linguagem principal etc.), a API retornou erro **502 Bad Gateway**. Esse erro ocorre quando a query excede o limite de complexidade permitido pela API do GitHub, pois queries com muitos nós e campos aninhados aumentam significativamente o custo computacional.

### Erro de Sintaxe GraphQL

Após simplificar a query, foi retornado o erro `Expected NAME, actual: ("\n")`. Esse erro indicava problema estrutural causado por chaves `{}` abertas e não fechadas corretamente.

### Erro de Union Type (SearchResultItem)

Após corrigir a sintaxe, surgiu o erro `Selections can't be made directly on unions`. O campo `search` retorna um tipo UNION chamado `SearchResultItem`, e em GraphQL não é permitido acessar campos diretamente em um union sem especificar o tipo concreto.

### Problema no arquivo `.env`

O token foi configurado incorretamente usando `:` como separador em vez de `=`, causando falha na leitura da variável de ambiente.

---

## Soluções aplicadas

- **Estratégia de lotes por faixa de estrelas**: divisão em 10 faixas (`stars:>=200000` até `stars:40000..44999`), coletando 10 repositórios por lote, evitando o limite de complexidade da API
- **Correção de sintaxe GraphQL**: ajuste no fechamento correto dos blocos `{}`
- **Uso de Inline Fragment**: `... on Repository { ... }` para acessar campos de um union type
- **Retry com backoff linear**: até 10 tentativas com espera crescente entre falhas
- **Correção do `.env`**: formato correto `GITHUB_TOKEN=valor`

---

## Conclusão da Sprint 1

A sprint validou a arquitetura da coleta, estabilizou a consulta GraphQL e garantiu a extração das métricas necessárias em pequena escala (100 repositórios). Os principais desafios técnicos foram superados, estabelecendo uma base sólida para a escalagem na Sprint 2.

---

## Artefatos gerados

- `lab01s01.py` — script de coleta
- `queries.py` — query GraphQL (`QUERY_POR_FAIXA`)
- `docs/Sprint1/saida_sprint1.txt` — saída de execução

