# Lab01Exp

Coleta e analise dos 1.000 repositorios publicos com mais estrelas no GitHub
para o Lab01 de Laboratorio de Experimentacao de Software.

## Estrutura

- `src/collect_repositories.py`: consulta GraphQL propria e exporta a amostra.
- `src/analyze_metrics.py`: calcula as metricas das RQs 01 a 08.
- `src/visualize_metrics.py`: gera os graficos das RQs.
- `src/export_project_snapshot.py`: exporta o estado atual do GitHub Project.
- `data/`: bases coletadas e snapshots do Project.
- `resultados/`: metricas e graficos gerados.

## Preparacao

Requer Python 3.11 ou superior e um token pessoal do GitHub com permissao de
leitura do repositorio. Crie um arquivo `.env` a partir de `.env.example` e
preencha `GITHUB_TOKEN`; esse arquivo nao deve ser versionado.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

## Execucao reproduzivel da Sprint 3

As RQs 01 e 04 dependem de uma data de referencia. Para reproduzir exatamente
os resultados versionados, use `2026-08-24T00:00:00Z`, a data da primeira
analise da Sprint 3:

```bash
python src/analyze_metrics.py --reference-at 2026-08-24T00:00:00Z
python src/visualize_metrics.py
python -m unittest discover -s tests -v
```

O primeiro comando atualiza `resultados/resultados_metricas_1000.json`; o
segundo gera os PNGs em `resultados/graficos/`. A execucao inclui RQ08, uma
comparacao exploratoria entre repositorios com e sem linguagem primaria
informada pelo GitHub.

Para analisar outra data, informe uma data ISO 8601 explicitamente:

```bash
python src/analyze_metrics.py --reference-at 2026-08-27T00:00:00Z
```

## Coleta e snapshot

```bash
# Coleta de 100 repositorios para validacao inicial.
python src/collect_repositories.py 100 json

# Coleta de 1.000 repositorios em CSV.
python src/collect_repositories.py 1000 csv

# Exportacao do estado atual do Project.
python src/export_project_snapshot.py
```

A coleta usa apenas requisicoes HTTP genericas para a API GraphQL oficial do
GitHub; nenhuma biblioteca de terceiros especifica para a API do GitHub e
usada.
