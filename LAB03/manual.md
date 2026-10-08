# LAB03 — Manual de contribuição

## 1. Configuração inicial (fazer uma vez)

### 1.1 Pré-requisitos
- Git instalado
- Python 3.11 ou superior (`python --version`)
- Acesso de escrita ao repositório https://github.com/PedroL10/Lab01Exp

### 1.2 Baixar o projeto
Se ainda não tem o repositório:
```bash
git clone https://github.com/PedroL10/Lab01Exp.git
cd Lab01Exp/LAB03
```
Se já tem, atualize:
```bash
git pull origin master
cd LAB03
```

### 1.3 Instalar as dependências
```bash
pip install -r requirements.txt
```

### 1.4 Gerar o seu token do GitHub
Cada integrante usa o PRÓPRIO token (não compartilhe o seu).
1. GitHub → foto → **Settings** → **Developer settings**
2. **Personal access tokens** → **Fine-grained tokens** → **Generate new token**
3. Nome: `lab03-dora` · Validade: 90 dias · Repository access: **Public repositories (read-only)**
4. **Generate token** e copie na hora (começa com `github_pat_`)

### 1.5 Testar se está tudo funcionando
Defina o token no terminal (vale só enquanto o terminal estiver aberto):

| Terminal | Comando |
|---|---|
| Git Bash | `export GITHUB_TOKEN="seu_token"` |
| PowerShell | `$env:GITHUB_TOKEN = "seu_token"` |

Depois, dentro de `LAB03`:
```bash
python -m pipeline --config config.yaml
python -m pytest
```
Esperado: `Requisicoes restantes: 5000/5000` e todos os testes passando.

> O token só é necessário para tasks que chamam a API (coletas).
> Funções de cálculo e seus testes usam fixtures e não precisam de token.

---

## 2. Estrutura do projeto

```
LAB03/
├── pipeline/            # coleta de dados
│   ├── __main__.py      # comando único: python -m pipeline --config config.yaml
│   ├── config.py        # leitura do config.yaml
│   └── github_client.py # cliente da API (token + paginação) — USE ESTE
├── metricas/            # funções de cálculo (lead time, CFR, recuperação...)
├── tests/               # testes com pytest (um arquivo test_*.py por módulo)
├── config.yaml          # janela, nº de repositórios, critérios de inclusão
└── requirements.txt
```

**Onde colocar cada coisa:**
- Código de coleta → um módulo novo em `pipeline/` (ex.: `pipeline/releases.py`)
- Funções de cálculo → `metricas/` (ex.: `metricas/lead_time.py`)
- Testes → `tests/test_<nome_do_modulo>.py`

**Como chamar a API:**
```python
from pipeline.github_client import GitHubClient

client = GitHubClient()  # lê o GITHUB_TOKEN automaticamente
repo = client.get("/repos/owner/nome")
for release in client.get_paginated("/repos/owner/nome/releases"):
    ...
# endpoints que devolvem objeto: informe onde está a lista
for run in client.get_paginated("/repos/owner/nome/actions/runs", items_key="workflow_runs"):
    ...
```

---

## 3. Fluxo de trabalho de cada task

1. **No GitHub Projects:** abra a Issue da task, coloque-se como **Assignee**
   e mova o cartão para **In Progress** (respeite o limite de WIP).
2. **Atualize o código antes de começar:** `git pull origin master`
3. **Implemente** dentro de `LAB03/`.
4. **Escreva os testes** (obrigatório para funções de `metricas/`), usando
   fixtures com resultados que você sabe calcular no papel. Inclua casos de borda.
5. **Rode os testes localmente:**
   ```bash
   python -m pytest --cov=metricas --cov-fail-under=80
   ```
6. **Commit citando o número da Issue:**
   ```bash
   git add <apenas os arquivos da sua task>
   git status            # confira o que vai entrar
   git commit -m "#NUMERO Descrição curta do que foi feito"
   git pull origin master
   git push origin master
   ```
7. **Confira o CI:** aba **Actions** → workflow `lab03-testes` deve ficar verde.
8. **Feche a task:** comente na Issue o que foi feito (com evidência: saída do
   comando, link da execução do CI), mova o cartão para **Done** e feche a Issue.

---

## 4. Regras que afetam a nota

- **Todo commit cita o número da Issue** (`#45 ...`). Commit sem número não é considerado.
- **Cada integrante precisa de pelo menos uma Issue com código commitado por sprint**
  (não vale só escrita). Sem isso, a nota individual da sprint é zerada.
- **Nunca commite o token.** Ele fica só na variável de ambiente.
- **Proibido usar bibliotecas prontas da API do GitHub** (PyGithub etc.).
  Use o `GitHubClient`. pandas, scipy, statsmodels e scikit-learn são permitidos.
- **Nunca use `git add .`** — o repositório tem arquivos de outros labs pendentes.
- **Cobertura mínima de 80%** no módulo `metricas` (o CI falha se ficar abaixo).
- **Mantenha o Projects atualizado:** Issue com Assignee, cartão na coluna certa,
  evolução semanal. Projects desatualizado desconta até 10% da nota.

---

## 5. Problemas comuns

| Erro | Solução |
|---|---|
| `bash: :GITHUB_TOKEN: command not found` | Você está no Git Bash: use `export GITHUB_TOKEN="..."` |
| `Defina a variavel de ambiente GITHUB_TOKEN` | Defina o token de novo nesse terminal |
| `401 Unauthorized` | Token errado ou expirado: gere outro |
| `No module named pipeline` | Rode os comandos de dentro da pasta `LAB03` |
| `No module named yaml` | `pip install -r requirements.txt` |
| `git push` rejeitado | Rode `git pull origin master` e tente de novo |
| CI vermelho | Actions → clique na execução → job `test` → leia o passo que falhou |
