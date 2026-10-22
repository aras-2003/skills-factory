#!/usr/bin/env python3
"""Sync existing GitHub Issues to Project V2 fields. Never create project items or mutate Issues."""
import json
import os
import re
import sys
import time
import subprocess

PROJECT = """query($owner:String!, $project:Int!, $repo:String!, $issue:Int!) {
  user(login:$owner) {
    projectV2(number:$project) {
      id
      fields(first:100) {nodes {
        ... on ProjectV2SingleSelectField {id name options{id name}}\n        ... on ProjectV2IterationField {id name configuration{iterations{id title startDate duration}}}
      }}
    }
    repository(name:$repo) {
      issue(number:$issue) {
        title body labels(first:100) {nodes{name}}
        projectItems(first:100) {nodes{id project{id number}}}
      }
    }
  }
}"""
# GitHub's user->repository works for own user repositories only.
ITERATION_UPDATE = """mutation($project:ID!, $item:ID!, $field:ID!, $iteration:String!) {\n  updateProjectV2ItemFieldValue(input:{\n    projectId:$project,itemId:$item,fieldId:$field,\n    value:{iterationId:$iteration}\n  }) {projectV2Item{id}}\n}"""\nUPDATE = """mutation($project:ID!, $item:ID!, $field:ID!, $option:String!) {
  updateProjectV2ItemFieldValue(input:{
    projectId:$project,itemId:$item,fieldId:$field,
    value:{singleSelectOptionId:$option}
  }) {projectV2Item{id}}
}"""
PRIORITY = {"P0", "P1", "P2", "P3"}
SIZE = {"XS", "S", "M", "L", "XL"}
STATUS = {"In Progress", "Blocked", "Discovery", "Validation", "In review", "Done", "Ready", "Backlog"}
AREA = {"Engineering", "Runtime", "E2E & Quality", "Security", "Commerce",
        "Investing", "OAF", "Learning", "Strategy", "Other"}
PREFIX_AREA = {"ENG":"Engineering", "E2E":"E2E & Quality",
               "STR":"Strategy", "LEA":"Learning", "DOM":"Engineering",
               "PRO":"Other", "LIF":"Other", "CON":"Other", "WRI":"Other",
               "CORE":"Engineering", "EXI":"Engineering"}

def gql(query, variables):
    """Use GitHub CLI for authenticated transport; never handle credentials here."""
    payload = json.dumps({"query":query, "variables":variables})
    result = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=payload, text=True, capture_output=True, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError(f"GitHub CLI GraphQL request failed (exit {result.returncode})")
    data = json.loads(result.stdout)
    if data.get("errors"):
        raise RuntimeError("GitHub GraphQL error: " + json.dumps(data["errors"]))
    return data["data"]

def values(title, body, labels):
    """Strict fields from labels, or legacy exact key syntax. Never guess missing values."""
    labels = {x.lower() for x in labels}
    result = {}
    for field, valid, pattern in (
        ("Priority", PRIORITY, r"(?im)(?:^\s*-?\s*|;)\s*(?:historical )?priority\s*:\s*\*{0,2}(P[0-3])\b"),
        ("Size", SIZE, r"(?im)(?:^\s*-?\s*|;)\s*(?:size|effort)\s*:\s*\*{0,2}(XS|S|M|L|XL)\b"),
        ("Area", AREA, None)):
        selected = [v for v in valid if f"{field.lower()}:{v.lower()}" in labels]
        if len(selected) > 1:
            raise ValueError(f"Conflicting {field} labels: {selected}")
        if selected:
            result[field] = selected[0]
        elif pattern:
            m = re.search(pattern, body)
            if m:
                result[field] = m.group(1)
    # Only a dedicated Project status marker controls the live Project column.
    # Historical backlog status and narrative "Status" remain non-authoritative.
    raw = re.findall(r"(?im)^\s*-?\s*Project status\s*:\s*\*{0,2}(In Progress|Blocked|Discovery|Validation|In review|Done|Ready|Backlog)\*{0,2}\s*$", body)
    selected_status = [v for v in STATUS if "status:" + v.lower() in labels]
    if len(set(selected_status)) > 1 or len(set(raw)) > 1:
        raise ValueError("Conflicting Project Status values")
    if selected_status and raw and selected_status[0].casefold() != raw[0].casefold():
        raise ValueError("Conflicting Project Status label and body")
    if selected_status or raw:
        result["Status"] = selected_status[0] if selected_status else raw[0]
    # Explicit exact Project iteration title only. No inference from roadmap, dates or issue prefixes.
    it = re.findall(r"(?im)^\\s*Project iteration\\s*:\\s*(.+?)\\s*$", body)
    if len(it) > 1 and len(set(it)) != 1:
        raise ValueError("Conflicting Project iteration markers")
    if it:
        result["Iteration"] = it[0].strip()
    if "Area" not in result:
        m = re.match(r"^\[([A-Z][A-Z0-9]*)-\d+\]", title)
        if m:
            result["Area"] = PREFIX_AREA.get(m.group(1), "Other")
    return result

def main():
    repo = os.environ["GH_REPOSITORY"]
    owner = os.environ["PROJECT_OWNER"]
    number = int(os.environ["PROJECT_NUMBER"])
    issue = int(os.environ["ISSUE_NUMBER"])
    if repo != f"{owner}/skills-factory":
        raise RuntimeError("Unexpected repository; refusing cross-repository mutation")
    data = None
    for attempt in range(6):
        data = gql(PROJECT, {"owner":owner,"project":number,"repo":"skills-factory","issue":issue})
        user = data.get("user") or {}
        project = user.get("projectV2")
        obj = (user.get("repository") or {}).get("issue")
        if not project or not obj:
            raise RuntimeError("Project or issue not accessible")
        items = [n for n in obj["projectItems"]["nodes"] if n["project"]["id"] == project["id"]]
        if items: break
        if attempt < 5: time.sleep(10)
    else:
        raise RuntimeError("Issue not in Project yet (auto-add pending/failed); refusing to report success")
    if len(items) != 1:
        raise RuntimeError("Ambiguous Project items")
    target = values(obj["title"], obj.get("body") or "", [n["name"] for n in obj["labels"]["nodes"]])
    fields = {x["name"]:x for x in project["fields"]["nodes"] if x and x.get("name")}
    if not target:
        print("No explicit metadata; no changes")
        return
    updates = []
    for name, value in target.items():
        f = fields.get(name)
        if name == "Iteration":
            if not f or not (f.get("configuration") or {}).get("iterations"):
                raise RuntimeError("Required native Iteration field unavailable")
            choices = [v for v in f["configuration"]["iterations"] if v["title"].casefold() == value.casefold()]
            if len(choices) != 1:
                raise RuntimeError(f"Iteration title {value!r} missing/ambiguous; existing options: {[v['title'] for v in f['configuration']['iterations']]}")
            updates.append((name, value, f["id"], choices[0]["id"]))
            continue
        if not f or "options" not in f:
            raise RuntimeError(f"Required Project field {name} missing or not single-select")
        options = [o["id"] for o in f["options"] if o["name"].casefold()==value.casefold()]
        if len(options)!=1:
            available = sorted(str(o["name"]) for o in f["options"])
            raise RuntimeError(f"Option {value} missing/ambiguous for {name}; available options: {available}")
        updates.append((name, value, f["id"], options[0]))
    for name, value, field_id, option in updates:
        gql(UPDATE, {"project":project["id"],"item":items[0]["id"],
                     "field":field_id,"option":option})
        print(f"Set {name}={value} on Project #{number} Issue #{issue}")

if __name__ == "__main__":
    try: main()
    except (ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(f"::error::{error}",file=sys.stderr)
        sys.exit(1)
