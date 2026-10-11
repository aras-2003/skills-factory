#!/usr/bin/env python3
"""Evidence-bound static process audit for every Skills Factory SKILL.md.

Based on packaged Lab skill-specification/authoring/test-design/validation/evaluation
v0.33.7. Heuristics identify *review candidates*, never behavioral PASS.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROUTING_CUES = ("use when", "use for", "use after", "use before", "when ", "before ", "after ")
RUNTIME = "NOT_RUN"


def examine(skill_file: Path, root: Path) -> dict:
    rel = skill_file.relative_to(root).as_posix()
    issues: list[dict] = []

    def flag(code: str, severity: str, reason: str) -> None:
        issues.append({"code": code, "severity": severity, "reason": reason})

    try:
        source = skill_file.read_text(encoding="utf-8")
        if not source.startswith("---\n") or "\n---\n" not in source[4:]:
            raise ValueError("missing frontmatter delimiter")
        head, body = source[4:].split("\n---\n", 1)
        fm = yaml.safe_load(head)
        if not isinstance(fm, dict):
            raise ValueError("frontmatter must be a mapping")
    except (OSError, ValueError, yaml.YAMLError, UnicodeDecodeError) as exc:
        return {
            "name": skill_file.parent.name, "source": rel, "status": "STATIC_BLOCKER",
            "runtime_evidence": RUNTIME, "issues": [
                {"code": "FRONTMATTER_INVALID", "severity": "blocker", "reason": str(exc)}],
        }

    name = fm.get("name")
    description = fm.get("description")
    metadata = fm.get("metadata")
    if not isinstance(name, str) or name != skill_file.parent.name:
        flag("IDENTITY", "blocker", "frontmatter name differs from directory or is absent")
    if not isinstance(description, str) or len(description.strip()) < 40:
        flag("ROUTING_DESCRIPTION", "blocker", "routing description absent or too short")
    elif not any(token in " ".join(description.lower().split()) for token in ROUTING_CUES):
        flag("ROUTING_CONTEXT", "review", "routing trigger not recognizable from description")
    if not isinstance(metadata, dict) or any(not metadata.get(key) for key in
                                             ("owner", "version", "maturity", "risk", "last_reviewed")):
        flag("METADATA", "blocker", "owner/version/maturity/risk/last_reviewed incomplete")

    headings = {m.group(1).strip().lower() for m in re.finditer(r"^## (.+)$", body, re.M)}
    if not any(h.startswith("purpose") for h in headings):
        flag("PURPOSE", "review", "no explicit purpose heading; verify contract is discoverable")
    if not any(h.startswith("procedure") or h.startswith("validation sequence") for h in headings):
        flag("PROCEDURE", "review", "nonstandard procedure layout needs semantic review")
    if not any("output" in h or h == "result" for h in headings):
        flag("OUTPUT", "review", "no explicit output/result heading; verify contract")
    if len(source) > 12000:
        flag("PROGRESSIVE_DISCLOSURE", "review",
             "SKILL.md over 12k characters; assess whether conditional detail belongs in references")

    suite = skill_file.parent / "tests" / "cases.yaml"
    pos = neg = 0
    edge_terms = ("missing", "stale", "ambiguous", "conflict", "failure", "unavailable",
                  "partial", "no evidence", "adversarial", "tool")
    has_edge_signal = False
    if not suite.is_file():
        flag("SUITE_MISSING", "blocker", "test case suite absent")
        cases = []
    else:
        try:
            suite_data = yaml.safe_load(suite.read_text(encoding="utf-8"))
            cases = suite_data.get("cases", []) if isinstance(suite_data, dict) else []
            if not isinstance(cases, list):
                raise ValueError("cases must be a list")
            identifiers = [x.get("id") for x in cases if isinstance(x, dict)]
            if len(identifiers) != len(set(identifiers)) or len(identifiers) != len(cases):
                flag("CASE_IDS", "blocker", "duplicate/missing/nonmapping test cases")
            for case in cases:
                if not isinstance(case, dict):
                    continue
                exp = case.get("expected")
                if not isinstance(exp, dict):
                    continue
                pos += exp.get("should_trigger") is True
                neg += exp.get("should_trigger") is False
                summary = " ".join(str(case.get(k, "")) for k in ("id", "case", "input"))
                if any(word in summary.lower() for word in edge_terms):
                    has_edge_signal = True
        except (OSError, ValueError, yaml.YAMLError, UnicodeDecodeError) as exc:
            cases = []
            flag("SUITE_INVALID", "blocker", str(exc))

    if pos == 0 or neg == 0:
        flag("ROUTING_POLARITY", "high", f"no balanced routing coverage: {pos} positive, {neg} negative")
    if pos < 2:
        flag("POSITIVE_DIVERSITY", "review", f"{pos} positive cases: Lab recommends >=2 realistic variants")
    if neg < 2:
        flag("NEAR_MISS_DIVERSITY", "review", f"{neg} negative cases: Lab recommends >=2 realistic near misses")
    if not has_edge_signal:
        flag("ROBUSTNESS_CASE", "review", "no obvious edge/failure case signal in fixture text; review manually")

    blockers = sum(item["severity"] in {"blocker", "high"} for item in issues)
    return {
        "name": str(name or skill_file.parent.name), "source": rel,
        "maturity": metadata.get("maturity") if isinstance(metadata, dict) else None,
        "test_source": suite.relative_to(root).as_posix(),
        "case_count": len(cases), "positive_cases": pos, "negative_cases": neg,
        "static_robustness_signal": has_edge_signal,
        "status": "STATIC_BLOCKER" if blockers else "REVIEW_REQUIRED" if issues else "STATIC_CHECKS_OK",
        "runtime_evidence": RUNTIME, "semantic_review": "REQUIRED",
        "issues": issues,
    }


def audit(root: Path) -> dict:
    skills = sorted((root / "skills").rglob("SKILL.md"))
    rows = [examine(path, root) for path in skills]
    counts = Counter(row["status"] for row in rows)
    signals = Counter(item["code"] for row in rows for item in row["issues"])
    by_domain = defaultdict(list)
    for row in rows:
        by_domain[Path(row["source"]).parts[1]].append(row["name"])
    return {
        "schema_version": "1.0",
        "basis": "Skills Factory Cloud Next packaged Lab 0.33.7; skill-specification, skill-authoring, skill-test-design, skill-validation, skill-evaluation",
        "source_revision": os.getenv("SOURCE_REVISION", "LOCAL_CHECKOUT_UNATTESTED"),
        "scope": "all_source_skills", "assessment_level": "DETERMINISTIC_STATIC_SCREEN_ONLY",
        "runtime_execution": RUNTIME, "runtime_behavioral_acceptance": "NOT_VERIFIED",
        "semantic_review_required": True,
        "total_skills": len(rows), "result_counts": dict(sorted(counts.items())),
        "finding_counts": dict(sorted(signals.items())),
        "domains": {k: sorted(v) for k, v in sorted(by_domain.items())},
        "skills": rows,
        "limitations": [
            "A visible heading or lexical cue is not proof of behavioral completeness or skill value.",
            "No tool/connector runtime, semantic routing or live evidence is executed by this script.",
            "Do not rewrite tests just to satisfy the case-count heuristic; near misses must be realistic.",
            "Release promotion needs separate evidence tied to exact source/package/channel and authorization.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-structural-blockers", action="store_true")
    args = parser.parse_args()
    report = audit(args.root.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print("Lifecycle audit: %s skills; counts=%s; findings=%s" % (
            report["total_skills"], report["result_counts"], report["finding_counts"]
        ))
        for row in report["skills"]:
            found = ",".join(issue["code"] for issue in row["issues"]) or "none"
            print("SKILL %s: %s; pos=%s, neg=%s; signals=%s; runtime=NOT_RUN" % (
                row["name"], row["status"], row["positive_cases"], row["negative_cases"], found
            ))
    else:
        print(rendered, end="")
    bad = report["result_counts"].get("STATIC_BLOCKER", 0) > 0
    return 1 if args.fail_on_structural_blockers and bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
