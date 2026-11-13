from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_VERSION = 1
REGISTRY_PATH = Path("provenance/registry.yaml")
SCHEMA_PATH = Path("scripts/validate/schemas/provenance-registry.schema.json")


def discover_sources(root: Path) -> list[dict[str, str]]:
    """Return every current skill/workflow source in stable path order."""
    registry_path = root / "workflows" / "runtime-registry.yaml"
    workflow_registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    workflow_by_path = {
        str(item.get("workflow")): item
        for item in workflow_registry.get("workflows", [])
        if isinstance(item, dict) and item.get("workflow")
    }
    rows: list[dict[str, str]] = []
    for path in sorted((root / "skills").rglob("SKILL.md")):
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{path}: missing delimited YAML frontmatter")
        frontmatter = yaml.safe_load(text[4:].split("\n---\n", 1)[0]) or {}
        if not isinstance(frontmatter, dict):
            raise ValueError(f"{path}: frontmatter must be a mapping")
        metadata = frontmatter.get("metadata") or {}
        source = path.relative_to(root).as_posix()
        rows.append({
            "kind": "skill", "name": str(frontmatter.get("name") or path.parent.name),
            "source": source, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "owner": str(metadata.get("owner") or "unassigned"),
        })
    for path in sorted((root / "workflows").rglob("WORKFLOW.md")):
        source = path.relative_to(root).as_posix()
        entry = workflow_by_path.get(source)
        metadata = (entry or {}).get("metadata") or {}
        rows.append({
            "kind": "workflow", "name": str((entry or {}).get("name") or path.parent.name),
            "source": source, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "owner": str(metadata.get("owner") or "unassigned"),
        })
    return sorted(rows, key=lambda item: (item["kind"], item["source"]))


def _unknown_record(source: dict[str, str]) -> dict[str, Any]:
    return {
        "kind": source["kind"],
        "name": source["name"],
        "source": source["source"],
        "source_sha256": source["source_sha256"],
        "classification": "UNKNOWN",
        "upstream": None,
        "components": [],
        "dependencies": [],
        "basis_evidence": [],
        "local_modifications": {"status": "UNKNOWN", "items": []},
        "license": {"status": "UNKNOWN", "spdx_id": None, "attribution": []},
        "update_policy": "MANUAL_REVIEW",
        "verification": {"state": "NOT_CLASSIFIED", "reviewed_at": None, "owner": source["owner"]},
    }


def migrate_registry(root: Path) -> dict[str, Any]:
    """Build a deterministic registry, preserving reviewed classifications.

    New records are UNKNOWN. Existing records retain their reviewed provenance
    fields while identity and local content digest are refreshed from source.
    Stale records are kept so inventory validation can require explicit review.
    """
    path = root / REGISTRY_PATH
    old = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    old_rows = old.get("records", []) if isinstance(old, dict) else []
    existing = {str(item.get("source")): item for item in old_rows if isinstance(item, dict) and item.get("source")}
    sources = discover_sources(root)
    result = []
    for source in sources:
        row = dict(existing.get(source["source"]) or _unknown_record(source))
        row.update({key: source[key] for key in ("kind", "name", "source", "source_sha256")})
        if row.get("classification") == "UNKNOWN":
            verification = dict(row.get("verification") or {})
            verification.update({"state": "NOT_CLASSIFIED", "reviewed_at": None, "owner": source["owner"]})
            row["verification"] = verification
        result.append(row)
    stale = sorted(set(existing) - {item["source"] for item in sources})
    result.extend(existing[item] for item in stale)
    return {"schema_version": SCHEMA_VERSION, "records": result}


def registry_errors(registry: object, root: Path, *, check_inventory: bool = True) -> list[str]:
    errors: list[str] = []
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(registry), key=lambda item: list(map(str, item.path))):
        location = "/".join(map(str, error.absolute_path)) or "$"
        errors.append(f"schema {location}: {error.message}")
    if errors or not isinstance(registry, dict):
        return errors

    rows = registry["records"]
    by_source: dict[str, dict[str, Any]] = {}
    identities: set[tuple[str, str]] = set()
    for row in rows:
        source = row["source"]
        identity = (row["kind"], row["name"])
        if source in by_source:
            errors.append(f"duplicate source path: {source}")
        if identity in identities:
            errors.append(f"duplicate {row['kind']} name: {row['name']}")
        by_source[source] = row
        identities.add(identity)
        source_path = Path(source)
        if source_path.is_absolute() or ".." in source_path.parts:
            errors.append(f"unsafe source path: {source}")
            continue
        expected_suffix = "SKILL.md" if row["kind"] == "skill" else "WORKFLOW.md"
        expected_root = "skills" if row["kind"] == "skill" else "workflows"
        if len(source_path.parts) < 3 or source_path.parts[0] != expected_root or source_path.name != expected_suffix:
            errors.append(f"{source}: source path does not match kind {row['kind']}")
            continue
        target = root / source_path
        if target.is_symlink():
            errors.append(f"source must not be a symlink: {source}")
        elif not target.is_file():
            errors.append(f"missing source: {source}")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != row["source_sha256"]:
            errors.append(f"stale source_sha256: {source}; rerun scripts/provenance/migrate.py")
        known_sources = {item["source"] for item in rows}
        for component in row["components"]:
            if component not in known_sources:
                errors.append(f"{source}: unknown composed component: {component}")
            elif component == source:
                errors.append(f"{source}: composition cannot reference itself")
        for dependency in row["dependencies"]:
            if dependency not in known_sources:
                errors.append(f"{source}: unknown dependency: {dependency}")
            elif dependency == source:
                errors.append(f"{source}: source cannot depend on itself")

    if check_inventory:
        expected = {item["source"] for item in discover_sources(root)}
        actual = set(by_source)
        errors.extend(f"unclassified source missing from registry: {item}" for item in sorted(expected - actual))
        errors.extend(
            f"stale registry source requires explicit reconciliation: {item}"
            for item in sorted(actual - expected)
        )

    for row in rows:
        if row["classification"] == "COMPOSED":
            for component in row["components"]:
                if component not in by_source:
                    errors.append(f"{row['source']}: missing component record: {component}")
    if not errors:
        graph = {row["source"]: row["components"] for row in rows}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(source: str) -> None:
            if source in visiting:
                errors.append(f"composition cycle detected at: {source}")
                return
            if source in visited:
                return
            visiting.add(source)
            for child in graph.get(source, []):
                if child in graph:
                    visit(child)
            visiting.remove(source)
            visited.add(source)

        for source in graph:
            visit(source)
    return sorted(set(errors))


def load_registry(root: Path, *, check_inventory: bool = True) -> dict[str, Any]:
    path = root / REGISTRY_PATH
    registry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = registry_errors(registry, root, check_inventory=check_inventory)
    if errors:
        raise ValueError("invalid provenance registry:\n- " + "\n- ".join(errors))
    return registry


def registry_digest(registry: dict[str, Any]) -> str:
    canonical = json.dumps(registry, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def migration_audit(registry: dict[str, Any]) -> dict[str, Any]:
    records = registry["records"]
    inventory = [
        {key: row[key] for key in ("kind", "name", "source", "source_sha256")}
        for row in sorted(records, key=lambda item: (item["kind"], item["source"]))
    ]
    counts: dict[str, dict[str, int]] = {kind: {} for kind in ("skill", "workflow")}
    for row in records:
        kind_counts = counts[row["kind"]]
        kind_counts[row["classification"]] = kind_counts.get(row["classification"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETE",
        "record_count": len(records),
        "skill_count": sum(counts["skill"].values()),
        "workflow_count": sum(counts["workflow"].values()),
        "classification_counts": counts,
        "registry_sha256": registry_digest(registry),
        "source_inventory_sha256": hashlib.sha256(
            json.dumps(inventory, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "interpretation": (
            "Every current source has a record. UNKNOWN is explicit and carries no ownership, "
            "upstream, attribution, or license claim."
        ),
        "external_sources_executed": False,
    }


def _project_record(
    record: dict[str, Any],
    by_source: dict[str, dict[str, Any]],
    ancestors: frozenset[str],
    *,
    include_identity: bool,
) -> dict[str, Any]:
    source = record["source"]
    if source in ancestors:
        raise ValueError(f"composition cycle detected while projecting {source}")
    lineage = ancestors | {source}
    components = []
    for component_source in record["components"]:
        child = by_source.get(component_source)
        if child is None:
            raise ValueError(f"cannot project component lineage without its canonical record: {component_source}")
        components.append(_project_record(child, by_source, lineage, include_identity=True))
    result = {
        "schema_version": SCHEMA_VERSION,
        "classification": record["classification"],
        "source": source,
        "source_sha256": record["source_sha256"],
        "upstream": record["upstream"],
        "components": components,
        "dependencies": list(record["dependencies"]),
        "basis_evidence": list(record["basis_evidence"]),
        "local_modifications": dict(record["local_modifications"]),
        "license": dict(record["license"]),
        "update_policy": record["update_policy"],
        "verification": dict(record["verification"]),
    }
    if include_identity:
        result["kind"] = record["kind"]
        result["name"] = record["name"]
    return result


def projection(record: dict[str, Any], by_source: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return the public, channel-neutral fields consumed by catalogs/manifests."""
    return _project_record(record, by_source or {}, frozenset(), include_identity=False)


def records_by_source(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source"]: row for row in registry["records"]}


def records_by_identity(registry: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["kind"], row["name"]): row for row in registry["records"]}


def enrich_capabilities(capabilities: list[dict[str, Any]], registry: dict[str, Any]) -> None:
    by_identity = records_by_identity(registry)
    by_source = records_by_source(registry)
    for item in capabilities:
        key = (str(item.get("kind") or ""), str(item.get("name") or ""))
        record = by_identity.get(key)
        if record is None:
            raise ValueError(f"missing provenance record for {key[0]} {key[1]}")
        item["provenance"] = projection(record, by_source)


def provenance_metadata(registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "provenance_schema_version": registry["schema_version"],
        "provenance_registry_sha256": registry_digest(registry),
    }
