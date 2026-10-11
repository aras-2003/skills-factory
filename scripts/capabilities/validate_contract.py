from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from contract import DIMENSIONS, assessment_for, load_contract, load_dimensions


def validate(root: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    contract = load_contract(root)
    load_dimensions(contract)
    known: set[str] = set()
    known_sources: dict[str, str] = {}
    for path in sorted((root / "skills").rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        end = text.find("\n---\n", 4) if text.startswith("---\n") else -1
        if end < 0:
            errors.append(f"{path.relative_to(root)}: missing frontmatter")
            continue
        data = yaml.safe_load(text[4:end]) or {}
        name = data.get("name")
        if isinstance(name, str):
            known.add(name)
            known_sources[name] = path.relative_to(root).as_posix()
    registry = yaml.safe_load((root / "workflows/runtime-registry.yaml").read_text(encoding="utf-8")) or {}
    for item in registry.get("workflows") or []:
        if isinstance(item, dict) and item.get("name"):
            name = str(item["name"])
            known.add(name)
            known_sources[name] = str(item.get("workflow") or "")
    declarations = contract["component_declarations"]
    for name in sorted(set(declarations) - known):
        errors.append(f"declaration references unknown component: {name}")
    for name in sorted(known):
        declaration = declarations.get(name)
        if not isinstance(declaration, dict):
            errors.append(f"{name}: missing explicit source inventory declaration")
            continue
        source = declaration.get("source")
        if not isinstance(source, str) or source.startswith("/") or ".." in Path(source).parts or not (root / source).is_file():
            errors.append(f"{name}: declaration must point to an existing repository source")
        elif source != known_sources[name]:
            errors.append(f"{name}: declared source differs from canonical registry path")
        if declaration.get("review_state") != "STATIC_PARTIAL":
            errors.append(f"{name}: source review_state must be STATIC_PARTIAL pending runtime verification")
    rows = []
    for name in sorted(known):
        try:
            assessment = assessment_for(contract, name)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        rows.append({"name": name, **assessment})
    return {
        "schema_version": "1.0",
        "contract_id": contract["contract_id"],
        "assessment_semantics": "UNASSESSED is not evidence of no permissions or runtime compatibility",
        "component_count": len(rows),
        "unassessed_count": sum(row["status"] == "UNASSESSED" for row in rows),
        "explicit_source_count": len(declarations),
        "partially_evidenced_count": sum(any(value != "unassessed" for value in row["requirements"].values()) for row in rows),
        "runtime_compatibility": "NOT_VERIFIED",
        "components": rows,
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report, errors = validate(args.root.resolve())
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print(f"[BLOCKER] {error}")
    if not errors:
        print(f"Capability contract schema: OK ({report['component_count']} components; {report['unassessed_count']} require review)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
