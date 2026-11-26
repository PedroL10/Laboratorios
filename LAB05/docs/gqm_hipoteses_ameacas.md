# GQM, hipóteses e ameaças à validade (versão revisada)

Revisado em 26/11/2026, antes de olhar os dados da coleta completa. Esta versão substitui a
primeira, que estava em [decisao_software_caminho.md](decisao_software_caminho.md).

## O que mudou em relação à primeira versão

| Antes | Agora | Por quê |
| --- | --- | --- |
| Tempo **médio** de resposta | **Mediana** e **p95** | A latência é assimétrica, com alguns valores muito altos. O piloto foi de 112 a 831 ms. A mediana mostra o caso típico, e o p95 mostra a cauda, que é o que um usuário percebe como "a API está lenta". São os indicadores usados em SLIs e SLOs. |
| Cada requisição é uma amostra | Cada **rodada** de 5 requisições é uma amostra | Requisições do mesmo minuto medem o mesmo estado da rede e não são independentes. Tratá-las como amostras separadas aumentaria artificialmente o poder do teste. |
| Só latência | Latência **e disponibilidade** | Uma API rápida que falha mais em um período também importa para quem a consome. |
| Sem expectativa registrada | Expectativa registrada antes dos dados | Evita ajustar a hipótese depois de ver o resultado, como fizemos no LAB04. |
| Ameaças sem status | Ameaças com mitigação e status | Mostra o que foi resolvido pelo desenho do estudo e o que continua sendo um limite. |

## GQM (template de Basili)

**Objetivo.**

- **Analisar** a API SGS do Banco Central em operação,
- **com o propósito de** caracterizar e comparar,
- **com respeito ao** tempo de resposta e à disponibilidade,
- **do ponto de vista de** quem desenvolve sistemas que consomem a API,
- **no contexto de** requisições feitas de fora, a partir de uma máquina na nuvem (GitHub Actions),
  em dias úteis, no horário comercial (09h–18h) e fora dele.

**Questões.**

| Questão | Métricas |
| --- | --- |
| Q1. Qual é o tempo de resposta típico em cada período? | M1, M3 |
| Q2. Qual é o tempo de resposta nos piores casos em cada período? | M1, M4 |
| Q3. A API responde com sucesso na mesma proporção nos dois períodos? | M2, M5 |
| Q4. A diferença entre os períodos é estatisticamente significativa e de que tamanho? | M3, M6 |

**Métricas.**

| Métrica | Definição | Tipo | Escala | Estatísticas permitidas |
| --- | --- | --- | --- | --- |
| M1. Latência da requisição | Tempo entre enviar a requisição e receber a resposta completa, em ms, medido no cliente | Direta | Razão | Todas: média, mediana, percentis, razões |
| M2. Resultado da requisição | Status HTTP (200, 4xx, 5xx) ou falha de rede | Direta | Nominal | Contagens, proporções, moda |
| M3. Mediana da rodada | Mediana de M1 nas 5 requisições de uma rodada, só com status 200 | Derivada | Razão | Todas |
| M4. p95 do período | Percentil 95 de M1 em todas as requisições com sucesso do período | Derivada | Razão | Todas |
| M5. Taxa de sucesso | Requisições com status 200 ÷ total de requisições do período | Derivada | Razão (proporção) | Todas |
| M6. Tamanho do efeito | Diferença e razão entre as medianas de M3 nos dois períodos, com intervalo de confiança, e probabilidade de superioridade | Derivada | Razão | Todas |

**Entidade e atributos.** A entidade é um **produto**: a API em operação. Tempo de resposta e
disponibilidade são **atributos externos**, porque só existem quando o software roda em seu
ambiente. Na ISO/IEC 25010, eles correspondem a *comportamento temporal* (eficiência de
desempenho) e *disponibilidade* (confiabilidade).

**Variáveis.**

- **Independente:** período do dia. É nominal, com dois níveis: `comercial` e `fora_comercial`.
  Vem da hora da medição, em Brasília.
- **Dependentes:** M3, M4 e M5.
- **Mantidas fixas:** endpoint, série consultada, máquina de coleta (GitHub Actions), tamanho
  da rodada e intervalo entre requisições.

**Armadilhas de medição.**

- **Goodhart e Campbell:** a métrica não gera incentivo para ninguém "jogar" com ela. O BCB não
  sabe que está sendo medido, e o grupo não ganha nada com um resultado específico. O risco é
  baixo.
- **Falácia de McNamara:** tempo de resposta não é toda a qualidade da API. Não medimos se os
  dados estão corretos nem se chegam no horário. A conclusão vai se limitar ao que foi medido.

## Hipóteses

**Hipótese principal (Q4), bicaudal, α = 0,05.** A unidade é a rodada (M3), considerando só os
dias úteis.

- **H0:** a mediana das rodadas tem a mesma distribuição no horário comercial e fora dele. Uma
  rodada de um período tem a mesma chance de ser mais lenta ou mais rápida que uma do outro.
- **H1:** as rodadas de um dos períodos tendem a ser mais lentas.

O teste específico, Welch ou Mann-Whitney, fica no plano de análise (próxima Issue). A escolha
vai considerar a forma dos dados, como aprendemos no LAB04.

**Por que bicaudal.** Há motivos para os dois sentidos:

- o horário comercial pode ser **mais lento**, porque mais sistemas consultam a API;
- o horário comercial pode ser **mais rápido**, porque o cache fica "quente" com tantas
  consultas, ou porque a infraestrutura reserva mais capacidade nesse horário.

**Hipóteses secundárias (exploratórias).**

- **Q2, cauda:** o p95 é igual nos dois períodos. O teste é bootstrap da diferença de p95.
- **Q3, disponibilidade:** a taxa de sucesso é igual nos dois períodos. O teste é o exato de
  Fisher, porque esperamos poucas falhas.

As duas são relatadas com correção de Holm e não mudam a conclusão principal.

**Expectativa do grupo, registrada em 26/11/2026, antes da coleta completa.** Esperamos o
horário comercial um pouco mais lento, com diferença de mediana pequena, de até 20%. Esperamos
diferença maior no p95 do que na mediana, e nenhuma diferença na taxa de sucesso, que deve ficar
perto de 100% nos dois períodos.

## Ameaças à validade

Status: **mitigada** (o desenho resolve), **parcial** (reduzida, mas não eliminada) ou
**aceita** (limite declarado nas conclusões).

### Validade de conclusão

| Ameaça | Mitigação | Status |
| --- | --- | --- |
| **Pseudorreplicação:** as 5 requisições da mesma rodada não são independentes. | A unidade de análise é a rodada (M3). | Mitigada |
| **Dependência no tempo:** rodadas de horas vizinhas e do mesmo dia se parecem. Um dia ruim pesa em várias rodadas. | Análise de sensibilidade com um valor por dia e período (a mediana do dia), comparando os períodos dentro de cada dia com o teste pareado de Wilcoxon. | Parcial |
| **Pouco poder:** poucas rodadas podem não detectar uma diferença pequena. | Cerca de 90 rodadas no horário comercial e 150 fora dele em 2 semanas. O poder será estimado por simulação calibrada com os dados, reaproveitando o LAB04. | Parcial |
| **Pressupostos do teste:** latência assimétrica e com outliers. | A escolha do teste vai seguir o que aprendemos no LAB04, e o tamanho do efeito será relatado com intervalo de confiança. | Mitigada |
| **Múltiplas comparações:** testar mediana, p95 e taxa de sucesso aumenta a chance de um falso positivo. | Uma única hipótese principal; as secundárias são exploratórias e corrigidas por Holm. | Mitigada |

### Validade interna

| Ameaça | Mitigação | Status |
| --- | --- | --- |
| **Rede do coletor varia com o horário:** a internet de casa fica mais lenta à noite. | A coleta roda no GitHub Actions, com rede de data center, e não em casa. | Mitigada |
| **A carga da própria nuvem varia com o horário:** o horário comercial do Brasil coincide com o dos EUA, onde fica boa parte das máquinas do GitHub. | Não dá para eliminar. Nas conclusões, registramos que a diferença pode vir de qualquer ponto do caminho até a API. | Aceita |
| **Atualização diária da PTAX:** a cotação do dia é divulgada por volta das 13h, dentro do horário comercial. A troca do valor pode invalidar caches e deixar as respostas mais lentas nessa hora. | Análise do perfil hora a hora e análise de sensibilidade sem as rodadas das 12h às 14h. | Parcial |
| **Agendamento irregular:** o GitHub pode atrasar ou pular execuções em horários de pico, e um período pode ficar com menos rodadas. | O horário real fica registrado em cada linha, e contamos as rodadas por hora antes da análise. | Mitigada |
| **Eventos isolados:** manutenção, incidente ou mudança na API durante a coleta. | Registro de falhas (M2) e gráfico da latência por data, para achar mudanças de nível. Dias com incidente entram em uma análise de sensibilidade. | Parcial |

### Validade de construto

| Ameaça | Mitigação | Status |
| --- | --- | --- |
| **Latência no cliente não é tempo de servidor:** inclui DNS, conexão TLS e o trajeto de rede. | Declaramos que medimos a experiência de quem consome a API, e não o desempenho isolado do servidor. | Aceita |
| **Um único endpoint leve:** a consulta "último valor da série 1" retorna 40 bytes e pode não representar consultas pesadas, como 10 anos de uma série. | A pergunta é sobre esse tipo de consulta, a mais comum em integrações de cotação. Isso fica declarado como limite. | Aceita |
| **"Horário comercial" é um corte arbitrário:** 09h–18h é uma convenção. | O perfil hora a hora mostra se a conclusão depende do corte escolhido. | Parcial |
| **Viés de mono-métrica:** uma única medida não representa "desempenho". | Três dependentes: mediana (M3), cauda (M4) e disponibilidade (M5). | Mitigada |

### Validade externa

| Ameaça | Mitigação | Status |
| --- | --- | --- |
| **Um único ponto de medição:** a máquina do GitHub fica fora do Brasil, e um usuário brasileiro tem outra rota de rede. | Declaramos o limite. O resultado mostra se a API muda ao longo do dia, mas os valores absolutos de latência não valem para todos os usuários. | Aceita |
| **Duas semanas no fim do ano:** não capturam efeitos de fim de mês, sazonalidade nem a demanda de outras épocas. | Declaramos o limite e indicamos uma coleta mais longa como trabalho futuro. | Aceita |
| **Uma versão da API:** o BCB pode mudar a infraestrutura depois do estudo. | Registramos as datas da coleta. | Aceita |

## O que fica para depois

- **Plano de análise (próxima Issue):** confirmar o teste da hipótese principal e a estimativa
  de poder.
- **Revisão na Sprint 3:** atualizar o status das ameaças com os dados reais. Por exemplo,
  verificar se as 13h realmente se destacam, se faltaram rodadas em alguma hora e se houve
  incidentes.
