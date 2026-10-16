<!--
Trecho de metodologia sobre a definicao operacional de CFR (b) e sua validacao.
Preencher os campos [ENTRE COLCHETES] depois que os dados reais existirem.
Depois de pronto, colar dentro da secao "Metodologia" do artigo principal (template SBC).
-->

### Change failure rate — variante (b), proxy de entrega

Definimos uma release R como **corretiva** quando pelo menos uma das condições
abaixo é satisfeita em relação à release anterior:

- a versão muda apenas no número de *patch* do Versionamento Semântico
  (ex.: `[EXEMPLO_PATCH_ANTERIOR]` → `[EXEMPLO_PATCH_ATUAL]`); e/ou
- há commits com `revert`, `hotfix` ou `fix` na mensagem entre as duas releases.

O CFR (b) do repositório é a proporção de releases avaliadas que **falharam**,
onde uma release falha se for seguida, em até 7 dias, por uma release
corretiva. Releases publicadas nos últimos 7 dias da janela de observação não
são avaliadas (censura).

**Validação da heurística.** Comparamos a classificação automática com o
rótulo de consenso dos três integrantes sobre a amostra-ouro de 60
repositórios (seção de Validação Manual):

| Métrica | Valor |
| --- | --- |
| Precisão | `[PRECISAO]` |
| Recall | `[RECALL]` |
| F1 | `[F1]` |
| N releases avaliadas | `[N_RELEASES_AVALIADAS]` |

[PREENCHER: um parágrafo dizendo se o F1 atingiu a meta de 0,70. Se não
atingiu na primeira versão, descrever o que foi ajustado — ver
`versoes_heuristica_cfr.md` — e o F1 final obtido.]

[PREENCHER: um parágrafo discutindo em que o CFR (b) (proxy de entrega) difere
do CFR (a) (proxy de CI, seção 3), citando os valores de ambos se já
calculados.]

### Ameaça à validade associada

[PREENCHER: um parágrafo de construto — ex.: a heurística pode classificar
erroneamente releases que mudam o patch por motivos que não são correção de
defeito (ex.: apenas atualização de dependência), ou deixar de identificar
releases corretivas que mudam minor/major. Apoiar no F1 obtido acima.]
