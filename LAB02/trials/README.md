# Armazenamento dos resultados dos trials

Esta pasta preserva os artefatos brutos do experimento do LAB02. O identificador
de um trial e a tripla `participant_id`, `kata_id` e `treatment`; por exemplo,
`P1`, `K1`, `IA`.

## Estrutura por trial

Cada participante cria uma copia do kata antes de iniciar o cronometro:

```text
LAB02/trials/
├── dados_trials.csv
├── metricas_estaticas.csv
└── P1/
    └── K1_IA/
        ├── README.md
        ├── solution.py
        └── test_kata_01.py
```

Somente `solution.py` pode ser alterado durante o trial. Depois do termino, a
solucao deve ser preservada para que as metricas estaticas sejam calculadas
sobre o mesmo codigo que gerou os resultados funcionais.

## `dados_trials.csv`

Possui uma linha por trial e e preenchido por `scripts/run_trial.py`. Campos:

| Campo | Formato e regra |
| --- | --- |
| `participant_id` | `P1`, `P2` ou `P3` |
| `kata_id` | `K1` a `K4` |
| `treatment` | `IA` ou `MANUAL` |
| `order` | inteiro de 1 a 4 |
| `start_time`, `end_time` | ISO 8601 com fuso horario |
| `duration_seconds` | inteiro; 2100 em trial censurado |
| `time_to_green_seconds` | inteiro ou vazio quando censurado |
| `time_box_seconds` | 2100 |
| `censored` | `true` ou `false` |
| `tests_total`, `tests_passed`, `tests_failed` | inteiros da execucao final do pytest |
| `prompts_count` | inteiro; `0` para MANUAL |
| `python_version`, `pytest_version` | versoes efetivamente usadas |
| `assistant_name`, `assistant_version` | `none` para MANUAL |
| `notes` | observacoes, interrupcoes ou desvios do protocolo |

## `metricas_estaticas.csv`

Possui uma linha para a versao final de cada trial. E preenchido por
`scripts/collect_static_metrics.py` com Radon 6.0.1 e JSCPD 5.2.0.

- `loc`, `lloc`, `sloc`, `comments` e `blank`: metricas brutas do Radon.
- `complexity_*`: resumo da complexidade ciclomática por funcao.
- `duplicate_lines` e `duplicate_percentage`: duplicacao detectada pelo JSCPD.
- `source_path`, `analyzed_at` e as versoes das ferramentas permitem auditar a
  origem da medicao.

O script recusa gravar duas vezes a mesma tripla participante/kata/tratamento.
Se uma coleta precisar ser refeita por erro de ambiente, mantenha o registro
anterior e documente a decisao em `notes` do trial ou no historico do Git.

O esquema foi congelado na Sprint 1 pela Issue #26, antes do inicio dos trials,
para que todos os participantes produzam registros comparaveis.

## Regras de integridade

- Os CSVs usam UTF-8, cabecalho na primeira linha e virgula como separador.
- Valores ausentes usam campo vazio; nao use `N/A`, `-` ou texto livre em
  colunas numericas.
- Nao invente dados para preencher os templates.
- Nao substitua um trial concluido por uma segunda tentativa; registre qualquer
  desvio do protocolo.
