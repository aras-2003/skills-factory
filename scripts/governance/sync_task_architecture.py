#!/usr/bin/env python3
"""Sync proposed Architecture Impact for existing GitHub Project V2 items.

Manifest is versioned, authored input; never infer impact from an Issue title at runtime.
Does not create Project items or change Issue state/contents.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
MANIFEST = HERE.parents[2] / "docs/governance/task-architecture-impact-2026-11.json"
SYNC_PATH = HERE.with_name("sync_project_metadata.py")
spec = importlib.util.spec_from_file_location("project_metadata_sync", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

VALID = {"A0", "A1", "A2", "A3", "A4"}
QUERY = """query($owner:String!, $project:Int!, $repo:String!, $issue:Int!) {
 user(login:$owner) {
   projectV2(number:$project) {
     id
     fields(first:100) {nodes {
       ... on ProjectV2SingleSelectField {id name options{id name}}
     }}
   }
   repository(name:$repo) {
     issue(number:$issue) {
       state
       title
       projectItems(first:100) {nodes{id project{id}}}
     }
   }
 }
}"""


def load_manifest(path=MANIFEST):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "tdc-architecture-batch-v1" or data.get("repository") != "aras-2003/skills-factory":
        raise ValueError("Wrong manifest schema/repository")
    issues = data.get("issues", {})
    if not issues:
        raise ValueError("Empty architecture manifest")
    for number, row in issues.items():
        if not number.isdigit() or int(number) <= 0:
            raise ValueError(f"Invalid Issue key: {number!r}")
        if row.get("level") not in VALID:
            raise ValueError(f"Invalid architecture impact for Issue {number}")
        if row.get("review") not in {"PROPOSED", "APPROVED"}:
            raise ValueError(f"Missing assessment status for Issue {number}")
        for field in ("title", "change_description", "architecture_reason", "acceptance_summary"):
            if not isinstance(row.get(field), str) or len(row[field].strip()) < 25:
                raise ValueError(f"Non-specific/missing {field} for Issue {number}")
        if "TO_CONFIRM" == row["level"]:
            raise ValueError(f"Ambiguous impact for Issue {number}")
    return issues


def option_id(fields, level):
    matched = [f for f in fields if f and f.get("name", "").casefold() == "architecture impact"]
    if len(matched) != 1 or "options" not in matched[0]:
        raise RuntimeError("Architecture Impact Project single-select field missing or ambiguous")
    field = matched[0]
    options = [o for o in field["options"] if o["name"].strip().casefold() == level.casefold()]
    if len(options) != 1:
        # Explicitly fail rather than silently map labels such as Low/Medium.
        raise RuntimeError(f"Architecture Impact option {level} missing or ambiguous; configured options: {[o['name'] for o in field['options']]}")
    return field["id"], options[0]["id"]


def sync_one(issue_number, row, apply=False):
    owner = os.environ.get("PROJECT_OWNER", "aras-2003")
    project_number = int(os.environ.get("PROJECT_NUMBER", "1"))
    repo = os.environ.get("GH_REPOSITORY", "")
    if repo != f"{owner}/skills-factory":
        raise RuntimeError("Unexpected repository; refusing cross-repository mutation")
    data = sync.gql(QUERY, {"owner": owner, "project": project_number, "repo": "skills-factory", "issue": issue_number})
    user = data.get("user") or {}
    project = user.get("projectV2") or {}
    issue = (user.get("repository") or {}).get("issue") or {}
    if not project or not issue:
        raise RuntimeError(f"Issue {issue_number}: Project or Issue unavailable")
    if issue.get("state") != "OPEN":
        return "SKIPPED_CLOSED"
    if issue.get("title") != row["title"]:
        raise RuntimeError(f"Issue {issue_number}: title changed since evidence capture; refresh manifest")
    items = [i for i in issue.get("projectItems", {}).get("nodes", []) if i.get("project", {}).get("id") == project["id"]]
    if len(items) != 1:
        raise RuntimeError(f"Issue {issue_number}: expected exactly one existing project item, got {len(items)}")
    field_id, selected = option_id(project["fields"]["nodes"], row["level"])
    if not apply:
        print(f"DRY_RUN Issue #{issue_number}: Architecture Impact={row['level']} assessment={row['review']}")
        return "DRY_RUN"
    sync.gql(sync.UPDATE, {"project": project["id"], "item": items[0]["id"],
                           "field": field_id, "option": selected})
    # Independent readback, not a GraphQL mutation receipt alone.
    verify = sync.gql("""query($id:ID!){node(id:$id){... on ProjectV2Item{
      fieldValues(first:100){nodes{... on ProjectV2ItemFieldSingleSelectValue {
        name field {... on ProjectV2FieldCommon {name}}
      }}}
    }}}""", {"id": items[0]["id"]})
    node = (verify.get("node") or {})
    values = (node.get("fieldValues") or {}).get("nodes", [])
    observed = [v["name"] for v in values if v and (v.get("field") or {}).get("name", "").casefold() == "architecture impact"]
    if observed != [row["level"]]:
        raise RuntimeError(f"Issue {issue_number}: post-write readback mismatch for Architecture Impact")
    print(f"VERIFIED Issue #{issue_number}: Architecture Impact={row['level']}")
    return "VERIFIED"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=MANIFEST)
    p.add_argument("--check", action="store_true", help="offline manifest validation, no GitHub calls")
    p.add_argument("--apply", action="store_true", help="explicitly write Project field; default is dry run")
    p.add_argument("--issue-number", type=int, default=0, help="zero = all manifest issues")
    args = p.parse_args(argv)
    issues = load_manifest(args.manifest)
    if args.check:
        print(f"MANIFEST_VALID {len(issues)} issues; no network/writes")
        return 0
    selected = [(int(n), r) for n, r in issues.items() if args.issue_number in (0, int(n))]
    if not selected:
        raise ValueError("Requested Issue not found in manifest")
    if args.apply and not os.environ.get("GH_TOKEN"):
        raise RuntimeError("PROJECTS_TOKEN/GH_TOKEN missing; refusing writes")
    errors = []
    for n, row in selected:
        try:
            sync_one(n, row, apply=args.apply)
        except (RuntimeError, ValueError, KeyError) as exc:
            errors.append((n, str(exc)))
            print(f"::error::Issue #{n}: {exc}", file=sys.stderr)
    print(f"Architecture Impact: processed={len(selected)} errors={len(errors)} mode={'APPLY' if args.apply else 'DRY_RUN'}")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        sys.exit(1)
