from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from common import ValidationIssue, load_json, repo_root_from


SCHEMA_RELATIVE = Path("docs/presentations/canonical-deck-v1.schema.json")
EXAMPLE_RELATIVE = Path("docs/presentations/examples/canonical-deck-v1.json")


def _unique(values: list[str], location: str, issues: list[ValidationIssue]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            issues.append(ValidationIssue("blocker", location, f"Duplicate ID: {value}"))
        seen.add(value)


def validate_deck(deck: Any, schema: dict, location: str = "<deck>") -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(deck), key=lambda e: (list(map(str, e.path)), e.message)):
        where = ".".join(str(part) for part in error.path)
        suffix = f" at {where}" if where else ""
        issues.append(ValidationIssue("blocker", location, f"Canonical deck schema violation{suffix}: {error.message}"))
    if not isinstance(deck, dict) or not isinstance(deck.get("slides"), list):
        return issues

    source_ids = [item["source_id"] for item in deck.get("sources", []) if isinstance(item, dict) and isinstance(item.get("source_id"), str)]
    _unique(source_ids, location, issues)
    known_sources = set(source_ids)
    slide_ids: list[str] = []
    for slide_index, slide in enumerate(deck["slides"]):
        if not isinstance(slide, dict):
            continue
        slide_id = slide.get("slide_id", f"slides[{slide_index}]")
        if isinstance(slide_id, str):
            slide_ids.append(slide_id)
        claims = slide.get("claims", [])
        data_refs = slide.get("data_refs", [])
        exhibits = slide.get("exhibits", [])
        _unique([x["claim_id"] for x in claims if isinstance(x, dict) and isinstance(x.get("claim_id"), str)], f"{location}:{slide_id}.claims", issues)
        _unique([x["data_ref_id"] for x in data_refs if isinstance(x, dict) and isinstance(x.get("data_ref_id"), str)], f"{location}:{slide_id}.data_refs", issues)
        _unique([x["exhibit_id"] for x in exhibits if isinstance(x, dict) and isinstance(x.get("exhibit_id"), str)], f"{location}:{slide_id}.exhibits", issues)
        data_ids = {x.get("data_ref_id") for x in data_refs if isinstance(x, dict)}
        for exhibit_index, exhibit in enumerate(exhibits):
            if not isinstance(exhibit, dict):
                continue
            for ref_id in exhibit.get("supported_data", []):
                if ref_id not in data_ids:
                    issues.append(ValidationIssue("blocker", location, f"{slide_id}.exhibits[{exhibit_index}] references missing data_ref_id {ref_id!r}"))
            target_slide = exhibit.get("slide_id")
            if target_slide is not None and target_slide != slide_id:
                issues.append(ValidationIssue("blocker", location, f"Exhibit {exhibit.get('exhibit_id')} slide_id {target_slide!r} does not match containing slide {slide_id!r}"))
        if known_sources:
            referenced_sources: set[str] = set()
            for claim in claims:
                if isinstance(claim, dict):
                    referenced_sources.update(claim.get("source_ids", []))
            for data_ref in data_refs:
                if isinstance(data_ref, dict):
                    referenced_sources.update(data_ref.get("source_ids", []))
            provenance = slide.get("provenance", {})
            if isinstance(provenance, dict):
                referenced_sources.update(provenance.get("source_ids", []))
            for source_id in sorted(referenced_sources - known_sources):
                issues.append(ValidationIssue("blocker", location, f"{slide_id} references source_id absent from deck.sources: {source_id}"))
    _unique(slide_ids, location, issues)
    return issues


def normalize_legacy_deck(legacy: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Normalize the documented unversioned slide form without dropping source fields."""
    normalized = {key: copy.deepcopy(value) for key, value in legacy.items() if key in {
        "deck_id", "communicated_thesis", "source_pack_refs", "source_decision_status", "governing_question",
        "structure_choice", "why_choice", "audience_objections", "upstream_challenges", "creative_direction", "sources",
    }}
    warnings: list[str] = []
    normalized["schema_version"] = "1.0"
    normalized.setdefault("deck_id", "legacy-deck")
    raw_slides = legacy.get("slides", [])
    normalized_slides = []
    for index, old in enumerate(raw_slides if isinstance(raw_slides, list) else []):
        if not isinstance(old, dict):
            warnings.append(f"slides[{index}] is not an object; preserved in legacy_source only")
            continue
        raw_layout = old.get("layout")
        if isinstance(raw_layout, dict) and isinstance(raw_layout.get("layout_id"), str) and isinstance(raw_layout.get("tokens", {}), dict):
            layout = copy.deepcopy(raw_layout)
        else:
            layout = {"layout_id": old.get("layout_id", raw_layout if isinstance(raw_layout, str) else "legacy-unspecified"), "tokens": {}}
            if raw_layout is not None and not isinstance(raw_layout, str):
                warnings.append(f"{old.get('id', index)}: legacy layout preserved only in legacy_source")
        raw_exhibits = old.get("exhibits", old.get("exhibit_specs", []))
        exhibits = []
        for exhibit_index, raw_exhibit in enumerate(raw_exhibits if isinstance(raw_exhibits, list) else []):
            if not isinstance(raw_exhibit, dict):
                warnings.append(f"{old.get('id', index)} exhibit[{exhibit_index}] preserved only in legacy_source")
                continue
            supported_data = raw_exhibit.get("supported_data", [])
            if not isinstance(supported_data, list) or any(not isinstance(ref, str) for ref in supported_data):
                supported_data = []
                warnings.append(f"{old.get('id', index)} exhibit[{exhibit_index}] supported_data could not be normalized; original preserved")
            known_exhibit = {
                "exhibit_id": raw_exhibit.get("exhibit_id", raw_exhibit.get("id", f"legacy-exhibit-{index + 1}-{exhibit_index + 1}")),
                "slide_id": old.get("slide_id", old.get("id", f"legacy-slide-{index + 1}")),
                "visual_type": raw_exhibit.get("visual_type", raw_exhibit.get("type", "unspecified")),
                "supported_data": copy.deepcopy(supported_data),
            }
            for field in ("visual_job", "units", "as_of", "uncertainty", "annotations", "deterministic_renderer", "asset_id", "alternative_text", "editability", "capability_status", "execution_status"):
                if field in raw_exhibit:
                    known_exhibit[field] = copy.deepcopy(raw_exhibit[field])
            if isinstance(raw_exhibit.get("provenance"), dict):
                known_exhibit["provenance"] = copy.deepcopy(raw_exhibit["provenance"])
            known_fields = {"exhibit_id", "id", "slide_id", "visual_type", "type", "supported_data", "visual_job", "units", "as_of", "uncertainty", "annotations", "deterministic_renderer", "asset_id", "alternative_text", "editability", "capability_status", "execution_status", "provenance"}
            extra = {key: copy.deepcopy(value) for key, value in raw_exhibit.items() if key not in known_fields}
            if extra:
                known_exhibit["extensions"] = {"legacy_fields": extra}
                warnings.append(f"{old.get('id', index)} exhibit[{exhibit_index}] has unsupported fields preserved in extensions")
            exhibits.append(known_exhibit)
        slide = {
            "slide_id": old.get("slide_id", old.get("id", f"legacy-slide-{index + 1}")),
            "role": old.get("role", "unknown"),
            "action_title": old.get("action_title", old.get("headline", "Untitled legacy slide")),
            "claims": copy.deepcopy(old.get("claims", [])),
            "data_refs": copy.deepcopy(old.get("data_refs", [])),
            "exhibits": exhibits,
            "layout": layout,
            "notes": old.get("notes", old.get("speaker_notes", "")),
            "provenance": copy.deepcopy(old.get("provenance", {})),
            "desired_editability": old.get("desired_editability", "UNKNOWN"),
            "extensions": {"legacy_source": copy.deepcopy(old)},
        }
        legacy_sources = old.get("source_ids", [])
        if not isinstance(slide["provenance"], dict):
            slide["extensions"]["legacy_provenance"] = copy.deepcopy(slide["provenance"])
            slide["provenance"] = {}
            warnings.append(f"{slide['slide_id']}: non-object legacy provenance preserved in extensions")
        if legacy_sources and not slide["provenance"].get("source_ids"):
            slide["provenance"]["source_ids"] = copy.deepcopy(legacy_sources)
        for old_key, new_key in (("section", "section"), ("reader_question", "reader_question"),
                                 ("transition", "transition"), ("visual_role", "visual_role"),
                                 ("proof_required", "proof_required"), ("source_line", "source_line"),
                                 ("alternative_text", "alternative_text"), ("output_state", "output_state")):
            if old_key in old:
                slide[new_key] = copy.deepcopy(old[old_key])
        if "claim_ids" in old or "source_finding_ids" in old or "source_option_ids" in old:
            slide["extensions"]["legacy_reference_ids"] = {key: copy.deepcopy(old[key]) for key in ("claim_ids", "source_finding_ids", "source_option_ids") if key in old}
            warnings.append(f"{slide['slide_id']}: legacy reference IDs preserved; claim objects/data references were not inferred")
        if "editability" in old or "editability_expected" in old:
            warnings.append(f"{slide['slide_id']}: legacy editability preserved only in legacy_source; desired_editability left UNKNOWN")
        normalized_slides.append(slide)
    normalized["slides"] = normalized_slides
    root_extensions = copy.deepcopy(legacy.get("extensions", {})) if isinstance(legacy.get("extensions", {}), dict) else {}
    root_extensions["legacy_source"] = copy.deepcopy(legacy)
    normalized["extensions"] = root_extensions
    warnings.append("Complete unversioned source archived at extensions.legacy_source")
    return normalized, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical Presentation DeckSpec v1")
    parser.add_argument("paths", nargs="*", help="JSON deck files; defaults to the canonical synthetic example")
    args = parser.parse_args()
    root = repo_root_from(__file__)
    schema = load_json(root / SCHEMA_RELATIVE)
    paths = [Path(path).resolve() for path in args.paths] if args.paths else [root / EXAMPLE_RELATIVE]
    issues: list[ValidationIssue] = []
    for path in paths:
        try:
            deck = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(ValidationIssue("blocker", str(path), f"Invalid JSON: {exc}"))
            continue
        issues.extend(validate_deck(deck, schema, str(path)))
    for issue in issues:
        print(issue)
    if not issues:
        print(f"Canonical Presentation DeckSpec v1 valid ({len(paths)} file(s)).")
    return 1 if any(issue.severity in {"blocker", "high"} for issue in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
