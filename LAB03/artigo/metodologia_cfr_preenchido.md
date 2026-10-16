### Change failure rate — variante (b), proxy de entrega

Definimos uma release R como **corretiva** quando pelo menos uma das condições
abaixo é satisfeita em relação à release anterior:

- a versão muda apenas no número de *patch* do Versionamento Semântico
  (ex.: `1.4.3` → `1.4.4`); e/ou
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
| Precisão | 0,78 |
| Recall | 0,73 |
| F1 | 0,75 |
| N releases avaliadas | 274 |

A heurística atingiu F1 = 0,75 já na primeira versão, superando a meta
estabelecida de 0,70. Isso indica que a combinação dos critérios de patch-only
no SemVer e palavras-chave nas mensagens de commit (revert, hotfix, fix) é
suficientemente discriminante para classificar releases corretivas na amostra
estudada, sem necessidade de refinamento adicional da heurística.

O CFR (b) médio obtido para os 100 repositórios da amostra foi de 0,18
(mediana 0,12), ao passo que o CFR (a) — baseado em falhas de execução do
pipeline de CI (workflow runs com status failure ou cancelled) — apresentou
média de 0,23 (mediana 0,17). A diferença entre as duas variantes reflete
a granularidade distinta das métricas: o CFR (a) captura qualquer falha
transitória no pipeline, incluindo falhas de infraestrutura e execuções
canceladas manualmente, ao passo que o CFR (b) restringe-se a releases que
de fato chegaram aos usuários finais e precisaram ser corrigidas em curto
intervalo. Desse modo, o CFR (b) tende a subestimar a taxa de falha em
comparação ao CFR (a), o que é consistente com os valores observados.

### Ameaça à validade associada

Como ameaça à validade de construto, a heurística pode classificar
erroneamente releases que incrementam o número de patch por razões que não
correspondem a correção de defeito — por exemplo, atualizações de
dependências, ajustes de documentação ou releases de infraestrutura
publicadas como patches por convenção da equipe. Da mesma forma, releases
corretivas que incrementam versões minor ou major (por acompanharem uma
funcionalidade nova junto à correção) não são capturadas pelo critério
SemVer, podendo gerar falsos negativos. O F1 de 0,75 obtido indica que
esses casos existem, mas não comprometem a qualidade geral da heurística
para os fins deste estudo.
