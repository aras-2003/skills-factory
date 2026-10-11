from __future__ import annotations

import sys
from pathlib import Path

import yaml

from common import repo_root


def known_capability_names(root: Path) -> set[str]:
    names: set[str] = set()
    for skill in (root / "skills").rglob("SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            data = yaml.safe_load(text[4:end]) or {}
            if isinstance(data.get("name"), str):
                names.add(data["name"])
    registry = yaml.safe_load((root / "workflows/runtime-registry.yaml").read_text(encoding="utf-8")) or {}
    for item in registry.get("workflows") or []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.add(item["name"])
    return names


def leaked_capabilities(input_text: str, known: set[str]) -> list[str]:
    lowered = input_text.lower()
    return sorted(name for name in known if name.lower() in lowered)


def validate(root: Path) -> list[str]:
    path = root / "evals/routing/registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = data.get("cases") or []
    errors: list[str] = []
    ids: set[str] = set()
    languages: set[str] = set()
    known = known_capability_names(root)

    if not isinstance(cases, list) or not cases:
        return ["routing registry must contain cases"]

    for case in cases:
        if not isinstance(case, dict):
            errors.append("routing registry entry must be a mapping")
            continue
        cid = str(case.get("id") or "")
        if not cid or cid in ids:
            errors.append(f"invalid/duplicate routing id: {cid!r}")
        ids.add(cid)
        ip = root / str(case.get("input") or "")
        rp = root / str(case.get("rubric") or "")
        if not ip.is_file() or not ip.name.endswith(".input.md"):
            errors.append(f"{cid}: invalid input file")
            continue
        if not rp.is_file() or not rp.name.endswith(".rubric.yaml"):
            errors.append(f"{cid}: invalid rubric file")
            continue
        input_text = ip.read_text(encoding="utf-8").lower()
        rubric = yaml.safe_load(rp.read_text(encoding="utf-8")) or {}
        if rubric.get("id") != cid:
            errors.append(f"{cid}: rubric id mismatch")
        if rubric.get("mode") != "natural-routing":
            errors.append(f"{cid}: mode must be natural-routing")
        target = rubric.get("expected_target")
        if target not in known and target != "no-skill":
            errors.append(f"{cid}: unknown expected_target {target!r}")
        if target == "no-skill" and (rubric.get("required_selected_capabilities") or []):
            errors.append(f"{cid}: no-skill case cannot require skill selection")
        if target == "no-skill" and not (rubric.get("forbidden_selected_capabilities") or []):
            errors.append(f"{cid}: no-skill case requires explicit forbidden skill routes")
        if target and str(target).lower() in input_text:
            errors.append(f"{cid}: input leaks expected target name")
        leaked = leaked_capabilities(input_text, known)
        if leaked:
            errors.append(f"{cid}: input names runtime capabilities: {', '.join(sorted(leaked))}")
        language = rubric.get("language")
        if language not in {"pl", "en"}:
            errors.append(f"{cid}: language must be pl or en")
        else:
            languages.add(language)
        competing = rubric.get("competing_intents")
        if not isinstance(competing, list) or not competing:
            errors.append(f"{cid}: competing_intents must be non-empty")
        for field in ("required_selected_capabilities", "forbidden_selected_capabilities"):
            values = rubric.get(field) or []
            if not isinstance(values, list) or not all(isinstance(x, str) and x for x in values):
                errors.append(f"{cid}: {field} must be a list of capability names")
                continue
            unknown = sorted(set(values) - known)
            if unknown:
                errors.append(f"{cid}: {field} contains unknown capabilities: {', '.join(unknown)}")

        tool_fragments = rubric.get("required_tool_fragments") or []
        if not isinstance(tool_fragments, list) or not all(isinstance(x, str) and x for x in tool_fragments):
            errors.append(f"{cid}: required_tool_fragments must be a list of non-empty strings")

        assertions = (rubric.get("assertions") or {}).get("manual") or []
        if not assertions:
            errors.append(f"{cid}: manual assertions are required")

    if languages != {"pl", "en"}:
        errors.append("routing suite must cover both pl and en")
    return errors


def main() -> int:
    errors = validate(repo_root())
    for error in errors:
        print(f"[BLOCKER] {error}")
    if not errors:
        print("Natural routing fixtures: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
