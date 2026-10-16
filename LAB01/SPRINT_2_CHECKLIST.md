# Sprint 2 - Checklist Operacional

## Objetivo da sprint
Evoluir a consulta GraphQL da Sprint 1 (100 repositorios) para os 1.000 repositorios com mais estrelas, com paginacao, saida em .csv, primeira versao do relatorio com hipoteses informais, board atualizado e o primeiro snapshot exportado (Lab01S02).

## Pre-requisito
- Sprint 1 concluida: script GraphQL funcionando com 100 repositorios, campos das 7 RQs validados, board com Issues e Assignees em uso.

## Antes de codar
1. Revisar o board: mover as Issues da Sprint 1 que ainda estao em `Doing`/`Review` para `Done` (se de fato concluidas) antes de abrir novas Issues.
2. Criar as Issues da Sprint 2 (ver lista abaixo), cada uma com `Assignee`.
3. Colocar todas as novas Issues no Project, respeitando o WIP definido para `Doing`.
4. Confirmar o padrao de commit com referencia da Issue (ex.: `#15 implementa paginacao GraphQL`).

## Divisao de trabalho

### Integrante responsavel pela paginacao (tarefa mecanica, definir quem)
- Implementar a paginacao (`cursor`/`after` ou `first`+`endCursor`) para varrer os 1.000 repositorios.
- Consolidar a saida em um unico `.csv`.

### Integrante A
- Validar, nos 1.000 repositorios, a consistencia dos dados de RQ01 (idade) e RQ02 (PRs aceitas): distribuicao, outliers, valores ausentes.
- Escrever, em Issue propria, a hipotese informal de RQ01 e RQ02.

### Integrante B
- Validar, nos 1.000 repositorios, a consistencia dos dados de RQ03 (releases) e RQ04 (tempo desde ultima atualizacao): distribuicao, outliers, valores ausentes.
- Escrever, em Issue propria, a hipotese informal de RQ03 e RQ04.

### Integrante C
- Validar, nos 1.000 repositorios, a consistencia dos dados de RQ05 (linguagem) e RQ06 (% issues fechadas): distribuicao, outliers, valores ausentes.
- Escrever, em Issue propria, a hipotese informal de RQ05 e RQ06.
- Apoio na consolidacao do `.csv` final e na primeira versao do relatorio.

## Issues sugeridas para a Sprint 2
1. Implementar paginacao da query GraphQL e exportar os 1.000 repositorios em `.csv` (inclui tratar rate limit / erros parciais durante a paginacao).
2. Validar distribuicao e outliers de RQ01 e RQ02 nos 1.000 repositorios e escrever a hipotese informal correspondente.
3. Validar distribuicao e outliers de RQ03 e RQ04 nos 1.000 repositorios e escrever a hipotese informal correspondente.
4. Validar distribuicao e outliers de RQ05 e RQ06 nos 1.000 repositorios e escrever a hipotese informal correspondente.
5. Montar a primeira versao do relatorio (estrutura + hipoteses consolidadas + metodologia).
6. Rodar o script GraphQL de snapshot do Project e exportar o primeiro CSV de snapshot.

Atualizar o board com o fluxo real da Sprint 2 e nao precisa de Issue propria — e trabalho continuo, feito a cada card movimentado.

## Passo a passo de execucao

### 1. Preparar a paginacao
1.1. Adaptar a query da Sprint 1 para incluir `pageInfo { hasNextPage endCursor }`.
1.2. Fazer um loop que repete a consulta usando `after: endCursor` ate reunir 1.000 repositorios ou `hasNextPage = false`.
1.3. Tratar limite de 1.000 resultados do GitHub Search API (a busca por estrelas via `search` para de paginar em ~1.000 itens; se for necessario, ajustar a estrategia de busca, ex.: `first: 100` por pagina, 10 paginas).
1.4. Adicionar tratamento de erro/retry para rate limit (`X-RateLimit-Remaining`, `retry-after`).

### 2. Consolidar e exportar os dados
2.1. Acumular os repositorios de todas as paginas em uma unica lista/estrutura.
2.2. Garantir que os campos das 7 RQs (definidos na Sprint 1) estejam presentes em todos os registros.
2.3. Exportar para `.csv` (uma linha por repositorio, colunas = campos das RQs).
2.4. Conferir manualmente uma amostra do `.csv` (cabecalho, tipos, encoding).

### 3. Validacao individual por integrante
3.1. Cada integrante roda uma analise simples (min/max/mediana, contagem de nulos) nas suas RQs sobre o `.csv` completo.
3.2. Identificar outliers ou valores incoerentes (ex.: datas futuras, releases negativas).
3.3. Se houver inconsistencia, corrigir a query ou o parsing e reexportar o `.csv`.
3.4. Documentar o que foi encontrado na Issue individual (serve de insumo para o relatorio).

### 4. Escrever hipoteses informais
4.1. Cada integrante escreve, para as RQs sob sua responsabilidade, uma hipotese informal (o que se espera encontrar e por que) antes de olhar os resultados finais consolidados.
4.2. Reunir as hipoteses das 7 RQs num unico documento/secao do relatorio.

### 5. Montar a primeira versao do relatorio
5.1. Estrutura minima: introducao (com as hipoteses), metodologia de coleta (reaproveitar da Sprint 1, atualizando para 1.000 repositorios + paginacao).
5.2. Resultados ainda podem estar incompletos (analise grafica fica para a Sprint 3) — mas a metodologia e as hipoteses devem estar prontas.
5.3. Deixar marcado no relatorio o campo do link do repositorio/GitHub Projects.

### 6. Snapshot do Project
6.1. Reaproveitar/adaptar o script GraphQL da Parte 1 para consultar os itens do Project (issues, status, assignee).
6.2. Exportar o snapshot para um `.csv` separado do CSV de repositorios (ex.: `snapshot_lab01_s02.csv`).
6.3. Guardar esse snapshot no repositorio (sera usado nos Labs 04 e 05).

### 7. Atualizar o GitHub Projects
7.1. Mover as Issues da Sprint 2 pelo fluxo real (`Backlog → To Do → Doing → Review → Done`), sem mover em lote no fim.
7.2. Respeitar o WIP definido em `Doing`.
7.3. Conferir que toda Issue tem `Assignee`.

### 8. Encerrar a sprint
8.1. Confirmar que o `.csv` com 1.000 repositorios esta completo e sem furos.
8.2. Confirmar que a primeira versao do relatorio (introducao + hipoteses + metodologia) esta no repositorio.
8.3. Confirmar que o snapshot do Project foi exportado.
8.4. Revisar o board para garantir evolucao real e commits referenciando Issues.

## Critério de pronto da Sprint 2
- Paginacao funcionando, 1.000 repositorios coletados.
- Dados exportados em `.csv`.
- Primeira versao do relatorio com hipoteses informais.
- Board atualizado com o fluxo real e primeiro snapshot exportado.
- Commits referenciando Issues.

## O que nao precisa fechar ainda
- Nao precisa ter analise grafica/estatistica completa das RQs (fica para a Sprint 3).
- Nao precisa ter a secao de discussao (hipotese vs. resultado) fechada.
- Nao precisa ter o relatorio final formatado.

## Sequencia resumida para a aula
1. Fechar Issues pendentes da Sprint 1 e abrir Issues da Sprint 2.
2. Implementar paginacao (1.000 repositorios).
3. Exportar `.csv` consolidado.
4. Validar dados por integrante (distribuicao/outliers).
5. Escrever hipoteses informais e montar 1a versao do relatorio.
6. Rodar snapshot do Project e exportar CSV.
7. Atualizar board e commits.
