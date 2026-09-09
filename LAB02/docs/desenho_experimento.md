# Lab02S01 - Desenho do experimento

## 1. Objetivo

Analisar o efeito do uso de um assistente de IA generativa na resolução de tarefas de programação, comparando o tratamento com IA habilitada ao tratamento de codificação manual sem consulta à IA.

O experimento será realizado por estudantes de graduação, em tarefas de programação de dificuldade comparável, com tempo limitado e coleta padronizada de resultados.

## 2. Questões de pesquisa

- **RQ1:** O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?
- **RQ2:** O uso de assistente de IA reduz a quantidade de defeitos no código produzido?
- **RQ3:** O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?

## 3. Hipóteses

### RQ1 - Tempo de resolução

- **H0_1:** O uso de assistente de IA não altera o tempo necessário para resolver uma tarefa de programação.
- **H1_1:** O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação.

A métrica primária será o tempo até todos os testes de aceitação passarem (`time-to-green`). Um trial que atingir o limite sem sucesso será registrado como censurado em 35 minutos, ou 2100 segundos, e não será descartado.

### RQ2 - Defeitos

- **H0_2:** O uso de assistente de IA não altera a quantidade de defeitos no código produzido.
- **H1_2:** O uso de assistente de IA reduz a quantidade de defeitos no código produzido.

Serão coletados o número de testes de aceitação passando, o número de testes falhando e a taxa de sucesso ao final do time-box.

### RQ3 - Estrutura do código

- **H0_3:** O uso de assistente de IA não altera a estrutura do código produzido.
- **H1_3:** O uso de assistente de IA altera a complexidade ciclomática, a duplicação ou o tamanho do código produzido.

Serão coletadas linhas de código (LOC), complexidade ciclomática e duplicação. LOC será usada como métrica de controle sempre que complexidade ou duplicação forem analisadas.

## 4. Variáveis

### 4.1 Variável independente

O uso de assistente de IA durante a resolução da tarefa, com dois níveis:

- **IA:** assistente de IA habilitado e permitido durante o trial.
- **MANUAL:** assistente de IA desabilitado e não consultado durante o trial.

O mesmo assistente de IA será usado em todos os trials do tratamento IA. O assistente e sua versão serão registrados antes da execução da Sprint 2.

### 4.2 Variáveis dependentes

| RQ  | Variável                 | Forma de medição                              |
| --- | ------------------------ | --------------------------------------------- |
| RQ1 | Time-to-green            | Segundos até todos os testes passarem         |
| RQ1 | Trial censurado          | `true` quando o time-box terminar sem sucesso |
| RQ2 | Testes passando          | Quantidade ao final do trial                  |
| RQ2 | Testes falhando          | Quantidade ao final do trial                  |
| RQ2 | Taxa de sucesso          | Testes passando dividido pelo total de testes |
| RQ3 | LOC                      | Linhas de código do trial                     |
| RQ3 | Complexidade ciclomática | Complexidade média por função/método          |
| RQ3 | Duplicação               | Percentual ou quantidade de linhas duplicadas |

As análises descritivas priorizarão mediana e IQR, devido ao tamanho reduzido da amostra. A análise inferencial planejada será o teste de Wilcoxon para amostras pareadas.

## 5. Tratamentos

Cada participante realizará tarefas nos dois tratamentos:

1. **Tratamento IA:** o assistente de IA poderá ser utilizado durante a implementação.
2. **Tratamento MANUAL:** o participante implementará a solução sem consultar ou utilizar assistente de IA.

Os enunciados, testes de aceitação, linguagem, ambiente e limite de tempo serão mantidos equivalentes entre os tratamentos.

## 6. Objetos experimentais

Serão utilizados quatro katas autorais, identificados como `K1`, `K2`, `K3` e `K4`, documentados em `docs/katas.md`. K1 e K2 foram classificados como fáceis; K3 e K4, como médios. A classificação será validada em um piloto curto antes da execução oficial.

Cada kata deverá possuir:

- enunciado e regras claras;
- definição de entradas e saídas;
- exemplos de comportamento esperado;
- testes automatizados de aceitação;
- estimativa e justificativa de dificuldade;
- solução possível dentro do time-box de 35 minutos.

Será dada preferência a exercícios autorais ou pouco indexados, reduzindo o risco de a IA reproduzir uma solução memorizada de exercícios muito conhecidos.

## 7. Projeto experimental

Será utilizado um desenho **crossover within-subject**, no qual cada participante atua nos dois tratamentos. Assim, cada participante servirá como seu próprio controle, reduzindo o efeito das diferenças individuais de habilidade.

Cada participante resolverá os quatro katas:

- dois katas no tratamento IA;
- dois katas no tratamento MANUAL;
- um trial por kata;
- no máximo 35 minutos por trial.

A distribuição e a ordem final serão definidas na Issue 3. A matriz inicial planejada é:

| Participante | K1     | K2     | K3     | K4     |
| ------------ | ------ | ------ | ------ | ------ |
| P1           | IA     | IA     | MANUAL | MANUAL |
| P2           | MANUAL | MANUAL | IA     | IA     |
| P3           | IA     | MANUAL | IA     | MANUAL |

`P1`, `P2` e `P3` são identificadores provisórios e serão substituídos pelos integrantes reais do grupo. A ordem será contrabalanceada para reduzir o efeito de aprendizado entre os katas.

## 8. Quantidade de medições

Considerando três participantes e quatro katas por participante, serão realizados inicialmente 12 trials:

- 6 trials no tratamento IA;
- 6 trials no tratamento MANUAL.

Cada trial produzirá um registro de tempo, resultado dos testes e métricas estáticas do código final. Caso o grupo tenha quantidade diferente de participantes, a matriz e o total de medições serão atualizados antes da Sprint 2.

## 9. Time-box e regra de encerramento

O limite máximo de cada trial será de **35 minutos**, equivalente a **2100 segundos**.

O trial será encerrado quando ocorrer uma das situações:

1. todos os testes de aceitação passarem, registrando o `time-to-green`; ou
2. o limite de 35 minutos for atingido, registrando o trial como censurado.

Trials censurados continuarão na análise e terão os resultados dos testes registrados ao final do tempo. O tratamento de um trial não poderá ser alterado depois que sua execução começar.

## 10. Dados a serem registrados

Cada registro de trial deverá conter, no mínimo:

- identificador do participante;
- identificador do kata;
- tratamento (`IA` ou `MANUAL`);
- ordem do trial;
- horário de início e término;
- duração em segundos;
- `time-to-green` em segundos, quando houver;
- limite do time-box;
- indicação de censura;
- total de testes;
- testes passando;
- testes falhando;
- quantidade de interações com o assistente, quando aplicável.

Os resultados das métricas estáticas deverão identificar o participante, o kata e o tratamento correspondentes.

## 11. Plano de análise

Para cada RQ, serão comparados os tratamentos IA e MANUAL usando as medições pareadas de cada participante e kata equivalente.

- RQ1: comparar `time-to-green`, considerando 2100 segundos para trials censurados.
- RQ2: comparar taxa de sucesso e quantidade de testes falhando ao final do time-box.
- RQ3: comparar LOC, complexidade ciclomática e duplicação, observando também a relação com LOC.

Serão reportados mediana e IQR por tratamento. O teste de Wilcoxon para amostras pareadas será utilizado na análise inferencial, quando houver dados suficientes para sua aplicação.

## 12. Ameaças à validade

### Validade interna

- **Efeito de aprendizado:** resolver um kata pode melhorar o desempenho em katas posteriores. A ordem será contrabalanceada entre os participantes.
- **Familiaridade com IA:** participantes podem ter níveis diferentes de experiência com o assistente. Essa informação deverá ser registrada para discussão.
- **Familiaridade com os katas:** soluções previamente conhecidas podem reduzir artificialmente o tempo. Serão priorizados katas autorais ou pouco indexados.
- **Vazamento de solução:** enunciados ou soluções não deverão ser compartilhados entre participantes durante a execução.
- **Uso acidental de IA no tratamento MANUAL:** o assistente deverá permanecer desabilitado e o participante não poderá consultar ferramentas de IA nesse tratamento.
- **Diferenças de habilidade:** o desenho within-subject reduz, mas não elimina, esse efeito.

### Validade de construção

- `Time-to-green` pode não representar toda a produtividade, pois uma solução que passa nos testes pode ter baixa qualidade estrutural.
- A quantidade de testes falhando depende da cobertura e da qualidade dos testes de aceitação.
- Métricas estáticas podem não capturar legibilidade ou correção semântica.
- LOC pode aumentar por razões de formatação ou estilo, sem representar pior qualidade.

### Validade externa

- O número reduzido de participantes limita a generalização dos resultados.
- Os resultados podem variar conforme a linguagem, o assistente e sua versão.
- Katas autorais podem não representar tarefas reais de desenvolvimento de software.

### Validade de conclusão

- A amostra pequena reduz o poder estatístico.
- Outliers podem influenciar a interpretação, por isso serão reportados mediana e IQR.
- Trials censurados serão mantidos na análise para evitar favorecer o tratamento com menos falhas.

## 13. Decisões pendentes para as próximas Issues

- revisão coletiva dos nomes, enunciados e testes de aceitação dos quatro katas;
- participantes reais do grupo;
- matriz final de distribuição dos tratamentos;
- assistente de IA e versão utilizada;
- linguagem e versões das ferramentas de métricas estáticas.
