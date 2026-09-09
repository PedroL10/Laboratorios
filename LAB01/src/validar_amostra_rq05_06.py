"""Validacao rapida (Sprint 1) dos campos usados por RQ05 e RQ06.

Consulta uma amostra pequena (5-10 repositorios bem conhecidos, com linguagem
primaria e contagem de issues facilmente conferiveis manualmente no site do
GitHub) e imprime os valores retornados pela query GraphQL, para o
responsavel checar "na mao" antes de integrar ao script unico de coleta
(collect_repositories.py).

Uso:
    python src/validar_amostra_rq05_06.py
"""

from github_client import run_query

AMOSTRA = [
    "torvalds/linux",
    "microsoft/vscode",
    "facebook/react",
    "python/cpython",
    "django/django",
    "golang/go",
    "rust-lang/rust",
    "nodejs/node",
]

QUERY = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    primaryLanguage {
      name
    }
    issues {
      totalCount
    }
    closedIssues: issues(states: CLOSED) {
      totalCount
    }
  }
}
"""


def validar():
    print(f"{'Repositorio':<28} {'linguagem':>14} {'issues_total':>13} {'issues_fechadas':>16} {'%fechadas':>10}")
    for name_with_owner in AMOSTRA:
        owner, name = name_with_owner.split("/")
        data = run_query(QUERY, {"owner": owner, "name": name})["repository"]
        total = data["issues"]["totalCount"]
        fechadas = data["closedIssues"]["totalCount"]
        percentual = round(100 * fechadas / total, 1) if total else 0.0
        linguagem = (data["primaryLanguage"] or {}).get("name", "Nao informado")
        print(f"{data['nameWithOwner']:<28} {linguagem:>14} {total:>13} {fechadas:>16} {percentual:>10}")


if __name__ == "__main__":
    validar()
