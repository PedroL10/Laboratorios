# Decisão do grupo — software, caminho e pergunta de pesquisa

Decidido pelo trio em 2026-11-19 (tarefa comum da Sprint 1, ver
[DIVISAO_SPRINT1.md](../DIVISAO_SPRINT1.md)).

> **Atualização 2026-11-19:** a decisão original (PostgreSQL 15×17 com `pgbench` em
> Docker) foi revista porque a máquina de coleta não tem Docker nem permissão para
> instalar software com privilégio de administrador. O grupo trocou para o caminho
> "medir o serviço de fora" (seção 2b do enunciado), descrito abaixo.

## Software: API SGS do Banco Central do Brasil (dados abertos)

O Sistema Gerenciador de Séries Temporais (SGS) é a API pública oficial do Banco Central
para consulta de séries históricas (ex.: taxa de câmbio, índices, indicadores
macroeconômicos). Endpoint base: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.<codigo>`.

| Critério (seção 2a) | Evidência | Fonte |
| --- | --- | --- |
| Real | API oficial do Banco Central do Brasil, documentada publicamente, mantida pelo próprio BCB | https://dadosabertos.bcb.gov.br/ — `<preencher data de acesso>` |
| Em operação | API em produção, usada para consultar séries atualizadas diariamente (ex.: série 1 = dólar PTAX, atualizada todo dia útil) | https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json — `<preencher data de acesso>` |
| Alto impacto | Fonte oficial de câmbio/indicadores usada por bancos, fintechs e sistemas financeiros brasileiros para cálculo de cotação e compliance | `<preencher: exemplos públicos de fintechs/bancos que citam a API do BCB como fonte, com link e data>` |

> A pendência de cada linha é preencher a data de acesso e, no critério de alto impacto,
> achar 1–2 exemplos públicos (posts técnicos, documentação de fintech) citando a API do
> BCB como fonte — responsabilidade de **A (PedroL10)**, dentro da tarefa de comprovar os
> três critérios (ver DIVISAO_SPRINT1.md).

**Por que não ViaCEP nem BrasilAPI:** ambas têm o caminho da API (`/ws/` e `/api/*`,
respectivamente) bloqueado no próprio `robots.txt` — usá-las violaria a regra de ética do
enunciado ("respeite... o robots.txt"). A API `api.bcb.gov.br` não tem `robots.txt`
restritivo (confirmado em 2026-11-19).

## Caminho (seção 2b): Medir o serviço de fora

Observar a API do BCB como um usuário comum faria (requisições HTTP GET simples, sem
autenticação), medindo o **tempo de resposta** em diferentes horários do dia, respeitando
no máximo 1 requisição por segundo.

Por que esse caminho: não depende de instalação de software nem de privilégio de admin,
está entre os exemplos dados pelo próprio enunciado ("tempo de resposta de APIs públicas
ao longo do dia"), e ainda permite reaproveitar o desenho de experimento do LAB04 (dois ou
mais grupos de medição, teste de hipótese, tamanho do efeito).

## Pergunta de pesquisa

O tempo de resposta da API do BCB varia entre horário comercial (09h–18h) e fora do
horário comercial, em dias úteis?

## GQM (template de Basili) — primeira versão

- **Objetivo:** Analisar as requisições à API SGS do Banco Central com o propósito de
  comparar em relação ao tempo de resposta no contexto de horário comercial vs. fora do
  horário comercial, do ponto de vista de quem consome a API (equipe de desenvolvimento).
- **Questões:**
  - Q1: Qual o tempo médio de resposta da API em horário comercial?
  - Q2: Qual o tempo médio de resposta da API fora do horário comercial?
  - Q3: A diferença entre os dois grupos é estatisticamente significativa?
- **Métricas:**
  - M1: Tempo de resposta por requisição (latência ponta a ponta, em milissegundos,
    medida no cliente).
  - M2: Código de status HTTP da resposta (para descartar falhas/timeouts da análise de
    latência).

## Hipóteses (primeira versão)

- H0: não há diferença no tempo médio de resposta entre horário comercial e fora dele.
- H1: há diferença no tempo médio de resposta entre os dois períodos.

Teste de hipótese e tamanho de efeito a confirmar por **C** na Sprint 1 (a decidir entre
Welch/Mann-Whitney, por continuidade com o LAB04, conforme a escala e a distribuição dos
dados coletados).

## Ameaças à validade (levantamento inicial — revisar na Sprint 3)

- **Conclusão:** poucas requisições por período podem não dar poder estatístico
  suficiente; mitigar definindo um número mínimo de amostras por período no plano de
  coleta de B.
- **Interna:** a conexão de internet do próprio grupo pode variar e se confundir com a
  latência do servidor; mitigar medindo apenas o tempo entre o envio da requisição e o
  recebimento da resposta (latência ponta a ponta) e registrando se há quedas de conexão
  durante a coleta.
- **Construto:** latência medida do lado do cliente inclui rede, não só processamento do
  servidor; registrar isso como limite de medida (não é uma medição isolada do servidor).
- **Externa:** resultado vale para essa rede/geolocalização e para este endpoint
  específico da API; não generaliza automaticamente para outras redes, horários fora da
  amostra ou outros endpoints do BCB.

## Cuidados de ética aplicados

- Nenhuma requisição excede 1 por segundo (aplicado no próprio script de coleta).
- Não há coleta de dados pessoais — as séries consultadas são indicadores econômicos
  agregados, públicos.
- `robots.txt` do domínio `api.bcb.gov.br` verificado antes da coleta (sem restrição
  encontrada).

## Pendências

- [ ] A: preencher data de acesso e exemplos de alto impacto na tabela de critérios.
- [ ] B: confirmar parâmetros finais da coleta completa (nº de dias, nº de amostras por
  período) — coleta piloto já rodada (ver [docs/plano_coleta.md](plano_coleta.md)).
- [ ] C: validar/ajustar o teste de hipótese e o plano de análise para o tempo de resposta.
