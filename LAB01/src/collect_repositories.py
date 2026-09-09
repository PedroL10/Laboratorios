import csv
import json
import os
import sys

from github_client import run_query

SEARCH_QUERY = "stars:>1 sort:stars-desc"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATHS = {
    "json": os.path.join(DATA_DIR, "repositorios_lab01_s01.json"),
    "csv": os.path.join(DATA_DIR, "repositorios_lab01_s02.csv"),
}

REPOSITORIES_QUERY = """
query ($searchQuery: String!, $first: Int!, $after: String) {
  search(query: $searchQuery, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount
        createdAt
        pushedAt
        primaryLanguage {
          name
        }
        releases {
          totalCount
        }
        issues {
          totalCount
        }
        closedIssues: issues(states: CLOSED) {
          totalCount
        }
        pullRequests(states: MERGED) {
          totalCount
        }
      }
    }
  }
}
"""


def _flatten(node):
    return {
        "name_with_owner": node["nameWithOwner"],
        "stargazers": node["stargazerCount"],
        "created_at": node["createdAt"],
        "pushed_at": node["pushedAt"],
        "primary_language": (node["primaryLanguage"] or {}).get("name"),
        "releases_total": node["releases"]["totalCount"],
        "issues_total": node["issues"]["totalCount"],
        "issues_closed_total": node["closedIssues"]["totalCount"],
        "pull_requests_merged_total": node["pullRequests"]["totalCount"],
    }


def fetch_top_repositories(count, page_size=10):
    repos = []
    cursor = None

    while len(repos) < count:
        variables = {
            "searchQuery": SEARCH_QUERY,
            "first": min(page_size, count - len(repos)),
            "after": cursor,
        }
        page = run_query(REPOSITORIES_QUERY, variables)["search"]
        repos.extend(_flatten(node) for node in page["nodes"])

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return repos


def save_json(repos, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)


def save_csv(repos, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(repos[0].keys()))
        writer.writeheader()
        writer.writerows(repos)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    fmt = sys.argv[2] if len(sys.argv) > 2 else "json"

    repos = fetch_top_repositories(count)
    path = OUTPUT_PATHS[fmt]

    if fmt == "csv":
        save_csv(repos, path)
    else:
        save_json(repos, path)

    print(f"{len(repos)} repositorios salvos em {path}")
