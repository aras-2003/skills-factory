"""Compare source-cited capability facts without executing candidate content.

The matcher is a transparent decision aid over structured facts. It uses
normalized exact-phrase overlap, carries source citations, and does not perform
semantic analysis or grant license/security approval.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
CORE_FACETS = ("triggers", "outputs", "domain_semantics")
FACETS = (*CORE_FACETS, "tools", "dependencies", "permissions", "conflicts")
HEX_64 = re.compile(r"^[a-f0-9]{64}$")


class CapabilityError(ValueError):
    """Invalid or insufficient comparison input."""


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _evidence_refs(value: Any, where: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise CapabilityError(f"{where} must contain at least one source citation")
    refs = []
    for index, ref in enumerate(value):
        ref_where = f"{where}[{index}]"
        if not isinstance(ref, dict):
            raise CapabilityError(f"{ref_where} must be an object")
        path = ref.get("source_path")
        if not isinstance(path, str) or "\\" in path or path.startswith("/") or ":" in path or any(ord(char) < 32 or unicodedata.category(char) == "Cf" for char in path) or any(part in {"", ".", ".."} for part in path.split("/")):
            raise CapabilityError(f"{ref_where}.source_path must be a safe repository-relative path")
        if not HEX_64.fullmatch(str(ref.get("source_sha256", ""))):
            raise CapabilityError(f"{ref_where}.source_sha256 must be a SHA-256 digest")
        start, end = ref.get("line_start"), ref.get("line_end")
        if not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or start < 1 or end < start:
            raise CapabilityError(f"{ref_where} must have a valid inclusive line range")
        refs.append({"source_path": path, "source_sha256": ref["source_sha256"], "line_start": start, "line_end": end})
    return refs


def _validate_capability(value: Any, where: str) -> tuple[str, dict[str, set[str] | None], dict[str, dict[str, list[dict[str, Any]]]]]:
    if not isinstance(value, dict):
        raise CapabilityError(f"{where} must be an object")
    identity = value.get("identity")
    if not isinstance(identity, str) or not identity.strip():
        raise CapabilityError(f"{where}.identity must be a non-empty string")
    facets = value.get("facets")
    if not isinstance(facets, dict):
        raise CapabilityError(f"{where}.facets must be an object")
    result: dict[str, set[str] | None] = {}
    refs_by_facet: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for facet in FACETS:
        if facet not in facets:
            raise CapabilityError(f"{where}.facets.{facet} must be present; use null when unknown")
        raw = facets[facet]
        if raw is None:
            result[facet] = None
            refs_by_facet[facet] = {}
            continue
        if not isinstance(raw, list):
            raise CapabilityError(f"{where}.facets.{facet} must be a list or null")
        normalized: set[str] = set()
        facet_refs: dict[str, list[dict[str, Any]]] = {}
        for index, item in enumerate(raw):
            item_where = f"{where}.facets.{facet}[{index}]"
            if not isinstance(item, dict) or not isinstance(item.get("value"), str) or not item["value"].strip():
                raise CapabilityError(f"{item_where} must have a non-empty value and cited evidence")
            key = _normalize(item["value"])
            if key in normalized:
                raise CapabilityError(f"{where}.facets.{facet} contains duplicate normalized values")
            normalized.add(key)
            facet_refs[key] = _evidence_refs(item.get("evidence"), f"{item_where}.evidence")
        result[facet] = normalized
        refs_by_facet[facet] = facet_refs
    return identity.strip(), result, refs_by_facet


def _facet_evidence(candidate: dict[str, set[str] | None], existing: dict[str, set[str] | None],
                    candidate_refs: dict[str, dict[str, list[dict[str, Any]]]],
                    existing_refs: dict[str, dict[str, list[dict[str, Any]]]]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for facet in FACETS:
        left, right = candidate[facet], existing[facet]
        if left is None or right is None:
            evidence[facet] = {"status": "UNKNOWN", "overlap": [], "candidate_only": None, "existing_only": None,
                               "overlap_evidence": {}, "candidate_only_evidence": None, "existing_only_evidence": None}
        else:
            overlap, candidate_only, existing_only = sorted(left & right), sorted(left - right), sorted(right - left)
            evidence[facet] = {
                "status": "COMPARED", "overlap": overlap, "candidate_only": candidate_only, "existing_only": existing_only,
                "overlap_evidence": {key: {"candidate": candidate_refs[facet][key], "existing": existing_refs[facet][key]} for key in overlap},
                "candidate_only_evidence": {key: candidate_refs[facet][key] for key in candidate_only},
                "existing_only_evidence": {key: existing_refs[facet][key] for key in existing_only},
            }
    return evidence



def _core_overlap_count(evidence: dict[str, dict[str, Any]]) -> int:
    return sum(bool(evidence[key]["overlap"]) for key in CORE_FACETS)


def _explicit_conflict(candidate_id: str, candidate: dict[str, set[str] | None], existing_id: str,
                        existing: dict[str, set[str] | None]) -> bool:
    candidate_conflicts, existing_conflicts = candidate["conflicts"], existing["conflicts"]
    if candidate_conflicts is None or existing_conflicts is None:
        return True
    return _normalize(existing_id) in candidate_conflicts or _normalize(candidate_id) in existing_conflicts


def compare_capabilities(candidate_raw: Any, inventory_raw: Any) -> dict[str, Any]:
    candidate_id, candidate, candidate_refs = _validate_capability(candidate_raw, "candidate")
    if not isinstance(inventory_raw, dict) or inventory_raw.get("schema_version") != SCHEMA_VERSION:
        raise CapabilityError("inventory must use schema_version 1")
    if not isinstance(inventory_raw.get("complete"), bool):
        raise CapabilityError("inventory.complete must be a boolean")
    capabilities = inventory_raw.get("capabilities")
    if not isinstance(capabilities, list):
        raise CapabilityError("inventory.capabilities must be a list")
    existing: list[tuple[str, dict[str, set[str] | None], dict[str, dict[str, list[dict[str, Any]]]]]] = []
    seen: set[str] = set()
    for index, item in enumerate(capabilities):
        identity, facets, refs = _validate_capability(item, f"inventory.capabilities[{index}]")
        key = _normalize(identity)
        if key in seen:
            raise CapabilityError("inventory contains duplicate capability identities")
        seen.add(key)
        existing.append((identity, facets, refs))

    comparisons = []
    unknown_evidence = any(candidate[facet] is None for facet in FACETS)
    exact_duplicates: list[str] = []
    compatible_matches: list[str] = []
    conflicts: list[str] = []
    for identity, facets, refs in existing:
        evidence = _facet_evidence(candidate, facets, candidate_refs, refs)
        unknown_evidence = unknown_evidence or any(facets[facet] is None for facet in FACETS)
        core_count = _core_overlap_count(evidence)
        explicit_or_unknown_conflict = _explicit_conflict(candidate_id, candidate, identity, facets)
        outputs = evidence["outputs"]
        trigger_domain_overlap = bool(evidence["triggers"]["overlap"] and evidence["domain_semantics"]["overlap"])
        disjoint_outputs = outputs["status"] == "COMPARED" and bool(outputs["candidate_only"]) and bool(outputs["existing_only"]) and not outputs["overlap"]
        inferred_conflict = trigger_domain_overlap and disjoint_outputs
        all_equal = all(candidate[key] is not None and facets[key] is not None and candidate[key] == facets[key] for key in FACETS)
        if all_equal and not explicit_or_unknown_conflict and not inferred_conflict:
            exact_duplicates.append(identity)
        elif explicit_or_unknown_conflict or inferred_conflict:
            conflicts.append(identity)
        elif core_count >= 2:
            compatible_matches.append(identity)
        comparisons.append({"identity": identity, "core_overlap_count": core_count, "evidence": evidence,
                           "conflict": explicit_or_unknown_conflict or inferred_conflict,
                           "conflict_basis": "EXPLICIT_OR_UNKNOWN_CONFLICT_DECLARATION" if explicit_or_unknown_conflict else ("SAME_TRIGGER_DOMAIN_DISJOINT_OUTPUTS" if inferred_conflict else None)})

    if unknown_evidence:
        decision, reasons, escalate = "REJECT", ["UNKNOWN_CAPABILITY_EVIDENCE"], True
    elif conflicts:
        decision, reasons, escalate = "REJECT", ["CAPABILITY_CONFLICT_REQUIRES_REVIEW"], True
    elif exact_duplicates:
        decision, reasons, escalate = "REUSE_EXISTING", ["DUPLICATE_REIMPORT_REJECTED"], False
    elif len(compatible_matches) > 1:
        decision, reasons, escalate = "COMPOSE", ["COMPLEMENTARY_MULTI_CAPABILITY_MATCH"], True
    elif len(compatible_matches) == 1:
        decision, reasons, escalate = "EXTEND", ["COMPLEMENTARY_SINGLE_CAPABILITY_MATCH"], True
    elif inventory_raw["complete"]:
        decision, reasons, escalate = "IMPORT", ["NO_COMPATIBLE_CAPABILITY_IN_COMPLETE_INVENTORY"], True
    else:
        decision, reasons, escalate = "REJECT", ["INVENTORY_INCOMPLETE"], True

    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_identity": candidate_id,
        "decision": decision,
        "reason_codes": reasons,
        "matched_capabilities": sorted(exact_duplicates + compatible_matches),
        "conflicts": sorted(conflicts),
        "escalation_required": escalate,
        "human_review_required": decision in {"IMPORT", "EXTEND", "COMPOSE", "REJECT"},
        "inventory_complete": inventory_raw["complete"],
        "candidate_facts": {
            facet: {
                "status": "UNKNOWN" if candidate[facet] is None else "COMPARED",
                "values": None if candidate[facet] is None else sorted(candidate[facet]),
                "evidence": None if candidate[facet] is None else candidate_refs[facet],
            }
            for facet in FACETS
        },
        "comparisons": sorted(comparisons, key=lambda item: _normalize(item["identity"])),
        "method_limitations": ["Compares only reviewer-supplied structured phrases using normalized exact equality.",
                               "Carries reviewer-supplied source citations but does not verify cited bytes or line ranges.",
                               "Does not infer semantic equivalence or approve license/security status."],
    }


def _load_json(path):
    try:
        if path.stat().st_size > 5_000_000:
            raise CapabilityError("JSON input exceeds the 5 MB limit")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityError(f"cannot read JSON input: {path.name}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare cited capability facts without executing candidate content.")
    parser.add_argument("--candidate", required=True, type=Path, help="candidate capability JSON")
    parser.add_argument("--inventory", required=True, type=Path, help="current capability inventory JSON")
    parser.add_argument("--output", type=Path, help="optional output file; otherwise JSON is printed")
    args = parser.parse_args(argv)
    try:
        report = compare_capabilities(_load_json(args.candidate), _load_json(args.inventory))
        encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        if args.output:
            if args.output.exists() or args.output.is_symlink():
                raise CapabilityError("output already exists; refusing to overwrite evidence")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except CapabilityError as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
