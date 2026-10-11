from __future__ import annotations

from pathlib import Path

import yaml


DIMENSIONS = ("network", "filesystem", "shell_exec", "credentials", "external_actions")


def load_contract(root: Path) -> dict:
    path = root / "release/capability-contract.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("contract_id") != "repository-side-v1":
        raise ValueError("unsupported capability contract id")
    if data.get("schema_version") != "1.0":
        raise ValueError("unsupported capability contract schema version")
    declarations = data.get("component_declarations")
    if not isinstance(declarations, dict):
        raise ValueError("component_declarations must be a mapping")
    return data


def assessment_for(contract: dict, component: str) -> dict:
    declarations = contract["component_declarations"]
    item = declarations.get(component)
    if item is None:
        return {
            "status": "UNASSESSED",
            "requirements": {name: "unassessed" for name in DIMENSIONS},
        }
    if not isinstance(item, dict) or not isinstance(item.get("requirements"), dict):
        raise ValueError(f"{component}: declaration must contain requirements mapping")
    values = item["requirements"]
    if set(values) != set(DIMENSIONS):
        raise ValueError(f"{component}: requirements must declare every contract dimension")
    schema = load_dimensions(contract)
    for name, value in values.items():
        if value not in schema[name]:
            raise ValueError(f"{component}: invalid {name} capability {value!r}")
    return {"status": "UNASSESSED" if "unassessed" in values.values() else "DECLARED", "requirements": dict(values)}


def load_dimensions(contract: dict) -> dict[str, list[str]]:
    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ValueError("contract dimensions do not match required capability dimensions")
    if any(not isinstance(values, list) for values in dimensions.values()):
        raise ValueError("each capability dimension must define allowed values")
    return dimensions
