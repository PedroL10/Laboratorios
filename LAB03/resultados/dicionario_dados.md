# Dicionario de dados — `resultados/amostra_metricas.csv`

Uma linha por repositorio da amostra. Gerado por `pipeline/dataset.py`, a partir
de `DICIONARIO`. Valor vazio = metrica sem dado para o repositorio (ex.: nenhum
episodio de falha encerrado na janela). Datas em UTC. A janela de observacao e a
do `config.yaml`, com inicio e fim inclusivos.

| Coluna | Tipo | Unidade | Formula / origem |
| --- | --- | --- | --- |
| `full_name` | texto | - | `owner/nome` do repositorio (`full_name` da busca) |
| `owner` | texto | - | Dono do repositorio (`owner.login`) |
| `name` | texto | - | Nome do repositorio (`name`) |
| `stargazers_count` | inteiro | estrelas | Estrelas no momento da busca (`stargazers_count`) |
| `language` | texto | - | Linguagem principal segundo o GitHub (`language`); vazio se nao detectada |
| `created_at` | data-hora ISO 8601 (UTC) | - | Criacao do repositorio (`created_at`) |
| `default_branch` | texto | - | Branch principal (`default_branch`); o unico considerado |
| `archived` | booleano | - | Repositorio arquivado (`archived`) |
| `fork` | booleano | - | Repositorio e fork (`fork`) |
| `html_url` | texto | - | Endereco do repositorio no GitHub (`html_url`) |
| `n_runs_push` | inteiro | runs | `total_count` de `actions/runs?event=push&branch=<default>&created=<janela>` (criterio de inclusao) |
| `n_runs_validos` | inteiro | runs | Runs de push com `conclusion` de sucesso ou falha na janela (criterio de inclusao); limite inferior se `runs_no_teto` |
| `runs_no_teto` | booleano | - | `n_runs_push` atingiu o teto de 2.500 do `total_count` da API (contagens do criterio sao limites inferiores) |
| `n_contribuidores` | inteiro | pessoas | Contribuidores, inclusive anonimos: ultima pagina de `contributors?per_page=1&anon=true` |
| `erro_contribuidores` | texto | - | Motivo de `n_contribuidores` vazio (ex.: lista grande demais para a API); vazio se contou |
| `idade_dias` | inteiro | dias | Fim da janela - `created_at` |
| `deployment_frequency` | decimal | releases/semana | RQ 01: `n_releases_janela / semanas_janela` |
| `n_releases_janela` | inteiro | releases | Releases publicadas (`draft = false`, `prerelease = false`) com `published_at` na janela |
| `semanas_janela` | decimal | semanas | Dias da janela (inclusive) / 7 = 52,14 |
| `lead_time_release_dias` | decimal | dias | RQ 02 (a): mediana, entre as releases da janela, de `published_at` - `commit.author.date` do commit mais antigo da release (`compare/<anterior>...<release>`) |
| `lead_time_commit_dias` | decimal | dias | RQ 02 (b): mediana de `published_at` - `commit.author.date` de todos os commits de todas as releases da janela |
| `n_releases_variante_a` | inteiro | releases | Releases com ao menos um commit novo, usadas na variante (a) |
| `n_commits_variante_b` | inteiro | commits | Commits usados na variante (b) |
| `n_ignoradas_primeira_release` | inteiro | releases | 1 se a primeira release da historia do repositorio esta na janela (sem release anterior para comparar); 0 caso contrario |
| `n_ignoradas_compare_404` | inteiro | releases | Releases da janela ignoradas porque o `compare` devolveu 404 (tag apagada ou reescrita) |
| `cfr_entrega` | proporcao (0 a 1) | - | RQ 03 (b): `n_releases_falhas / n_releases_avaliadas`; release falha se a seguinte, em ate 7 dias, e corretiva pela heuristica (`metricas.cfr`) |
| `n_releases_avaliadas` | inteiro | releases | Releases da janela avaliadas no CFR (b) (exclui as censuradas) |
| `n_releases_falhas` | inteiro | releases | Releases seguidas, em ate 7 dias, por uma release corretiva |
| `n_releases_censuradas` | inteiro | releases | Releases publicadas nos ultimos 7 dias da janela, fora do denominador do CFR (b) |
| `cfr_ci` | proporcao (0 a 1) | - | RQ 03 (a): `n_runs_falha / (n_runs_falha + n_runs_sucesso)`, runs de push no default branch na janela |
| `n_runs_falha` | inteiro | runs | Runs com `conclusion` em failure, timed_out ou startup_failure |
| `n_runs_sucesso` | inteiro | runs | Runs com `conclusion` = success |
| `n_runs_ignorados` | inteiro | runs | Runs com outro `conclusion` (cancelled, skipped, neutral, action_required, stale ou vazio) |
| `fatias_no_teto` | inteiro | dias | Dias com mais de 1.000 runs (teto de uma consulta filtrada): runs desses dias estao incompletos |
| `tempo_recuperacao_horas` | decimal | horas | RQ 04: mediana dos episodios de todos os workflows; episodio = `updated_at` do sucesso - `run_started_at` da primeira falha apos um sucesso, no mesmo `workflow_id` |
| `n_episodios` | inteiro | episodios | Episodios de falha encerrados na janela |
| `n_episodios_censurados` | inteiro | episodios | Episodios sem sucesso ate o fim da janela (fora da mediana) |
| `proporcao_censurados` | proporcao (0 a 1) | - | `n_episodios_censurados / (n_episodios + n_episodios_censurados)` |
| `n_episodios_sem_inicio` | inteiro | workflows | Workflows que ja comecam a janela falhando (inicio do episodio desconhecido; fora da mediana) |
| `deployment_frequency_pre` | decimal | unidades/semana | Frequencia de deploy, com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `n_unidades_janela_pre` | inteiro | unidades | Unidades de deploy com data na janela, com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `lead_time_release_dias_pre` | decimal | dias | Lead time (a), por unidade, com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `lead_time_commit_dias_pre` | decimal | dias | Lead time (b), por commit, com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `cfr_entrega_pre` | proporcao (0 a 1) | - | CFR (b), com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `n_avaliadas_cfr_pre` | inteiro | unidades | Unidades avaliadas no CFR (b), com unidade de deploy = release + pre-release (toda release que nao e draft) (RQ 07) |
| `deployment_frequency_tag` | decimal | unidades/semana | Frequencia de deploy, com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `n_unidades_janela_tag` | inteiro | unidades | Unidades de deploy com data na janela, com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `lead_time_release_dias_tag` | decimal | dias | Lead time (a), por unidade, com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `lead_time_commit_dias_tag` | decimal | dias | Lead time (b), por commit, com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `cfr_entrega_tag` | proporcao (0 a 1) | - | CFR (b), com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `n_avaliadas_cfr_tag` | inteiro | unidades | Unidades avaliadas no CFR (b), com unidade de deploy = tag (data = committedDate do commit apontado, via GraphQL) (RQ 07) |
| `categoria_frequencia` | categoria | - | Elite/High/Medium/Low de `deployment_frequency` (cortes da RQ 07, `metricas.classificacao`) |
| `categoria_lead_time` | categoria | - | Elite/High/Medium/Low de `lead_time_release_dias` (variante a) |
| `categoria_cfr` | categoria | - | Elite/High/Medium/Low de `cfr_ci` (variante a) |
| `categoria_recuperacao` | categoria | - | Elite/High/Medium/Low de `tempo_recuperacao_horas` |
| `categoria_geral` | categoria | - | Combinacao C1: mediana dos pontos (Elite 4 ... Low 1) das metricas disponiveis, arredondada para baixo |
| `n_metricas` | inteiro | metricas | Quantas das 4 metricas tem valor e entraram em `categoria_geral` |
