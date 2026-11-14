#!/usr/bin/env python3
"""Sync proposed Architecture Impact for existing GitHub Project V2 items.

Manifest is versioned, authored input; never infer impact from an Issue title at runtime.
Does not create Project items or change Issue state/contents.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
MANIFEST = HERE.parents[2] / "docs/governance/task-architecture-impact-2026-11.json"
SYNC_PATH = HERE.with_name("sync_project_metadata.py")
spec = importlib.util.spec_from_file_location("project_metadata_sync", SYNC_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

VALID = {"A0", "A1", "A2", "A3", "A4"}
FIELD_VALUES = """query($id:ID!){node(id:$id){... on ProjectV2Item{
 fieldValues(first:100){nodes{
  ... on ProjectV2ItemFieldSingleSelectValue {name field {... on ProjectV2FieldCommon {name}}}
  ... on ProjectV2ItemFieldTextValue {text field {... on ProjectV2FieldCommon {name}}}
 }}
}}}"""
TEXT_UPDATE = """mutation($project:ID!, $item:ID!, $field:ID!, $text:String!){
 updateProjectV2ItemFieldValue(input:{
  projectId:$project,itemId:$item,fieldId:$field,value:{text:$text}
 }){projectV2Item{id}}
}"""
QUERY = """query($owner:String!, $project:Int!, $repo:String!, $issue:Int!) {
 user(login:$owner) {
   projectV2(number:$project) {
     id
     fields(first:100) {nodes {
       ... on ProjectV2SingleSelectField {id name options{id name}}
       ... on ProjectV2Field {id name dataType}
     }}
   }
   repository(name:$repo) {
     issue(number:$issue) {
       state title
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
    expected_count = data.get("expected_issue_count")
    if expected_count != len(issues):
        raise ValueError(f"Architecture manifest count mismatch: expected {expected_count}, found {len(issues)}")
    expected_ids = data.get("expected_issue_ids_sha256")
    actual_ids = hashlib.sha256(("\n".join(sorted(issues, key=int)) + "\n").encode()).hexdigest()
    if expected_ids != actual_ids:
        raise ValueError("Architecture manifest Issue ID lock mismatch")
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
    if level not in VALID:
        raise RuntimeError(f"Unrecognized Architecture Impact level: {level}")
    matched = [f for f in fields if f and f.get("name", "").casefold() == "architecture impact"]
    if len(matched) != 1 or "options" not in matched[0]:
        raise RuntimeError("Architecture Impact Project single-select field missing or ambiguous")
    field = matched[0]
    missing_or_ambiguous = [level for level in sorted(VALID)
                            if sum(o["name"].strip().casefold() == level.casefold()
                                   for o in field["options"]) != 1]
    if missing_or_ambiguous:
        raise RuntimeError(f"Architecture Impact options missing or ambiguous: {missing_or_ambiguous}")
    options = [o for o in field["options"] if o["name"].strip().casefold() == level.casefold()]
    if len(options) != 1:
        # Explicitly fail rather than silently map labels such as Low/Medium.
        raise RuntimeError(f"Architecture Impact option {level} missing or ambiguous; configured options: {[o['name'] for o in field['options']]}")
    return field["id"], options[0]["id"]


def field_target(fields, row):
    """Project's native field may be a single-select classification or a text description."""
    matched = [f for f in fields if f and f.get("name", "").casefold() == "architecture impact"]
    if len(matched) != 1:
        raise RuntimeError("Architecture Impact field missing or ambiguous")
    field = matched[0]
    if "options" in field:
        _, option = option_id(fields, row["level"])
        return field["id"], "option", option, row["level"]
    if field.get("dataType") == "TEXT":
        # GitHub Projects text field: preserve concise issue-specific impact, rather than
        # assuming single-select A0..A4 options which the user did not guarantee.
        description = row["change_description"].replace("\n", " ").strip()
        reason = row["architecture_reason"].replace("\n", " ").strip()
        value = f"{row['level']} — {reason}\nOpis zmiany: {description}"
        if len(value) > 1000:
            value = value[:997].rsplit(" ", 1)[0] + "..."
        return field["id"], "text", value, value
    raise RuntimeError("Architecture Impact field is neither TEXT nor single-select")


def field_values(data):
    nodes = ((data.get("node") or {}).get("fieldValues") or {}).get("nodes", [])
    return [v.get("name", v.get("text")) for v in nodes
            if v and (v.get("field") or {}).get("name", "").casefold() == "architecture impact"]


def sync_one(issue_number, row, apply=False):
    if apply and row.get("review") != "APPROVED":
        raise RuntimeError(f"Issue {issue_number}: Architecture Impact is not approved; refusing Project write")
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
    # Manifest was frozen while items were OPEN. Retain coverage if a captured Issue
    # becomes CLOSED before the backfill; only the Project field is being updated.
    if issue.get("state") not in {"OPEN", "CLOSED"}:
        raise RuntimeError(f"Issue {issue_number}: unknown issue state")
    if issue.get("title") != row["title"]:
        raise RuntimeError(f"Issue {issue_number}: title changed since evidence capture; refresh manifest")
    items = [i for i in issue.get("projectItems", {}).get("nodes", []) if i.get("project", {}).get("id") == project["id"]]
    if len(items) != 1:
        raise RuntimeError(f"Issue {issue_number}: expected exactly one existing project item, got {len(items)}")
    field_id, mode, selected, expected = field_target(project["fields"]["nodes"], row)
    if mode == "option":
        impact_field = next(f for f in project["fields"]["nodes"]
                            if f and f.get("name", "").casefold() == "architecture impact")
        field_summary = "single-select options=" + ",".join(sorted(o["name"].strip() for o in impact_field["options"]))
    else:
        field_summary = "text"
    if not apply:
        print(f"DRY_RUN Issue #{issue_number}: Architecture Impact={row['level']} assessment={row['review']} field={field_summary}")
        return "DRY_RUN"
    # Do not clobber a field a project reviewer already classified differently.
    before = sync.gql(FIELD_VALUES, {"id": items[0]["id"]})
    present = field_values(before)
    if len(present) > 1:
        raise RuntimeError(f"Issue {issue_number}: ambiguous existing Architecture Impact values")
    if present == [expected]:
        print(f"ALREADY_VERIFIED Issue #{issue_number}: Architecture Impact={row['level']}")
        return "ALREADY_VERIFIED"
    if issue.get("state") == "CLOSED":
        raise RuntimeError(f"Issue {issue_number}: closed after manifest capture; refusing a new Project write")
    if present:
        raise RuntimeError(f"Issue {issue_number}: existing reviewed Architecture Impact differs; refusing overwrite")
    mutation = sync.UPDATE if mode == "option" else TEXT_UPDATE
    sync.gql(mutation, {"project": project["id"], "item": items[0]["id"],
                        "field": field_id, mode: selected})
    # Independent readback, not a GraphQL mutation receipt alone.
    verify = sync.gql(FIELD_VALUES, {"id": items[0]["id"]})
    observed = field_values(verify)
    if observed != [expected]:
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
    manifest_sha256 = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    if args.check:
        print(f"MANIFEST_VALID {len(issues)} issues sha256={manifest_sha256}; no network/writes")
        return 0
    selected = [(int(n), r) for n, r in issues.items() if args.issue_number in (0, int(n))]
    if not selected:
        raise ValueError("Requested Issue not found in manifest")
    if args.apply and not os.environ.get("GH_TOKEN"):
        raise RuntimeError("PROJECTS_TOKEN/GH_TOKEN missing; refusing writes")
    print(f"MANIFEST_SHA256 {manifest_sha256}")
    errors = []
    for n, row in selected:
        try:
            sync_one(n, row, apply=args.apply)
        except (RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
            errors.append((n, str(exc)))
            print(f"::error::Issue #{n}: {exc}", file=sys.stderr)
    print(f"Architecture Impact: processed={len(selected)} errors={len(errors)} mode={'APPLY' if args.apply else 'DRY_RUN'}")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        sys.exit(1)
