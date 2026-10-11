#!/usr/bin/env python3
"""Read-only structural audit of historical P0 backlog; no completion inference."""
import argparse
import json
from pathlib import Path

DEFAULT = Path("docs/roadmap/2026-10-05/BACKLOG.json")

def audit(data):
    items = data.get("items")
    if not isinstance(items, list):
        return ["items must be a list"], []
    errors, by_id = [], {}
    for n, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append(f"items[{n}]: missing string id")
            continue
        if item["id"] in by_id:
            errors.append(f'{item["id"]}: duplicate id')
        by_id[item["id"]] = item
    p0 = [x for x in items if isinstance(x, dict) and x.get("priority") == "P0"]
    for item in p0:
        key = item.get("id", "<missing>")
        deps = item.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"{key}: depends_on is not a list")
            continue
        for dep in deps:
            if not isinstance(dep, str) or dep not in by_id:
                errors.append(f"{key}: unknown dependency {dep!r}")
            elif dep == key:
                errors.append(f"{key}: self dependency")
    graph = {}
    for key, item in by_id.items():
        deps = item.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"{key}: depends_on is not a list")
            deps = []
        graph[key] = deps
    state = {}
    def visit(node, trail):
        if state.get(node) == 1:
            errors.append("dependency cycle: " + " -> ".join(trail + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in graph[node]:
            if isinstance(dep, str) and dep in graph:
                visit(dep, trail + [node])
        state[node] = 2
    for item in p0:
        if isinstance(item.get("id"), str):
            visit(item["id"], [])
    rows = [
        {"id": x.get("id"), "title": x.get("title"), "status": x.get("status"),
         "dependencies": x.get("depends_on", []), "evidence_state": "UNVERIFIED"}
        for x in p0
    ]
    return sorted(set(errors)), rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    errors, p0 = audit(json.loads(args.backlog.read_text(encoding="utf-8")))
    result = {"source": str(args.backlog), "p0_count": len(p0), "p0": p0,
              "structural_errors": errors,
              "note": "Historical status only. No implementation/runtime PASS inferred."}
    output = json.dumps(result, indent=2, ensure_ascii=False) + chr(10)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
