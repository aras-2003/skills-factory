#!/usr/bin/env python3
"""Reference-informed layout assignment for canonical Presentation OS DeckSpec v1.

No third-party code is imported or executed. This is a semantic planning adapter,
NOT a slide renderer or a verified consulting-design evaluator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PATTERN_FILE = Path(__file__).resolve().parents[2] / "docs/presentations/consulting-reference-patterns-v1.json"

class ContractError(ValueError):
    pass

def plan(deck: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if deck.get("schema_version") != "1.0" or not isinstance(deck.get("slides"), list):
        raise ContractError("Expected canonical Presentation DeckSpec v1 with slides")
    if not deck["slides"]:
        raise ContractError("Empty deck")
    patterns = {p["id"]: p for p in registry["patterns"]}
    sources = {s["id"]: s for s in registry["sources"]}
    seen = set()
    results = []
    for slide in deck["slides"]:
        sid = slide.get("slide_id")
        if not isinstance(sid, str) or not sid or sid in seen:
            raise ContractError("Missing or duplicate slide_id")
        seen.add(sid)
        role = slide.get("role", "").lower()
        selection = next((p for p in registry["patterns"]
                          if p["role"] == role), None)
        if selection is None:
            results.append({"slide_id": sid, "status": "NO_PATTERN",
                            "layout_id": None, "source_ids": [],
                            "checks": ["No matching reference-informed layout"]})
            continue
        claims = slide.get("claims", [])
        if not isinstance(claims, list):
            raise ContractError(f"{sid}: claims must be an array")
        checks = []
        if not claims and selection["requires_evidence"]:
            checks.append("Missing claim/evidence: block evidence-backed exhibit")
        for claim in claims:
            if not claim.get("claim_id") or claim.get("epistemic_status") not in {
                "USER_PROVIDED", "EXTERNAL_VERIFIED", "CANONICAL", "DERIVED",
                "HYPOTHESIS", "UNKNOWN", "CONTRADICTED"
            }:
                raise ContractError(f"{sid}: claim identity/status invalid")
            if claim.get("epistemic_status") == "CONTRADICTED":
                checks.append("CONTRADICTED claim requires resolution")
        for src in selection["source_ids"]:
            if src not in sources:
                raise ContractError(f"{sid}: unknown reference {src}")
        results.append({
            "slide_id": sid,
            "status": "REVIEW_REQUIRED" if checks else "PLANNED_NOT_RENDERED",
            "layout_id": selection["id"],
            "design_principle": selection["design_principle"],
            "source_ids": selection["source_ids"],
            "reference_revisions": {
                i: sources[i].get("revision") or sources[i].get("archive_sha256")
                for i in selection["source_ids"]
            },
            "checks": checks,
            "visual_review": "NOT_RUN",
            "external_skill_execution": "NOT_RUN"
        })
    return {
        "schema_version": "1.0",
        "deck_id": deck.get("deck_id"),
        "artifact_status": "SEMANTIC_PLAN_ONLY",
        "render_status": "NOT_RUN",
        "editable_export_status": "NOT_RUN",
        "reference_registry": str(PATTERN_FILE.relative_to(PATTERN_FILE.parents[2])),
        "slides": results
    }

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck", type=Path, help="Canonical DeckSpec v1 JSON")
    p.add_argument("--registry", type=Path, default=PATTERN_FILE)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    deck = json.loads(args.deck.read_text(encoding="utf-8"))
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    result = plan(deck, registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
