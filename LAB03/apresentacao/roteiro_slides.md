# Roteiro da apresentação — LAB03: Mineração de métricas DORA

Cerca de 12 slides, para 10–15 minutos. Cada slide traz o conteúdo, a figura ou
tabela de onde ele vem e uma nota de fala. `[colchetes]` = valor que sai dos
resultados da coleta (arquivos em `resultados/`).

---

## 1. Título

**Velocidade e estabilidade em projetos open-source: mineração das métricas DORA no GitHub**
LAB03 — Laboratório de Experimentação de Software · nomes · data

---

## 2. O problema

- As métricas DORA são o padrão para medir entrega de software: **frequência de
  deploy, lead time, change failure rate e tempo de recuperação**.
- O GitHub **não registra deploys nem falhas em produção**.
- Então medimos **proxies**: release ≈ deploy; CI com falha ≈ falha.
- Pergunta central: *qual é o valor da métrica* — e *o quanto podemos confiar nele?*

> Fala: o trabalho não é só calcular quatro números, é medir o quanto eles
> dependem das escolhas que fazemos para aproximá-los.

---

## 3. Questões de pesquisa

| RQ | Pergunta |
| --- | --- |
| 01–04 | Frequência, lead time, CFR e tempo de recuperação dos repositórios |
| 05 | Mais deploys ↔ mais ou menos falhas? |
| 06 | Que características se associam a melhor desempenho? |
| 07 | A classificação DORA muda se mudarmos a definição? |
| 08 | (bônus) Rework rate |

---

## 4. Pipeline de coleta

Diagrama: busca → filtro de Actions → critério de inclusão → releases →
commits entre releases → workflow runs → tags → dataset → análises.

- Script próprio (`requests`, sem PyGithub), um único comando.
- **Cache e retomada**: interrompeu, roda de novo e continua.
- **Rate limit** com espera automática; **backoff** exponencial para 5xx.
- Testes com pytest (100% de cobertura nas métricas) e CI no GitHub Actions.

> Fala: citar o volume — 22.100 releases, mais de 477 mil runs, dezenas de
> milhares de chamadas à API.

---

## 5. Funil de seleção

Tabela (de `resultados/funil_selecao.md`):
**2.000 → 1.727 → 646 → 347 → 300**

- Janela: 01/10/2025 a 30/09/2026.
- Critério: ≥ 5 releases e ≥ 50 runs válidos no default branch.
- Amostra: mediana de 63 mil estrelas, 473 contribuidores, 6 anos de idade;
  TypeScript (80), Python (72), Rust (32), Go (32).

---

## 6. Desafios técnicos e decisões

- **Teto de 1.000 runs por consulta** → janela fatiada por mês, e meses
  cheios divididos ao meio. 130 repositórios estavam no teto.
- **Tags sem data** → API GraphQL, tags ordenadas pela data do commit.
- **Release anterior fora da janela** → usada como base do compare (bug
  encontrado e corrigido nos testes).
- **Coleta lenta** → cache compartilhado de compares e 8 repositórios em
  paralelo: de ~30 h estimadas para ~9 h.
- **Censura** → falhas não recuperadas e releases dos últimos 7 dias contadas
  à parte, não descartadas.

> Fala: este slide mostra engenharia, vale a pena.

---

## 7. RQ 01–04: distribuições

Figura: `resultados/rq01_04/figuras/distribuicoes.png`

| Métrica | Mediana | IQR |
| --- | --- | --- |
| Frequência (releases/semana) | [ ] | [ ] |
| Lead time (a) / (b) (dias) | [ ] / [ ] | [ ] |
| CFR (a) / (b) | [ ] / [ ] | [ ] |
| Recuperação (horas) | [ ] | [ ] |

> Fala: destacar a diferença entre lead time (a) e (b) e entre CFR (a) e (b).

---

## 8. Classificação DORA (C1)

Figura: `resultados/rq01_04/figuras/classificacao_c1.png`

- [% Elite / High / Medium / Low na classificação geral]
- [Qual métrica puxa os repositórios para cima e qual puxa para baixo]

---

## 9. RQ 05: velocidade × estabilidade

Figura: `resultados/rq05/figuras/dispersao.png`

- CFR (a): ρ = [ ], p [ ] · CFR (b): ρ = [ ], p [ ]
- O DORA diz que velocidade e estabilidade não são um *trade-off*. Os dados
  [confirmam / contradizem]?
- Correlação ≠ causalidade.

---

## 10. RQ 06: o que se associa a melhor desempenho

Figura: `resultados/rq06/figuras/efeitos.png`

- 4 fatores × 4 métricas = 16 testes, correção de Holm.
- [Diferenças significativas e tamanho de efeito — ver `testes.md` e `medianas.md`]

---

## 11. RQ 07: a classificação depende da definição?

Figuras: `resultados/rq07/figuras/distribuicao.png` e `transicoes.png`

- C1 release/(a)/(a) · C2 release+pré-release/(b)/(b) · C3 tag/(b)/(a)
- [% de repositórios que mudam de categoria e kappa ponderado por par]
- Mensagem: [as conclusões são robustas / dependem da definição]

> Fala: este é o resultado mais importante do trabalho — mostra o quanto podemos
> confiar no proxy.

---

## 12. Ameaças à validade e limitações

- Release ≠ deploy; falha de CI ≠ falha em produção.
- Heurística de release corretiva [validada com F1 = [ ] / ainda não validada
  manualmente].
- Amostra só de repositórios muito populares (> 41 mil estrelas).
- Repositórios criados dentro da janela (49) e workflows auxiliares.

---

## 13. Conclusão e próximos passos

- [3 mensagens principais dos resultados]
- Próximos passos: validação manual da heurística; replicação do pipeline por
  outro grupo (entrega final).
- Repositório: https://github.com/PedroL10/Laboratorios

---

## Slides reserva (perguntas)

- Dicionário de dados (`resultados/dicionario_dados.md`).
- Tabela completa da RQ 06 (`resultados/rq06/testes.md`).
- Censura e dados ignorados (`resultados/rq01_04/censura.md`).
- RQ 08: rework rate × CFR (b) (`resultados/rq08/rework.md`).
