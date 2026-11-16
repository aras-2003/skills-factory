"""Create a read-only, evidence-bound review of a pinned external skill update.

This tool compares accepted v1 intake evidence with a proposed GitHub commit.
It never installs candidate content, edits the provenance registry, or grants
authorization. Candidate bytes are treated as inert data throughout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker

try:
    import external_skill_intake as intake
except ImportError:  # module import when loaded as scripts.security.external_skill_update
    from scripts.security import external_skill_intake as intake


TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = 1
ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SCHEMA = ROOT / "scripts/validate/schemas/external-skill-intake.schema.json"
REPORT_SCHEMA = ROOT / "scripts/validate/schemas/external-skill-update-impact.schema.json"
REGISTRY_SCHEMA = ROOT / "scripts/validate/schemas/provenance-registry.schema.json"
DEPRECATION_MARKERS = {
    "DEPRECATED": re.compile(r"\bdeprecated\b", re.I),
    "OBSOLETE": re.compile(r"\bobsolete\b", re.I),
    "REMOVED": re.compile(r"\bremoved\b", re.I),
    "END_OF_LIFE": re.compile(r"\b(?:end[ -]of[ -]life|eol)\b", re.I),
    "SUNSET": re.compile(r"\bsunset\b", re.I),
}
LICENSE_NAMES = intake.LICENSE_NAMES


class UpdateError(ValueError):
    """Input evidence is invalid or cannot be verified safely."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_digest(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _schema_errors(instance: Any, schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda error: list(map(str, error.absolute_path))) ]


def _validate_snapshot(receipt: dict[str, Any], source: dict[str, Any], files: dict[str, bytes]) -> None:
    errors = _schema_errors(receipt, RECEIPT_SCHEMA)
    if errors:
        raise UpdateError("accepted receipt is invalid: " + "; ".join(errors[:4]))
    try:
        repository, commit, subdir = intake.validate_github_identity(
            source.get("repository"), source.get("commit"), source.get("subdir")
        )
    except (intake.IntakeError, AttributeError) as exc:
        raise UpdateError("accepted baseline must be pinned to a full-SHA GitHub source") from exc
    receipt_source = receipt["source"]
    if (
        receipt_source.get("type") != "github_repository"
        or receipt_source.get("repository") != repository
        or receipt_source.get("commit") != commit
        or receipt_source.get("subdir") != subdir
        or receipt_source.get("source_digest") != source.get("source_digest")
    ):
        raise UpdateError("fetched source identity does not match the accepted receipt")
    rows = receipt.get("files")
    if not isinstance(rows, list):
        raise UpdateError("accepted receipt has no file inventory")
    expected = {row["path"]: (row["size_bytes"], row["sha256"]) for row in rows}
    actual = {path: (len(data), _digest(data)) for path, data in files.items()}
    if expected != actual:
        raise UpdateError("pinned source inventory does not match the accepted receipt")
    if intake._source_inventory_digest(intake._inventory_rows(files)) != receipt.get("inventory_sha256"):
        raise UpdateError("pinned source inventory digest does not match the accepted receipt")


def _normalized_tool_declarations(files: dict[str, bytes]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    result: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path, data in sorted(files.items()):
        if PurePosixPath(path).name != "SKILL.md":
            continue
        if len(data) > intake.MAX_FRONTMATTER_BYTES:
            errors.append(f"{path}: frontmatter exceeds the configured limit")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path}: skill source is not UTF-8")
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            errors.append(f"{path}: frontmatter is missing")
            continue
        try:
            end = next(index for index in range(1, len(lines)) if lines[index] == "---")
        except StopIteration:
            errors.append(f"{path}: frontmatter is not closed")
            continue
        raw = "\n".join(lines[1:end])
        try:
            from yaml.tokens import AliasToken, AnchorToken
            if any(isinstance(token, (AliasToken, AnchorToken)) for token in yaml.scan(raw)):
                errors.append(f"{path}: YAML aliases are not accepted")
                continue
            metadata = yaml.safe_load(raw)
        except Exception:
            errors.append(f"{path}: frontmatter could not be parsed safely")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{path}: frontmatter must be a mapping")
            continue
        declarations: dict[str, Any] = {}
        declarations_supported = True
        for key in ("allowed-tools", "tools"):
            if key in metadata:
                value = metadata[key]
                if isinstance(value, str):
                    if len(value) > 4096:
                        errors.append(f"{path}: tool declaration exceeds the configured limit")
                        declarations_supported = False
                        break
                elif isinstance(value, list) and len(value) <= 100 and all(isinstance(item, str) and len(item) <= 256 for item in value):
                    pass
                else:
                    errors.append(f"{path}: tool declaration has an unsupported shape")
                    declarations_supported = False
                    break
                declarations[key] = value
        if not declarations_supported:
            continue
        try:
            canonical = json.dumps(declarations, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError):
            errors.append(f"{path}: tool declarations have an unsupported value")
            continue
        if len(canonical) > 16_384:
            errors.append(f"{path}: tool declarations exceed the configured limit")
            continue
        result[path] = {"sha256": _digest(canonical), "declarations": declarations}
    return result, errors


def _deprecation_counts(files: dict[str, bytes]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for path, data in sorted(files.items()):
        if b"\x00" in data[:4096]:
            continue
        text = data.decode("utf-8", errors="ignore")
        markers = {name: sum(1 for _match in pattern.finditer(text)) for name, pattern in DEPRECATION_MARKERS.items()}
        markers = {name: min(count, 10_000) for name, count in markers.items() if count}
        if markers:
            counts[path] = markers
    return counts


def _consumer_impact(registry: dict[str, Any], registry_digest: str, baseline: dict[str, Any]) -> dict[str, Any]:
    records = registry.get("records", []) if isinstance(registry, dict) else []
    upstream = baseline["source"]
    repository = upstream["repository"]
    commit = upstream["commit"]
    subdir = upstream.get("subdir") or ""
    baseline_content = baseline["inventory_sha256"]
    anchor_sources: set[str] = set()
    for row in records:
        ref = row.get("upstream") if isinstance(row, dict) else None
        if not isinstance(ref, dict):
            continue
        parsed = urlsplit(str(ref.get("url") or ""))
        path_parts = [part for part in parsed.path.split("/") if part]
        ref_repository = "/".join(path_parts[:2]) if parsed.hostname == "github.com" else ""
        ref_path = str(ref.get("path") or "").strip("/")
        if (
            ref.get("provider") == "github"
            and ref_repository.casefold() == repository.casefold()
            and ref.get("commit") == commit
            and ref_path == subdir
            and ref.get("content_sha256") == baseline_content
        ):
            anchor_sources.add(str(row.get("source")))

    reverse: dict[str, set[str]] = {}
    forward: dict[str, set[str]] = {}
    graph_errors: list[str] = []
    unknown_records: list[str] = []
    known_sources = [row.get("source") for row in records if isinstance(row, dict) and isinstance(row.get("source"), str)]
    source_set = set(known_sources)
    if len(source_set) != len(known_sources):
        graph_errors.append("registry contains duplicate source identities")
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("source"), str):
            graph_errors.append("registry contains a malformed record")
            continue
        source = row["source"]
        if row.get("classification") == "UNKNOWN" or row.get("verification", {}).get("state") != "VERIFIED":
            unknown_records.append(source)
        edges = row.get("dependencies")
        components = row.get("components")
        if not isinstance(edges, list) or not isinstance(components, list):
            graph_errors.append(f"{source}: dependency or component lineage is unavailable")
            continue
        for target in set(edges + components):
            if not isinstance(target, str):
                graph_errors.append(f"{source}: dependency edge is malformed")
                continue
            if target == source or target not in source_set:
                graph_errors.append(f"{source}: dependency target is self-referential or missing")
                continue
            reverse.setdefault(target, set()).add(source)
            forward.setdefault(source, set()).add(target)

    cycle_nodes: set[str] = set()
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            cycle_nodes.add(node)
            return
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(forward.get(node, set())):
            if child in visiting:
                cycle_nodes.update((node, child))
            else:
                visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(forward):
        visit(node)
    if cycle_nodes:
        graph_errors.append("dependency/component cycle detected: " + ", ".join(sorted(cycle_nodes)[:10]))

    queue: deque[str] = deque(sorted(anchor_sources))
    visited = set(anchor_sources)
    direct: set[str] = set()
    all_consumers: set[str] = set()
    while queue:
        target = queue.popleft()
        for consumer in sorted(reverse.get(target, set())):
            if target in anchor_sources and consumer not in visited:
                direct.add(consumer)
            if consumer in visited:
                continue
            visited.add(consumer)
            all_consumers.add(consumer)
            queue.append(consumer)
    transitive = all_consumers - direct
    complete = bool(anchor_sources) and not graph_errors and not unknown_records
    return {
        "status": "COMPLETE" if complete else "UNKNOWN",
        "complete": complete,
        "registry_sha256": registry_digest,
        "anchor_sources": sorted(anchor_sources),
        "direct_consumers": sorted(direct),
        "transitive_consumers": sorted(transitive),
        "unclassified_records": sorted(unknown_records),
        "errors": sorted({error[:200] for error in graph_errors}),
    }


def _file_changes(before: dict[str, bytes], after: dict[str, bytes]) -> dict[str, list[dict[str, Any]]]:
    old_rows = {path: {"size_bytes": len(data), "sha256": _digest(data)} for path, data in before.items()}
    new_rows = {path: {"size_bytes": len(data), "sha256": _digest(data)} for path, data in after.items()}
    added = [{"path": path, **new_rows[path]} for path in sorted(new_rows.keys() - old_rows.keys())]
    removed = [{"path": path, **old_rows[path]} for path in sorted(old_rows.keys() - new_rows.keys())]
    changed = [
        {"path": path, "before": old_rows[path], "after": new_rows[path]}
        for path in sorted(old_rows.keys() & new_rows.keys())
        if old_rows[path] != new_rows[path]
    ]
    return {"added": added, "removed": removed, "changed": changed}


def _license_diff(before: dict[str, bytes], after: dict[str, bytes], baseline_decision: str, unchanged: bool) -> dict[str, Any]:
    def rows(files: dict[str, bytes]) -> dict[str, str]:
        return {path: _digest(data) for path, data in sorted(files.items()) if PurePosixPath(path).name.casefold() in LICENSE_NAMES}
    old, new = rows(before), rows(after)
    changed = sorted(path for path in old.keys() & new.keys() if old[path] != new[path])
    return {
        "before": [{"path": path, "sha256": old[path]} for path in sorted(old)],
        "after": [{"path": path, "sha256": new[path]} for path in sorted(new)],
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "changed": changed,
        "decision": baseline_decision if unchanged else "REVIEW_REQUIRED",
    }


def build_update_report(
    *, baseline_receipt: dict[str, Any], baseline_review: dict[str, Any],
    baseline_source: dict[str, Any], baseline_files: dict[str, bytes], baseline_modes: dict[str, int | None],
    candidate_source: dict[str, Any] | None, candidate_files: dict[str, bytes] | None,
    candidate_modes: dict[str, int | None] | None, registry: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic review report from two already fetched snapshots."""
    _validate_snapshot(baseline_receipt, baseline_source, baseline_files)
    _validate_modes(baseline_files, baseline_modes)
    review_valid, review_errors = intake.validate_review_authorization(baseline_receipt, baseline_review)
    if not review_valid:
        raise UpdateError("accepted baseline lacks a valid approval: " + "; ".join(review_errors))
    registry_errors = _schema_errors(registry, REGISTRY_SCHEMA)
    registry_digest = _canonical_digest(registry)
    blockers: list[str] = []
    if registry_errors:
        blockers.append("REGISTRY_INVALID")
        impact = {"status": "UNKNOWN", "complete": False, "registry_sha256": registry_digest, "anchor_sources": [], "direct_consumers": [], "transitive_consumers": [], "unclassified_records": [], "errors": [error[:200] for error in registry_errors[:10]]}
    else:
        impact = _consumer_impact(registry, registry_digest, baseline_receipt)
        if not impact["anchor_sources"]:
            blockers.append("ACCEPTED_LINEAGE_NOT_FOUND")
        if not impact["complete"]:
            blockers.append("CONSUMER_LINEAGE_INCOMPLETE")

    baseline_inventory = baseline_receipt["inventory_sha256"]
    if candidate_source is None or candidate_files is None:
        comparison = "BLOCKED"
        candidate = {"repository": baseline_source["repository"], "commit": None, "subdir": baseline_source.get("subdir"), "source_digest": None, "inventory_sha256": None}
        changes = {"added": [], "removed": [], "changed": []}
        permission_changes = {
            "changed_paths": [], "before": [], "after": [], "baseline_status": "UNKNOWN",
            "candidate_status": "UNKNOWN", "errors": [],
        }
        resource_changes = {"added": [], "removed": [], "changed": []}
        license = _license_diff(baseline_files, {}, baseline_review["license_decision"], False)
        deprecations: list[dict[str, Any]] = []
        mode_changes = {"status": "UNKNOWN", "added": [], "removed": [], "changed": []}
        blockers.extend(("CANDIDATE_SOURCE_UNAVAILABLE", "EXECUTABLE_MODE_UNKNOWN"))
    else:
        try:
            candidate_repository, candidate_commit, candidate_subdir = intake.validate_github_identity(
                candidate_source.get("repository"), candidate_source.get("commit"), candidate_source.get("subdir")
            )
        except (intake.IntakeError, AttributeError) as exc:
            raise UpdateError("candidate must use a full-SHA GitHub source identity") from exc
        if candidate_source.get("type") != "github_repository" or not re.fullmatch(r"[a-f0-9]{64}", str(candidate_source.get("source_digest"))):
            raise UpdateError("candidate source digest or provider identity is invalid")
        _validate_file_inventory(candidate_files)
        _validate_modes(candidate_files, candidate_modes)
        candidate_inventory = intake._source_inventory_digest(intake._inventory_rows(candidate_files))
        candidate = {
            "repository": candidate_repository,
            "commit": candidate_commit,
            "subdir": candidate_subdir,
            "source_digest": candidate_source.get("source_digest"),
            "inventory_sha256": candidate_inventory,
        }
        exact_pin = all(candidate.get(key) == baseline_source.get(key) for key in ("repository", "commit", "subdir"))
        unchanged = exact_pin and candidate_inventory == baseline_inventory and candidate_source.get("source_digest") == baseline_source.get("source_digest")
        comparison = "UNCHANGED" if unchanged else "REVIEW_REQUIRED"
        changes = _file_changes(baseline_files, candidate_files)
        base_permissions, base_permission_errors = _normalized_tool_declarations(baseline_files)
        new_permissions, new_permission_errors = _normalized_tool_declarations(candidate_files)
        permission_paths = sorted(path for path in base_permissions.keys() | new_permissions.keys() if base_permissions.get(path) != new_permissions.get(path))
        permission_changes = {
            "changed_paths": permission_paths,
            "before": [{"path": path, "sha256": base_permissions[path]["sha256"]} for path in sorted(base_permissions)],
            "after": [{"path": path, "sha256": new_permissions[path]["sha256"]} for path in sorted(new_permissions)],
            "baseline_status": "UNKNOWN" if base_permission_errors else "KNOWN",
            "candidate_status": "UNKNOWN" if new_permission_errors else "KNOWN",
            "errors": [error[:200] for error in (base_permission_errors + new_permission_errors)[:20]],
        }
        if base_permission_errors or new_permission_errors:
            blockers.append("TOOL_PERMISSION_PARSE_UNKNOWN")
        excluded = {"SKILL.md", "README.md"}
        def is_resource(path: str) -> bool:
            name = PurePosixPath(path).name
            return name not in excluded and name.casefold() not in LICENSE_NAMES
        resource_changes = {
            key: [row for row in values if is_resource(row["path"])]
            for key, values in changes.items()
        }
        old_markers, new_markers = _deprecation_counts(baseline_files), _deprecation_counts(candidate_files)
        deprecations = [
            {"path": path, "before": old_markers.get(path, {}), "after": new_markers.get(path, {})}
            for path in sorted(old_markers.keys() | new_markers.keys())
            if old_markers.get(path, {}) != new_markers.get(path, {})
        ]
        base_mode_map = baseline_modes or {}
        new_mode_map = candidate_modes or {}
        mode_unknown = any(base_mode_map.get(path) is None for path in baseline_files) or any(new_mode_map.get(path) is None for path in candidate_files)
        common_mode_paths = base_mode_map.keys() & new_mode_map.keys()
        mode_changes = {
            "status": "UNKNOWN" if mode_unknown else "COMPLETE",
            "added": [
                {"path": path, "mode": new_mode_map[path], "executable": bool(new_mode_map[path] & 0o111) if new_mode_map[path] is not None else None}
                for path in sorted(new_mode_map.keys() - base_mode_map.keys())
            ],
            "removed": [
                {"path": path, "mode": base_mode_map[path], "executable": bool(base_mode_map[path] & 0o111) if base_mode_map[path] is not None else None}
                for path in sorted(base_mode_map.keys() - new_mode_map.keys())
            ],
            "changed": [
                {"path": path, "before_mode": base_mode_map[path], "after_mode": new_mode_map[path], "before_executable": bool(base_mode_map[path] & 0o111), "after_executable": bool(new_mode_map[path] & 0o111)}
                for path in sorted(common_mode_paths)
                if base_mode_map[path] is not None and new_mode_map[path] is not None and base_mode_map[path] != new_mode_map[path]
            ],
        }
        if mode_unknown:
            blockers.append("EXECUTABLE_MODE_UNKNOWN")
        license = _license_diff(baseline_files, candidate_files, baseline_review["license_decision"], unchanged)
    readiness = "BLOCKED" if blockers else ("NOT_READY" if comparison == "REVIEW_REQUIRED" else "UNCHANGED")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "status": readiness,
        "comparison_status": comparison,
        "review_required": comparison != "UNCHANGED",
        "baseline": {
            "repository": baseline_source["repository"], "commit": baseline_source["commit"],
            "subdir": baseline_source.get("subdir"), "source_digest": baseline_source["source_digest"],
            "inventory_sha256": baseline_inventory, "receipt_sha256": intake.receipt_digest(baseline_receipt),
            "review_sha256": _canonical_digest(baseline_review),
        },
        "candidate": candidate,
        "registry_sha256": registry_digest,
        "inventory_diff": changes,
        "permission_changes": permission_changes,
        "license_changes": license,
        "resource_changes": resource_changes,
        "deprecation_signals": deprecations,
        "executable_mode": mode_changes,
        "consumer_impact": impact,
        "blockers": sorted(set(blockers)),
        "authorization_state": "NOT_AUTHORIZED",
    }


def _validate_file_inventory(files: dict[str, bytes]) -> None:
    try:
        intake._validate_file_paths(files)
    except intake.IntakeError as exc:
        raise UpdateError("candidate inventory is unsafe") from exc


def _validate_modes(files: dict[str, bytes], modes: dict[str, int | None] | None) -> None:
    if modes is None or not isinstance(modes, dict) or set(modes) != set(files):
        raise UpdateError("executable mode inventory does not match the source files")
    if any(value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 0o7777) for value in modes.values()):
        raise UpdateError("executable mode inventory contains an invalid permission value")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError("input JSON is unavailable or invalid") from exc


def _baseline_unavailable_report(receipt: dict[str, Any], review: dict[str, Any], registry: Any, candidate: dict[str, Any], error_type: str, blocker: str = "BASELINE_SOURCE_UNAVAILABLE") -> dict[str, Any]:
    errors = _schema_errors(receipt, RECEIPT_SCHEMA)
    if errors:
        raise UpdateError("accepted receipt is invalid: " + "; ".join(errors[:4]))
    review_valid, review_errors = intake.validate_review_authorization(receipt, review)
    if not review_valid:
        raise UpdateError("accepted baseline lacks a valid approval: " + "; ".join(review_errors))
    source = receipt["source"]
    registry_digest = _canonical_digest(registry)
    registry_errors = _schema_errors(registry, REGISTRY_SCHEMA)
    blockers = [blocker, "CONSUMER_LINEAGE_INCOMPLETE", "EXECUTABLE_MODE_UNKNOWN"]
    if registry_errors:
        blockers.append("REGISTRY_INVALID")
    return {
        "schema_version": SCHEMA_VERSION, "tool_version": TOOL_VERSION, "status": "BLOCKED", "comparison_status": "BLOCKED", "review_required": True,
        "baseline": {
            "repository": source["repository"], "commit": source["commit"], "subdir": source.get("subdir"),
            "source_digest": source["source_digest"], "inventory_sha256": receipt["inventory_sha256"],
            "receipt_sha256": intake.receipt_digest(receipt), "review_sha256": _canonical_digest(review),
        },
        "candidate": {"repository": candidate["repository"], "commit": candidate["commit"], "subdir": candidate.get("subdir"), "source_digest": None, "inventory_sha256": None},
        "registry_sha256": registry_digest,
        "inventory_diff": {"added": [], "removed": [], "changed": []},
        "permission_changes": {"changed_paths": [], "before": [], "after": [], "baseline_status": "UNKNOWN", "candidate_status": "UNKNOWN", "errors": []},
        "license_changes": {
            "before": receipt.get("license_evidence", []), "after": [], "added": [], "removed": [], "changed": [], "decision": "UNKNOWN",
        },
        "resource_changes": {"added": [], "removed": [], "changed": []}, "deprecation_signals": [],
        "executable_mode": {"status": "UNKNOWN", "added": [], "removed": [], "changed": []},
        "consumer_impact": {"status": "UNKNOWN", "complete": False, "registry_sha256": registry_digest, "anchor_sources": [], "direct_consumers": [], "transitive_consumers": [], "unclassified_records": [], "errors": [error[:200] for error in (["accepted source could not be re-fetched and verified"] + registry_errors[:9])]},
        "blockers": blockers,
        "candidate_fetch_error": error_type, "authorization_state": "NOT_AUTHORIZED",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-receipt", type=Path, required=True)
    parser.add_argument("--baseline-review", type=Path, required=True)
    parser.add_argument("--candidate-repository", required=True)
    parser.add_argument("--candidate-commit", required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--candidate-subdir")
    target.add_argument("--candidate-root", action="store_true", help="compare the repository root instead of the accepted baseline subdirectory")
    parser.add_argument("--registry", type=Path, default=ROOT / "provenance/registry.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        baseline_receipt = _read_json(args.baseline_receipt)
        baseline_review = _read_json(args.baseline_review)
        if not isinstance(baseline_receipt, dict) or not isinstance(baseline_review, dict):
            raise UpdateError("baseline receipt and review must be JSON objects")
        baseline_ref = baseline_receipt.get("source") or {}
        if not isinstance(baseline_ref, dict) or baseline_ref.get("type") != "github_repository":
            raise UpdateError("baseline receipt is not a GitHub-pinned intake receipt")
        requested_subdir = None if args.candidate_root else (args.candidate_subdir if args.candidate_subdir is not None else baseline_ref.get("subdir"))
        repository, commit, subdir = intake.validate_github_identity(args.candidate_repository, args.candidate_commit, requested_subdir)
        candidate_identity = {"repository": repository, "commit": commit, "subdir": subdir}
        try:
            registry = yaml.safe_load(args.registry.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            registry = None
        try:
            baseline_source, baseline_files, baseline_modes = intake.fetch_github_source_with_modes(
                baseline_ref.get("repository"), baseline_ref.get("commit"), baseline_ref.get("subdir")
            )
        except (intake.IntakeError, OSError) as exc:
            report = _baseline_unavailable_report(baseline_receipt, baseline_review, registry, candidate_identity, type(exc).__name__)
            errors = _schema_errors(report, REPORT_SCHEMA)
            if errors:
                raise UpdateError("generated report failed schema validation: " + "; ".join(errors[:4]))
            sys.stdout.buffer.write(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
            return 2
        try:
            _validate_snapshot(baseline_receipt, baseline_source, baseline_files)
        except UpdateError as exc:
            blocker = "BASELINE_DIGEST_MISMATCH" if "digest does not match" in str(exc) or "inventory does not match" in str(exc) else "BASELINE_SOURCE_INVALID"
            report = _baseline_unavailable_report(baseline_receipt, baseline_review, registry, candidate_identity, type(exc).__name__, blocker)
            errors = _schema_errors(report, REPORT_SCHEMA)
            if errors:
                raise UpdateError("generated report failed schema validation: " + "; ".join(errors[:4]))
            sys.stdout.buffer.write(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
            return 2
        try:
            candidate_source, candidate_files, candidate_modes = intake.fetch_github_source_with_modes(
                repository, commit, subdir
            )
        except (intake.IntakeError, OSError) as exc:
            candidate_source = candidate_files = candidate_modes = None
            fetch_error = type(exc).__name__
        else:
            fetch_error = None
        report = build_update_report(
            baseline_receipt=baseline_receipt, baseline_review=baseline_review,
            baseline_source=baseline_source, baseline_files=baseline_files, baseline_modes=baseline_modes,
            candidate_source=candidate_source, candidate_files=candidate_files, candidate_modes=candidate_modes,
            registry=registry,
        )
        if fetch_error:
            report["candidate"].update(candidate_identity)
            report["candidate_fetch_error"] = fetch_error
            report["status"] = "BLOCKED"
            report["comparison_status"] = "BLOCKED"
            report["review_required"] = True
            report["blockers"] = sorted(set(report["blockers"] + ["CANDIDATE_SOURCE_UNAVAILABLE"]))
        errors = _schema_errors(report, REPORT_SCHEMA)
        if errors:
            raise UpdateError("generated report failed schema validation: " + "; ".join(errors[:4]))
        sys.stdout.buffer.write(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
        return 0 if report["status"] != "BLOCKED" else 2
    except (UpdateError, intake.IntakeError, OSError, ValueError) as exc:
        print(f"external update review blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
