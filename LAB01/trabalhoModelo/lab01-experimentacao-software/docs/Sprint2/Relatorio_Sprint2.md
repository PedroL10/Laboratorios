# Relatório Sprint 2 — Lab01S02

## O que foi feito

- Implementação do script `lab01s02.py` com suporte a **paginação via cursor** pela API GraphQL do GitHub
- Coleta de **1000 repositórios populares** (10 repositórios por página × 100 páginas)
- Adição da query `QUERY_PAGINADA` em `queries.py` com suporte a `pageInfo { hasNextPage endCursor }`
- Cálculo de métricas derivadas por repositório:
  - `idade_dias` — diferença entre data de criação e data atual
  - `dias_desde_atualizacao` — diferença entre data da última atualização e data atual
  - `razao_issues_fechadas` — proporção entre issues fechadas e total de issues
- Exportação dos dados para arquivo CSV (`docs/Sprint2/repositorios.csv`) com 12 colunas
- Exibição de estatísticas resumidas ao final da execução
- Mecanismo de **retry com backoff** mantido e aprimorado

---

## Dificuldades encontradas

### Instabilidade da API em alto volume

Ao aumentar o volume de requisições para 100 páginas, a API do GitHub apresentou respostas intermitentes com erros 5xx, exigindo retentativas frequentes.

### Controle de cursor de paginação

A lógica de paginação exige rastreamento correto do `endCursor` retornado em cada resposta. Um cursor inválido ou ausente interrompe a coleta antes de atingir o total desejado.

### Padronização dos dados para CSV

Alguns repositórios não possuíam linguagem primária, releases ou issues, retornando `null` na API. Era necessário tratar esses valores para garantir consistência no CSV.

### Tempo de execução

Coletar 1000 repositórios com pausas entre páginas levou tempo considerável, exigindo monitoramento contínuo do processo.

---

## Soluções aplicadas

- **Paginação com cursor**: uso de `first: 10, after: $cursor` e atualização do cursor a cada resposta via `pageInfo.endCursor`
- **Retry com backoff linear e exponencial**: até 10 tentativas por página, com espera crescente para erros 5xx e de rate limit
- **Timeout de 120 segundos** por requisição para evitar travamentos
- **Pausa de 2 segundos** entre páginas para respeitar os limites da API
- **Tratamento de nulos**: valores ausentes substituídos por `0`, `""` ou `"Não especificada"` conforme o campo
- **Função `processar_repositorio()`**: mapeamento padronizado de JSON para dicionário flat antes da escrita no CSV

---

## Conclusão da Sprint 2

A sprint entregou a base definitiva de dados (1000 repositórios) em formato estruturado e pronto para análise estatística. A estratégia de paginação com cursor mostrou-se estável e eficiente. O arquivo CSV gerado contém todas as métricas necessárias para responder às 6 RQs na Sprint 3.

---

## Artefatos gerados

- `lab01s02.py` — script de coleta com paginação
- `queries.py` — query `QUERY_PAGINADA` adicionada
- `docs/Sprint2/repositorios.csv` — dados de 1000 repositórios (1001 linhas: cabeçalho + dados)
