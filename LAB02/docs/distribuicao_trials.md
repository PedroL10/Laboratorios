# LAB02S01 - Distribuicao dos trials

## Objetivo

Definir, antes da Sprint 2, qual tratamento cada participante usara em cada kata e em qual ordem os trials serao executados.

O desenho e crossover within-subject: cada participante resolve os quatro mesmos katas, sendo dois com assistente de IA e dois sem assistente de IA.

## Participantes

Os identificadores abaixo foram definidos pelo grupo e devem ser usados nos registros e nas pastas dos trials.

| Identificador | Integrante |
| ------------- | ---------- |
| P1            | Pedro      |
| P2            | Enrico     |
| P3            | Pericles   |

## Matriz de tratamentos

| Participante | K1                  | K2                  | K3                  | K4                  | Total IA | Total MANUAL |
| ------------ | ------------------- | ------------------- | ------------------- | ------------------- | -------: | -----------: |
| P1           | IA                  | IA                  | MANUAL              | MANUAL              |        2 |            2 |
| P2           | MANUAL              | MANUAL              | IA                  | IA                  |        2 |            2 |
| P3           | IA                  | MANUAL              | IA                  | MANUAL              |        2 |            2 |
| **Total**    | **2 IA / 1 MANUAL** | **1 IA / 2 MANUAL** | **2 IA / 1 MANUAL** | **1 IA / 2 MANUAL** |    **6** |        **6** |

A matriz foi escolhida para garantir que cada participante tenha dois trials em cada tratamento e que o conjunto total tenha a mesma quantidade de trials IA e MANUAL.

## Ordem dos trials

A ordem deve ser registrada antes da execução. A sugestão abaixo alterna ou contrabalanceia os tratamentos e evita que todos os participantes executem a mesma sequência.

| Participante | Ordem 1     | Ordem 2     | Ordem 3 | Ordem 4     |
| ------------ | ----------- | ----------- | ------- | ----------- |
| P1           | K1 - IA     | K3 - MANUAL | K2 - IA | K4 - MANUAL |
| P2           | K3 - IA     | K1 - MANUAL | K4 - IA | K2 - MANUAL |
| P3           | K2 - MANUAL | K4 - MANUAL | K1 - IA | K3 - IA     |

A ordem acima e uma proposta inicial. O grupo pode ajusta-la antes da Sprint 2, mas deve registrar a decisao e manter a mesma ordem durante a coleta.

## Regras de congelamento

Depois que os trials comecarem:

- nao trocar IA por MANUAL ou MANUAL por IA;
- nao trocar o kata de um participante;
- nao alterar a ordem registrada;
- nao substituir um trial ruim por uma nova tentativa;
- nao compartilhar solucoes ou resultados entre participantes que ainda nao executaram seus trials;
- registrar qualquer interrupcao, erro de ambiente ou desvio do protocolo.

Se ocorrer um erro antes do inicio do cronometro, corrija o ambiente e registre o fato. Se ocorrer depois do inicio, preserve o trial e marque o desvio no registro.

## Identificacao das pastas

Cada copia de trial deve usar o identificador do participante, o kata e o tratamento:

```text
LAB02/trials/P1/K1_IA/
LAB02/trials/P1/K3_MANUAL/
```

A ordem tambem deve aparecer no registro dos dados, por exemplo `order=1` para o primeiro trial do participante.

## Checklist antes da Sprint 2

- [x] Os nomes reais foram associados a P1, P2 e P3.
- [ ] Todos confirmaram a matriz de tratamentos.
- [ ] Todos confirmaram a ordem dos trials.
- [ ] Cada participante tem dois trials IA e dois MANUAL.
- [ ] O grupo confirmou 12 trials no total.
- [ ] O grupo confirmou 6 trials IA e 6 MANUAL.
- [ ] A matriz foi registrada no GitHub Project ou na Issue 22.
- [ ] A ordem nao sera alterada durante a coleta.
