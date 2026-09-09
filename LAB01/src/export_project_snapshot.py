import csv
import os
import sys

from github_client import run_query

PROJECT_OWNER = "PedroL10"
PROJECT_NUMBER = 1
DEFAULT_OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "snapshot_lab01_s02.csv"
)

PROJECT_ITEMS_QUERY = """
query ($login: String!, $number: Int!, $after: String) {
  user(login: $login) {
    projectV2(number: $number) {
      title
      items(first: 50, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field {
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
              }
            }
          }
          content {
            ... on Issue {
              number
              title
              url
              state
              assignees(first: 5) {
                nodes {
                  login
                }
              }
            }
            ... on DraftIssue {
              title
            }
          }
        }
      }
    }
  }
}
"""


def _status(item):
    for field_value in item["fieldValues"]["nodes"]:
        if field_value.get("field", {}).get("name") == "Status":
            return field_value.get("name")
    return None


def _flatten(item):
    content = item["content"]
    is_draft = "number" not in content

    return {
        "issue_number": content.get("number"),
        "title": content.get("title"),
        "status": _status(item),
        "assignees": ", ".join(a["login"] for a in content.get("assignees", {}).get("nodes", [])),
        "state": content.get("state"),
        "url": content.get("url"),
        "is_draft_issue": is_draft,
    }


def fetch_project_items():
    items = []
    cursor = None

    while True:
        variables = {"login": PROJECT_OWNER, "number": PROJECT_NUMBER, "after": cursor}
        page = run_query(PROJECT_ITEMS_QUERY, variables)["user"]["projectV2"]["items"]
        items.extend(_flatten(node) for node in page["nodes"])

        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return items


def save_csv(items, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(items[0].keys()))
        writer.writeheader()
        writer.writerows(items)


if __name__ == "__main__":
    items = fetch_project_items()
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_PATH
    save_csv(items, output_path)
    print(f"{len(items)} itens do Project salvos em {output_path}")

    drafts = [i for i in items if i["is_draft_issue"]]
    if drafts:
        print(f"AVISO: {len(drafts)} draft issue(s) encontrada(s) no board (nao permitido pelo enunciado): "
              f"{[d['title'] for d in drafts]}", file=sys.stderr)
