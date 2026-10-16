# Próximos passos — Sprint 2 (papel B)

## 1. Se precisar parar e continuar em outra máquina

1. Pare o pipeline com `Ctrl+C` (seguro — o cache só grava arquivo completo, nunca pela metade).
2. Copie a pasta inteira `Laboratorios-master\LAB03` para a outra máquina (pendrive,
   OneDrive, Google Drive). Não precisa levar `.pytest_cache\` (é só cache de testes).
   As pastas importantes de levar são:
   - `cache\` (releases, commits_entre_releases, etc.) — é o que permite retomar sem
     refazer chamadas já feitas;
   - `dados\` e `resultados\`;
   - `config.yaml`.
3. Na máquina nova:
   ```powershell
   cd "caminho\para\Laboratorios-master\LAB03"
   pip install -r requirements.txt
   $env:GITHUB_TOKEN = "seu_token"   # gere um novo se o antigo expirou; nunca cole em chat/e-mail
   python -m pytest                  # confirma que o ambiente está ok
   python -m pipeline --config config.yaml   # retoma de onde parou
   ```

## 2. Quando as etapas 7 e 8 terminarem (rodada de teste com 100 repos)

Isso só confirma que o pipeline funciona. **Ainda não é a entrega da Sprint 2.** Depois disso:

### 2.1. Alinhar com o grupo (A e C)

- [ ] Confirmar quem vai rodar a coleta ampliada para `n_repos >= 300` em `config.yaml`
      (sugestão: um só do grupo roda e compartilha `cache\`/`dados\`/`resultados\`
      com os outros dois, em vez de cada um rodar do zero).
- [ ] Confirmar o sorteio da amostra-ouro (60 repositórios, seed fixa) — gerado com
      `pipeline/amostra_ouro.py` sobre a amostra final (300+), não sobre esta amostra
      de teste de 100.
- [ ] Combinar prazo para as 3 planilhas de rótulos (você, A e C) ficarem prontas.

### 2.2. Sua parte manual (intransferível)

- [ ] Rotular, sozinho, sem ver a heurística automática nem os colegas, os 60
      repositórios sorteados: tipo do projeto, se releases representam entrega
      real, e se cada uma de 5 releases sorteadas por repositório é corretiva.
- [ ] Commitar sua planilha de rótulos em uma Issue própria.
- [ ] Depois que A consolidar o consenso dos 3: rodar `metricas.cfr.avaliar_heuristica`
      com os rótulos reais. Se o F1 ficar abaixo de 0,70, pedir para refinar
      `metricas/cfr.py` e documentar a nova versão testada.

### 2.3. Git / Processo (regra da seção 10 do enunciado — sem isso a nota zera)

- [ ] Abrir as duas Issues no GitHub Projects — texto já pronto em
      [`artigo/issue_e_commit_template.md`](artigo/issue_e_commit_template.md)
      (uma para a heurística CFR b, outra para a rotulagem da amostra-ouro),
      marcar-se como Assignee, mover para "In Progress".
- [ ] Commitar citando o número de cada Issue — comandos prontos no mesmo
      arquivo [`artigo/issue_e_commit_template.md`](artigo/issue_e_commit_template.md)
      (só trocar `[NUMERO_ISSUE_1]`/`[NUMERO_ISSUE_2]` pelos números reais).
- [ ] Conferir na aba **Actions** que o workflow `lab03-testes` ficou verde.
- [ ] Comentar nas Issues o que foi feito (saída do pytest, link da execução do CI),
      mover para "Done" e fechar.

### 2.4. Artigo (sua parte da metodologia)

- [ ] Preencher [`artigo/metodologia_cfr.md`](artigo/metodologia_cfr.md) — casca
      pronta do trecho de metodologia sobre a definição operacional de CFR (b)
      e sua validação (precisão/recall/F1), só faltam os `[VALORES]` e os
      parágrafos de discussão/ameaça à validade. Fazer por último, depois do
      passo 2.2 estar pronto — o texto precisa citar o F1 obtido.
- [ ] Preencher [`artigo/versoes_heuristica_cfr.md`](artigo/versoes_heuristica_cfr.md)
      — tabela exigida pela seção 6 do enunciado com as versões testadas da
      heurística e o F1 de cada uma (a v1 já está descrita, só falta o número).
- [ ] Colar o conteúdo final de `metodologia_cfr.md` dentro da seção de
      Metodologia do artigo principal (template SBC).
