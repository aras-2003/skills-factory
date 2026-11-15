"""Bound development WIP using existing Project items, without another task store."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MAX_DEVELOPMENT_WIP = 2
STAGES = {"Backlog", "Discovery", "Ready", "In progress", "In review", "Verification", "Done"}
ACTIVE = {"In progress", "In review"}
PROJECT_ITEMS = """query($owner:String!, $project:Int!, $cursor:String) {
 user(login:$owner) {projectV2(number:$project) {items(first:100,after:$cursor) {
 pageInfo {hasNextPage endCursor} nodes {id isArchived
 content {... on Issue {number repository{nameWithOwner} labels(first:100){nodes{name} pageInfo{hasNextPage}}}}
 fieldValues(first:100){nodes {... on ProjectV2ItemFieldSingleSelectValue {name field {... on ProjectV2FieldCommon {name}}}}}
 }}}}}
"""


def check_wip(items: list[dict], *, starting_item: str | None = None) -> dict:
    active = []
    for item in items:
        if item.get("archived") or item.get("blocked"):
            continue
        if item.get("status") not in STAGES:
            raise ValueError("Unknown Project stage; verify native field options")
        if item["status"] in ACTIVE or item["id"] == starting_item:
            active.append(item["id"])
    return {"status": "PASS" if len(active) <= MAX_DEVELOPMENT_WIP else "BLOCKED",
            "development_wip": len(active), "limit": MAX_DEVELOPMENT_WIP,
            "active_items": sorted(active), "runtime_pass_claim": False}


def read_project_items(gql, owner: str, project: int, repository: str) -> list[dict]:
    cursor = None
    items = []
    while True:
        data = gql(PROJECT_ITEMS, {"owner": owner, "project": project, "cursor": cursor})
        connection = data["user"]["projectV2"]["items"]
        for node in connection["nodes"]:
            obj = node.get("content") or {}
            if (obj.get("repository") or {}).get("nameWithOwner") != repository:
                continue
            values = [v["name"] for v in node["fieldValues"]["nodes"] if v and
                      (v.get("field") or {}).get("name") == "Status"]
            if len(values) != 1 or obj.get("labels", {}).get("pageInfo", {}).get("hasNextPage"):
                raise ValueError("Incomplete or ambiguous Project metadata")
            labels = {v["name"].lower() for v in obj.get("labels", {}).get("nodes", [])}
            items.append({"id": node["id"], "status": values[0], "archived": node.get("isArchived", False),
                          "blocked": bool(labels & {"blocked", "status:blocked"})})
        info = connection["pageInfo"]
        if not info["hasNextPage"]:
            return items
        next_cursor = info["endCursor"]
        if not next_cursor or next_cursor == cursor:
            raise ValueError("Project pagination did not advance")
        cursor = next_cursor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-owner", default="aras-2003")
    parser.add_argument("--project-number", type=int, default=1)
    parser.add_argument("--repository", default="aras-2003/skills-factory")
    args = parser.parse_args()
    from sync_project_metadata import gql
    report = check_wip(read_project_items(gql, args.project_owner, args.project_number, args.repository))
    # Counts only: do not disclose Project contents in public Actions logs.
    print(json.dumps({k: v for k, v in report.items() if k != "active_items"}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
