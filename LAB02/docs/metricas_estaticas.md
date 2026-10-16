# LAB02S01 — Coleta de metricas estaticas

Para responder a RQ3, cada `solution.py` final sera analisado com as mesmas
versoes de ferramenta:

- **Radon 6.0.1:** LOC e complexidade ciclomática.
- **JSCPD 5.2.0:** linhas e percentual de duplicacao.

LOC e registrado como variavel de controle: diferencas de complexidade ou de
duplicacao devem ser interpretadas junto com o tamanho da solucao.

## Preparacao

Na pasta `LAB02`, instale as dependencias antes dos trials:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm install
```

No Windows, use `.venv\\Scripts\\activate` no lugar de `source`.

## Coleta depois de um trial

Execute o comando uma vez, sem alterar a solucao final:

```bash
python scripts/collect_static_metrics.py \
  --participant P1 --kata K1 --treatment IA \
  --trial-dir trials/P1/K1_IA
```

O registro sera acrescentado em `trials/metricas_estaticas.csv`. O comando
falha se a mesma combinacao de participante, kata e tratamento ja existir,
protegendo o dado original contra sobrescrita acidental.

## Criterio de analise

Para cada tratamento, o relatorio apresentara mediana e IQR de LOC,
complexidade e duplicacao. Como cada participante executa ambos os
tratamentos, a comparacao inferencial planejada para a RQ3 e o teste de
Wilcoxon pareado, se a quantidade de dados permitir.
