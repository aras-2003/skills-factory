#!/usr/bin/env python3
"""Check source registry ↔ generated catalog ↔ capability inventory consistency.

This never calls an MCP host. Source declaration parity is NOT installed/runtime
availability. Missing or mismatched source records fail closed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CHANNELS = {"plugin", "lab", "chatgpt-zip"}
STATES = {"supported", "unavailable", "requiring_approval", "unknown"}


def assess(root: Path, *, registry: object | None = None, catalog: object | None = None,
           contract: object | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        if registry is None:
            registry = yaml.safe_load((root / "workflows/runtime-registry.yaml").read_text(encoding="utf-8"))
        if catalog is None:
            catalog = json.loads((root / "docs/catalog.json").read_text(encoding="utf-8"))
        if contract is None:
            contract = yaml.safe_load((root / "release/capability-contract.yaml").read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {"status": "BLOCKED_SOURCE", "errors": [type(exc).__name__],
                "runtime_installation": "NOT_OBSERVED", "release_approved": False}

    if not isinstance(registry, dict) or not isinstance(registry.get("workflows"), list):
        errors.append("registry: workflows list required")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("workflows"), list) or not isinstance(catalog.get("skills"), list):
        errors.append("catalog: skills/workflows lists required")
    if not isinstance(contract, dict) or not isinstance(contract.get("component_declarations"), dict):
        errors.append("contract: component declarations mapping required")
    if errors:
        return {"status": "BLOCKED_SOURCE", "errors": errors,
                "runtime_installation": "NOT_OBSERVED", "release_approved": False}

    def collect(rows: list, label: str) -> dict[str, dict]:
        found = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
                errors.append(f"{label}: invalid identity")
                continue
            name = row["name"]
            if name in found:
                errors.append(f"{label}: duplicate {name}")
            found[name] = row
        return found

    reg = collect(registry["workflows"], "registry")
    cat = collect(catalog["workflows"], "catalog workflow")
    skills = collect(catalog["skills"], "catalog skill")
    sources = {x.relative_to(root).as_posix() for x in (root / "workflows").rglob("WORKFLOW.md")}
    skill_sources = {x.relative_to(root).as_posix() for x in (root / "skills").rglob("SKILL.md")}
    declared = contract["component_declarations"]

    for name in sorted(set(reg) ^ set(cat)):
        errors.append(f"registry/catalog workflow mismatch: {name}")
    if len(sources) != len(reg):
        errors.append(f"source workflow count {len(sources)} != registry {len(reg)}")
    if len(skill_sources) != len(skills):
        errors.append(f"source skill count {len(skill_sources)} != catalog {len(skills)}")
    if set(reg) | set(skills) != set(declared):
        errors.append("capability declaration set does not match current registered workflow/skill inventory")
    for name, row in reg.items():
        if name not in cat:
            continue
        exported = cat[name]
        source = row.get("workflow")
        if not isinstance(source, str) or source not in sources:
            errors.append(f"{name}: registered workflow source missing or unsafe")
        for source_field, cat_field in (("workflow", "source"),):
            if row.get(source_field) != exported.get(cat_field):
                errors.append(f"{name}: {cat_field} mismatch")
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{name}: missing metadata")
            metadata = {}
        for key in ("version", "maturity"):
            if metadata.get(key) != exported.get(key):
                errors.append(f"{name}: {key} mismatch")
        channels = row.get("channels")
        if not isinstance(channels, dict) or set(channels) != CHANNELS or any(x not in STATES for x in channels.values()):
            errors.append(f"{name}: invalid declared channels")
        if channels != exported.get("declared_channels"):
            errors.append(f"{name}: generated declared_channels mismatch")
        deps = row.get("dependencies") or {}
        if not isinstance(deps, dict):
            errors.append(f"{name}: dependencies not a mapping")
            deps = {}
        required = deps.get("required") or []
        optional = deps.get("optional") or []
        if not isinstance(required, list) or not isinstance(optional, list):
            errors.append(f"{name}: dependencies must be lists")
            continue
        if not all(isinstance(x, str) for x in required) or not all(isinstance(x, dict) and isinstance(x.get("name"), str) for x in optional):
            errors.append(f"{name}: malformed dependencies")
            continue
        if sorted(required) != exported.get("required_dependencies"):
            errors.append(f"{name}: required dependencies mismatch")
        if sorted(x["name"] for x in optional) != exported.get("optional_dependencies"):
            errors.append(f"{name}: optional dependencies mismatch")
        decl = declared.get(name) or {}
        reqs = decl.get("requirements") if isinstance(decl, dict) else None
        if not isinstance(reqs, dict) or any(x == "unassessed" for x in reqs.values()):
            if exported.get("capability_assessment") != "UNASSESSED":
                errors.append(f"{name}: unassessed source promoted to declared-ready in catalog")
            warnings.append(f"{name}: capability requirements not independently assessed")
        if exported.get("runtime_registration") != "registered":
            errors.append(f"{name}: registered workflow not registered in catalog")
    for name, item in skills.items():
        if item.get("source") not in skill_sources:
            errors.append(f"{name}: missing source SKILL.md")
        decl = declared.get(name) or {}
        reqs = decl.get("requirements") if isinstance(decl, dict) else None
        if not isinstance(reqs, dict) or any(x == "unassessed" for x in reqs.values()):
            if item.get("capability_assessment") != "UNASSESSED":
                errors.append(f"{name}: skill requirements promoted without assessment")
            warnings.append(f"{name}: skill capability requirements unassessed")
    metadata = catalog.get("metadata") or {}
    if not isinstance(metadata, dict) or metadata.get("runtime_installation") != "NOT_OBSERVED":
        errors.append("catalog must not claim installed runtime from static source")
    if metadata.get("registered_workflow_count") != len(reg) or metadata.get("source_workflow_count") != len(sources):
        errors.append("generated workflow totals do not match exact source set")
    return {
        "schema_version": "1.0", "kind": "static_registry_catalog_contract_parity",
        "status": "BLOCKED" if errors else "SOURCE_PARITY_ONLY_REVIEW_REQUIRED",
        "workflow_count": len(reg), "skill_count": len(skills),
        "errors": sorted(set(errors)),
        "review_signal_count": len(set(warnings)),
        "review_signals": sorted(set(warnings)),
        "runtime_installation": "NOT_OBSERVED",
        "tool_calls_executed": False,
        "release_approved": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = assess(args.root)
    contents = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(contents, encoding="utf-8")
    else:
        print(contents, end="")
    return int(result["status"] != "SOURCE_PARITY_ONLY_REVIEW_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())
