# Sprint 1 - Checklist Operacional

## Objetivo da sprint
Validar a coleta via GitHub GraphQL para 100 repositorios, com os campos necessarios para as RQs, board ativo no GitHub Projects e Issues rastreaveis por integrante.

## Antes de codar
1. Confirmar o GitHub Projects do grupo.
2. Criar as colunas do board: `Backlog`, `To Do`, `Doing`, `Review`, `Done`.
3. Definir WIP de `Doing` como no maximo 3 cards.
4. Criar Issues reais para a sprint, cada uma com `Assignee`.
5. Colocar todas as Issues no Project.
6. Definir um padrao de commit com referencia da Issue, por exemplo `#12 implementa consulta GraphQL`.
7. Escolher a fonte oficial para a RQ05 e manter a mesma referencia ate o fim do laboratorio.

## Divisao de trabalho

### Integrante A
- RQ01: idade do repositorio.
- RQ02: total de pull requests aceitas.

### Integrante B
- RQ03: total de releases.
- RQ04: tempo ate a ultima atualizacao.

### Integrante C
- RQ05: linguagem primaria versus a fonte escolhida de linguagens populares.
- RQ06: razao entre issues fechadas e total de issues.
- Apoio na estrutura da query e validacao dos campos.

## Issues sugeridas para a Sprint 1
1. Configurar autenticacao com a GitHub GraphQL API.
2. Montar query base para coletar 100 repositorios.
3. Validar campos da RQ01 e RQ02 em amostra pequena.
4. Validar campos da RQ03 e RQ04 em amostra pequena.
5. Validar campos da RQ05 e RQ06 em amostra pequena.
6. Integrar a coleta final com os 100 repositorios.
7. Registrar a saida provisoria em JSON ou CSV.
8. Atualizar o board com o fluxo real das Issues.

## Passo a passo de execucao

### 1. Preparar o ambiente
1.1. Criar a estrutura do projeto no repositorio.
1.2. Configurar o token do GitHub em variavel de ambiente.
1.3. Criar o script principal que vai falar com a API GraphQL.

### 2. Montar a coleta inicial
2.1. Fazer uma requisicao simples para confirmar autenticacao.
2.2. Trazer poucos repositorios apenas para validar formato.
2.3. Ajustar nomes de campos, tipos e datas se necessario.

### 3. Definir os campos da query
3.1. Data de criacao do repositorio.
3.2. Data da ultima atualizacao.
3.3. Linguagem primaria.
3.4. Total de releases.
3.5. Total de issues abertas e fechadas.
3.6. Dados suficientes para calcular pull requests aceitas.
3.7. Nome do repositorio e numero de estrelas.

### 4. Validacao por integrante
4.1. Integrante A testa 5 a 10 repositorios e confere a idade.
4.2. Integrante B testa 5 a 10 repositorios e confere releases e atualizacao.
4.3. Integrante C testa 5 a 10 repositorios e confere linguagem e issues.
4.4. Se algum valor parecer incoerente, corrigir a query antes de integrar.

### 5. Integrar a coleta dos 100 repositorios
5.1. Ajustar a consulta para retornar os 100 primeiros repositorios.
5.2. Garantir que todos os campos das 7 RQs estejam presentes.
5.3. Salvar uma saida provisoria para inspeção.

### 6. Atualizar o GitHub Projects
6.1. Toda Issue começa em `Backlog`.
6.2. Ao iniciar, mover para `To Do`.
6.3. Durante a execucao, mover para `Doing`.
6.4. Depois da implementacao, mover para `Review`.
6.5. So mover para `Done` apos validacao.
6.6. Nao mover cards em massa no fim da sprint.

### 7. Encerrar a sprint
7.1. Verificar se a coleta de 100 repositorios funciona de ponta a ponta.
7.2. Confirmar que cada integrante tem tarefas e commits vinculados a Issues.
7.3. Revisar o board para garantir evolucao real.

## Critério de pronto da Sprint 1
- Script GraphQL funcionando com 100 repositorios.
- Campos essenciais coletados e validados.
- Issues distribuidas entre os 3 integrantes.
- Board atualizado com o fluxo real.
- Commits referenciando Issues.

## O que nao precisa fechar ainda
- Nao precisa ter os 1000 repositorios.
- Nao precisa ter o CSV final consolidado.
- Nao precisa ter analise grafica completa.
- Nao precisa fechar o relatorio final.

## Sequencia resumida para a aula
1. Criar Issues da sprint.
2. Distribuir responsaveis no Projects.
3. Implementar autenticacao GraphQL.
4. Escrever a query base.
5. Validar em amostra pequena.
6. Integrar os 100 repositorios.
7. Atualizar board e commits.