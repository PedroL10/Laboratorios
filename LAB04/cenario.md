# Cenário

## Pergunta

O tempo até o merge dos PRs do HPX mudou depois que o projeto adotou o bot de revisão
CodeRabbit?

## Hipóteses

| | Em palavras | t de Welch | Mann-Whitney |
| --- | --- | --- | --- |
| H₀ | O tempo até o merge é o mesmo antes e depois do bot. | As médias são iguais. | Um PR de um grupo tem a mesma chance de demorar mais ou menos que um PR do outro grupo. |
| H₁ | O tempo até o merge mudou depois do bot. | As médias são diferentes. | Os PRs de um grupo tendem a demorar mais que os do outro. |

- **Teste bicaudal.** O bot pode acelerar o merge, porque antecipa parte da revisão, ou
  atrasá-lo, porque gera comentários que o autor precisa responder. Não há motivo para
  descartar nenhum dos dois sentidos antes de olhar os dados.
- **Nível de significância:** α = 0,05.
- **O que cada teste compara:** o t de Welch compara as médias e não supõe variâncias
  iguais. O Mann-Whitney compara os postos, ou seja, a posição de cada PR quando os 60
  tempos são ordenados.

## Dados reais

60 PRs mergeados do repositório `TheHPXProject/hpx`, 30 abertos antes da adoção do
CodeRabbit (março a maio de 2026) e 30 depois (julho a setembro de 2026). A coleta e as
limitações estão em [dados/README.md](dados/README.md).

## Como os dados simulados são gerados

A análise da forma da distribuição mostrou dados assimétricos e não normais. A Gamma e a
Weibull empatam como melhores ajustes, e a lognormal fica atrás.

| Uso | Distribuição | Parâmetros | Origem |
| --- | --- | --- | --- |
| G1 e teste de exemplo | Melhor ajuste de cada grupo | `sem_bot`: Weibull (forma 1,07; escala 41,35 h). `com_bot`: Gamma (forma 1,25; escala 54,52 h). | Ajuste de cada grupo real |
| Erro tipo I e poder | Gamma, igual para os dois grupos | Forma 1,07; escala 50,59 h | Ajuste da amostra inteira |

- **H₀ verdadeira:** os dois grupos vêm da mesma Gamma.
- **Efeito:** os tempos do grupo `com_bot` são multiplicados por um fator. O fator 1 é a
  ausência de efeito. Os fatores simulados vão de 1 a 2,5. Nos dados reais, a média de
  `com_bot` é 1,68 vez a de `sem_bot`.
- **Por que um fator multiplicativo:** em `com_bot`, o desvio padrão cresce junto com a
  média, e o coeficiente de variação fica parecido. Isso indica uma mudança de escala, e
  não uma soma de horas.

### Situações que violam os pressupostos do t de Welch

| Situação | Distribuição | n por grupo | O que viola |
| --- | --- | --- | --- |
| Ajuste real (n=30) | Gamma (forma 1,07; escala 50,59 h) | 30 | Nada: é a situação de referência, próxima dos dados reais |
| Amostra pequena (n=10) | Mesma Gamma | 10 | Com poucos dados, a aproximação usada pelo t de Welch fica pior |
| Cauda pesada (lognormal, forma=2.5) | Lognormal (σ do log = 2,5; mediana 41,8 h) | 30 | Assimetria e outliers bem mais extremos que os reais |

## Expectativa do grupo

Registrada em 12/11/2026, antes das simulações de poder. As taxas de erro tipo I já
tinham sido calculadas.

- **Erro tipo I:** os dois testes devem ficar perto de 5% na situação calibrada. Com cauda
  pesada, o t de Welch deve ficar abaixo de 5% (conservador), porque os outliers inflam o
  desvio padrão e reduzem a estatística t.
- **Poder:** o Mann-Whitney deve detectar o efeito com mais frequência que o t de Welch.
  Em dados assimétricos, poucos PRs muito demorados dominam a média e o desvio padrão, e
  isso esconde o efeito no t de Welch. O Mann-Whitney usa só a ordem dos tempos, então
  esses PRs pesam o mesmo que os outros.
- **Onde a vantagem deve ser maior:** na cauda pesada. Com amostra pequena, os dois testes
  devem perder poder, e a diferença entre eles deve diminuir.
