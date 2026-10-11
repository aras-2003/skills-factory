from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import yaml

from common import repo_root


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokens(text: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(char for char in folded if not unicodedata.combining(char))
    return {word for word in TOKEN_RE.findall(normalized) if len(word) > 2}


def similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def catalog_surfaces(root: Path) -> dict[str, str]:
    catalog = json.loads((root / "docs/catalog.json").read_text(encoding="utf-8"))
    result = {
        item["name"]: " ".join((item.get("name", ""), item.get("domain", ""), item.get("description", "")))
        for item in catalog.get("skills", [])
    }
    for item in catalog.get("workflows", []):
        result[item["name"]] = " ".join((item.get("name", ""), item.get("description", "")))
    return result


def build_report(root: Path) -> dict:
    surfaces = catalog_surfaces(root)
    registry = yaml.safe_load((root / "evals/routing/registry.yaml").read_text(encoding="utf-8")) or {}
    cases = []
    for entry in registry.get("cases") or []:
        rubric = yaml.safe_load((root / entry["rubric"]).read_text(encoding="utf-8")) or {}
        prompt = (root / entry["input"]).read_text(encoding="utf-8")
        target = str(rubric.get("expected_target") or "")
        ranked = sorted(
            ((name, round(similarity(prompt, surface), 6)) for name, surface in surfaces.items()),
            key=lambda row: (-row[1], row[0]),
        )
        no_skill = target == "no-skill"
        target_score = next((score for name, score in ranked if name == target), 0.0)
        target_rank = next((index + 1 for index, (name, _) in enumerate(ranked) if name == target), None) if target_score > 0 else None
        competitor = next(((name, score) for name, score in ranked if name != target and score > 0), None)
        margin = round(target_score - competitor[1], 6) if competitor and not no_skill else None
        review_signal = (
            "REVIEW" if no_skill and competitor
            else "INSUFFICIENT_LEXICAL_SIGNAL" if target_score == 0
            else "REVIEW" if target_rank != 1 or (margin is not None and margin < 0.03)
            else "NO_STATIC_COLLISION_SIGNAL"
        )
        cases.append({
            "id": entry["id"],
            "language": rubric.get("language"),
            "expected_target": target,
            "route_kind": "no_skill_negative" if no_skill else "skill_positive",
            "lexical_target_rank": target_rank,
            "lexical_margin_to_competitor": margin,
            "target_score": target_score,
            "nearest_competitor": {"name": competitor[0], "score": competitor[1]} if competitor else None,
            "semantic_review_signal": review_signal,
            "runtime_semantic_evidence_required": rubric.get("mode") == "natural-routing",
            "runtime_outcome": None,
        })
    neighbors = []
    names = sorted(surfaces)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            score = similarity(surfaces[left], surfaces[right])
            if score >= 0.2:
                neighbors.append({"left": left, "right": right, "description_overlap": round(score, 6)})
    neighbors.sort(key=lambda item: (-item["description_overlap"], item["left"], item["right"]))
    return {
        "schema_version": "1.0",
        "classification": "STATIC_SIGNAL_ONLY",
        "runtime_evidence": "NOT_PROVIDED",
        "catalog_component_count": len(surfaces),
        "case_count": len(cases),
        "positive_case_count": sum(row["route_kind"] == "skill_positive" for row in cases),
        "no_skill_negative_case_count": sum(row["route_kind"] == "no_skill_negative" for row in cases),
        "languages": sorted({row["language"] for row in cases if row["language"]}),
        "cases": cases,
        "description_neighbors": neighbors[:100],
        "limitations": [
            "Lexical similarity is an early-warning signal, not evidence of natural-language routing correctness.",
            "This report never assigns runtime PASS or FAIL.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate evaluator-side static routing collision signals.")
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.root.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
