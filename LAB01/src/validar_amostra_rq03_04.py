"""Validacao rapida (Sprint 1) dos campos usados por RQ03 e RQ04.

Consulta uma amostra pequena (5-10 repositorios bem conhecidos, com
release/atualizacao facilmente conferiveis manualmente no site do GitHub) e
imprime os valores retornados pela query GraphQL, para o responsavel checar
"na mao" antes de integrar ao script unico de coleta (collect_repositories.py).

Uso:
    python src/validar_amostra_rq03_04.py
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
    pushedAt
    releases {
      totalCount
    }
  }
}
"""


def validar():
    print(f"{'Repositorio':<28} {'releases_total':>15} {'pushed_at':>25}")
    for name_with_owner in AMOSTRA:
        owner, name = name_with_owner.split("/")
        data = run_query(QUERY, {"owner": owner, "name": name})["repository"]
        print(f"{data['nameWithOwner']:<28} {data['releases']['totalCount']:>15} {data['pushedAt']:>25}")


if __name__ == "__main__":
    validar()
