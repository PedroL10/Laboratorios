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

A análise da forma da distribuição mostrou dados assimétricos e não normais. Gamma e
Weibull têm AICs muito próximos nos dois grupos e na amostra inteira. A lognormal ajusta
pior o grupo `sem_bot` e a amostra inteira, mas fica próxima da Gamma em `com_bot`.

| Uso | Distribuição | Parâmetros | Origem |
| --- | --- | --- | --- |
| G1 e teste de exemplo | Melhor ajuste de cada grupo | `sem_bot`: Weibull (forma 1,07; escala 41,35 h). `com_bot`: Gamma (forma 1,25; escala 54,52 h). | Ajuste de cada grupo real |
| Erro tipo I e poder | Gamma, igual para os dois grupos | Forma 1,07; escala 50,59 h | Ajuste da amostra inteira |

Os ajustes usam máxima verossimilhança, com localização fixada em zero nas distribuições
positivas. Os valores acima estão arredondados; o código usa os parâmetros completos
reajustados a partir do CSV real.

O G1 e o teste de exemplo preservam as diferenças observadas entre os grupos. Para medir
erro tipo I e poder, usamos uma única distribuição base, ajustada aos 60 PRs juntos:
assim, quando não há efeito, os grupos têm a mesma distribuição e H₀ é verdadeira para
ambos os testes. Reutilizar os dois ajustes distintos do G1 nessa etapa já introduziria
uma diferença entre os grupos antes de aplicar o efeito controlado.

- **H₀ verdadeira na situação de referência:** os dois grupos vêm da mesma Gamma. Nas
  demais situações, os dois vêm da mesma distribuição especificada na tabela abaixo.
- **Efeito:** os tempos do grupo `com_bot` são multiplicados por um fator. O fator 1 é a
  ausência de efeito, equivalente a efeito zero. Os fatores simulados são 1; 1,25; 1,5;
  1,75; 2 e 2,5. Nos dados reais, a média de `com_bot` é 1,68 vez a de `sem_bot`.
- **Por que um fator multiplicativo:** em `com_bot`, o desvio padrão cresce junto com a
  média, e os coeficientes de variação ficam próximos (0,96 com bot e 0,84 sem bot).
  Esse padrão motivou modelar uma mudança de escala, em vez de somar horas.
- **Reprodutibilidade:** 10.000 pares de amostras por combinação de situação e fator,
  semente 42 e α = 0,05. As linhas com fator 1 fornecem o erro tipo I; as demais medem o
  poder.

### Situações que violam os pressupostos do t de Welch

| Situação | Distribuição | n por grupo | O que viola |
| --- | --- | --- | --- |
| Ajuste real (n=30) | Gamma (forma 1,07; escala 50,59 h) | 30 | Nada: é a situação de referência, próxima dos dados reais |
| Amostra pequena (n=10) | Mesma Gamma | 10 | Com poucos dados, a aproximação usada pelo t de Welch fica pior |
| Cauda pesada (lognormal, forma=2.5) | Lognormal (σ do log = 2,5; mediana 41,8 h) | 30 | Assimetria e outliers bem mais extremos que os reais |

O caso de cauda pesada é um teste de estresse, não um ajuste aos PRs reais: preserva a
mediana da amostra inteira, mas usa σ do log = 2,5 para exagerar a dispersão e os outliers.
As sugestões iniciais e a escolha final estão distinguidas em
[dados/README.md](dados/README.md#da-sugestão-inicial-à-simulação-final).

## Expectativa do grupo

O cenário foi registrado no commit `47aaa92`, de 12/11/2026 às 15h10, depois do commit
`6d6ddd9` de erro tipo I, às 14h30, e antes do commit `9964e90` de poder, às 15h48
(horário de Brasília). Essa sequência de commits é compatível com o registro antes da
etapa de poder, mas não comprova que nenhuma simulação de poder havia sido executada
localmente. As taxas de erro tipo I já tinham sido calculadas.

**Limitação metodológica:** o repositório não contém registro da expectativa anterior a
todas as simulações, como pede o enunciado. Por isso, a afirmação sobre erro tipo I abaixo não
deve ser tratada como previsão independente dos resultados; a comparação da expectativa
com o poder usa o registro disponível nessa etapa. Mantemos a cronologia original, sem
atribuir uma data anterior ao que foi documentado.

- **Erro tipo I:** os dois testes devem ficar perto de 5% na situação calibrada. Com cauda
  pesada, o t de Welch deve ficar abaixo de 5% (conservador), porque os outliers inflam o
  desvio padrão e reduzem a estatística t.
- **Poder:** o Mann-Whitney deve detectar o efeito com mais frequência que o t de Welch.
  Em dados assimétricos, poucos PRs muito demorados dominam a média e o desvio padrão, e
  isso esconde o efeito no t de Welch. O Mann-Whitney usa só a ordem dos tempos, então
  esses PRs pesam o mesmo que os outros.
- **Onde a vantagem deve ser maior:** na cauda pesada. Com amostra pequena, os dois testes
  devem perder poder, e a diferença entre eles deve diminuir.
