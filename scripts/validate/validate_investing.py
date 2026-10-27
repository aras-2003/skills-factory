from __future__ import annotations

import sys
from pathlib import Path

import yaml


REQUIRED_SKILLS = {
    "decision-journal-update",
    "investment-attention-triage",
    "investment-policy-design",
    "investment-record-store",
    "investor-pattern-research",
    "historical-decision-replay",
    "market-opportunity-scan",
    "portfolio-state-review",
    "position-sizing-review",
    "security-underwriting",
    "thesis-challenge",
    "thesis-monitor",
    "technical-structure",
    "trend-theme-research",
    "valuation-scenario-review",
}

REQUIRED_WORKFLOWS = {
    "investment-os-review",
    "investment-attention-review",
    "investment-opportunity-hunter",
    "investment-security-review",
    "investment-portfolio-observation",
    "investment-portfolio-review",
    "investment-theme-discovery",
}

LEGACY_LOGICAL_AREAS = {
    "Portfolio_Current",
    "Transactions",
    "Portfolio_History",
    "Watchlist",
    "Opportunities",
    "Research_Log",
    "Signals_History",
    "Thesis_Register",
    "Decision_Journal",
    "Investment_Policy",
    "Market_Themes",
    "Sources",
}

REQUIRED_RELATIONAL_ENTITIES = {
    "accounts",
    "instruments",
    "transactions",
    "portfolio_snapshots",
    "position_snapshots",
    "watchlist",
    "opportunities",
    "research_events",
    "signals",
    "theses",
    "thesis_versions",
    "decisions",
    "decision_outcomes",
    "investment_policies",
    "investment_policy_versions",
    "market_themes",
    "market_theme_versions",
    "sources",
    "evidence_links",
    "instrument_exposures",
}

REQUIRED_VIEWS = {
    "current_positions",
    "latest_portfolio_snapshot",
    "latest_valid_snapshot_pair",
    "portfolio_position_changes",
    "portfolio_exposure_source_coverage",
    "current_theses",
    "draft_theses",
    "current_policy",
    "current_watchlist",
    "portfolio_exposures",
    "decision_performance",
}

LEAKAGE_MARKERS = ("expected_routing:", "failure_if:", "should_trigger:", "\nmust:", "\nmust_not:")


def fail(message: str) -> None:
    print(f"BLOCKER investing: {message}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    problems: list[str] = []

    skill_root = root / "skills" / "investing"
    found_skills = {p.parent.name for p in skill_root.rglob("SKILL.md")}
    missing_skills = REQUIRED_SKILLS - found_skills
    extra_skills = found_skills - REQUIRED_SKILLS
    if missing_skills:
        problems.append(f"missing required skills: {sorted(missing_skills)}")
    if extra_skills:
        problems.append(f"unexpected investing skills not covered by architecture test: {sorted(extra_skills)}")

    for name in REQUIRED_SKILLS:
        cases_path = skill_root / name / "tests" / "cases.yaml"
        if not cases_path.exists():
            problems.append(f"{name}: missing tests/cases.yaml")
            continue
        data = yaml.safe_load(cases_path.read_text(encoding="utf-8")) or {}
        cases = data.get("cases") or []
        positives = [c for c in cases if (c.get("expected") or {}).get("should_trigger") is True]
        negatives = [c for c in cases if (c.get("expected") or {}).get("should_trigger") is False]
        if not positives or not negatives:
            problems.append(f"{name}: requires positive and negative routing cases")

    workflow_root = root / "workflows"
    for name in REQUIRED_WORKFLOWS:
        p = workflow_root / name / "WORKFLOW.md"
        if not p.exists():
            problems.append(f"missing workflow: {name}")
            continue
        text = p.read_text(encoding="utf-8")
        if name == "investment-os-review":
            for child in (
                "investment-portfolio-observation",
                "investment-portfolio-review",
                "investment-security-review",
                "investment-opportunity-hunter",
                "investment-theme-discovery",
                "investment-attention-review",
                "investment-policy-design",
            ):
                if child not in text:
                    problems.append(f"{name}: missing child route {child}")
            for required in ("default orchestration front door", "generic investment commentary", "Select the primary route"):
                if required.lower() not in text.lower():
                    problems.append(f"{name}: missing front-door guardrail: {required}")
        else:
            if "investment-record-store" not in text:
                problems.append(f"{name}: durable storage dependency missing")
            if name not in {"investment-theme-discovery", "investment-portfolio-observation"} and "XTB" not in text:
                problems.append(f"{name}: XTB v1 boundary missing")

    governance_path = skill_root / "investment-record-store" / "references" / "canonical-schema-governance.md"
    if not governance_path.exists():
        problems.append("canonical schema governance contract missing")
    else:
        governance = governance_path.read_text(encoding="utf-8")
        for required in ("public.system_config", "cross_schema_fallback", "deprecated/noncanonical", "Never infer cutover from which schema happens to contain rows"):
            if required.lower() not in governance.lower():
                problems.append(f"canonical schema governance missing rule/token: {required}")

    supabase_contract_path = skill_root / "investment-record-store" / "references" / "supabase-contract.md"
    if not supabase_contract_path.exists():
        problems.append("Supabase data contract missing")
    else:
        contract = supabase_contract_path.read_text(encoding="utf-8")
        for entity in REQUIRED_RELATIONAL_ENTITIES:
            if f"### {entity}" not in contract:
                problems.append(f"Supabase contract missing entity: {entity}")
        for view in REQUIRED_VIEWS:
            if f"### {view}" not in contract:
                problems.append(f"Supabase contract missing view: {view}")
        for required in ("append-only", "as_of_date", "source_date", "Google Drive", "explicit cutover", "never allow dual canonical writes", "canonical identity", "idempotent", "DRAFT", "ACTIVE", "RETIRED", "non-null `isin`", "composite legacy references", "source coverage", "decomposition completeness"):
            if required.lower() not in contract.lower():
                problems.append(f"Supabase contract missing integrity rule/token: {required}")

    legacy_contract_path = skill_root / "investment-record-store" / "references" / "google-sheets-contract.md"
    if not legacy_contract_path.exists():
        problems.append("legacy Google Sheets migration contract missing")
    else:
        legacy = legacy_contract_path.read_text(encoding="utf-8")
        for area in LEGACY_LOGICAL_AREAS:
            if area not in legacy:
                problems.append(f"legacy migration contract missing logical area: {area}")
        for required in ("read-only", "migration", "no new canonical writes"):
            if required.lower() not in legacy.lower():
                problems.append(f"legacy migration contract missing rule/token: {required}")

    sizing = (skill_root / "position-sizing-review" / "SKILL.md").read_text(encoding="utf-8")
    for required in ("investment policy", "portfolio state", "Without policy or portfolio state"):
        if required not in sizing:
            problems.append(f"position-sizing-review missing guardrail: {required}")

    attention = (skill_root / "investment-attention-triage" / "SKILL.md").read_text(encoding="utf-8")
    for required in (
        "NOISE",
        "MONITOR",
        "REVIEW",
        "ESCALATE",
        "next research question",
        "provisional decision rule",
        "minimum missing inputs",
        "decision assumption",
    ):
        if required.lower() not in attention.lower():
            problems.append(f"investment-attention-triage missing materiality/escalation guardrail: {required}")

    monitor = (skill_root / "thesis-monitor" / "SKILL.md").read_text(encoding="utf-8")
    for required in ("Append a monitoring record", "never rewrite", "kill criteria"):
        if required.lower() not in monitor.lower():
            problems.append(f"thesis-monitor missing history guardrail: {required}")

    eval_root = root / "evals" / "investing"
    input_files = sorted(eval_root.glob("*.input.md"))
    rubric_files = sorted(eval_root.glob("*.rubric.yaml"))
    if len(input_files) < 6:
        problems.append("expected at least six investing workflow input evals")
    if len(input_files) != len(rubric_files):
        problems.append("every investing input eval must have exactly one rubric")

    for input_path in input_files:
        rubric_path = input_path.with_name(input_path.name.replace(".input.md", ".rubric.yaml"))
        if not rubric_path.exists():
            problems.append(f"missing rubric for {input_path.name}")
        text = input_path.read_text(encoding="utf-8")
        for marker in LEAKAGE_MARKERS:
            if marker in text:
                problems.append(f"{input_path.name}: evaluator leakage marker found: {marker!r}")

    registry = (workflow_root / "runtime-registry.yaml").read_text(encoding="utf-8")
    for name in REQUIRED_WORKFLOWS:
        if f"- name: {name}" not in registry:
            problems.append(f"runtime registry missing candidate workflow: {name}")
    if 'maturity: candidate' not in registry:
        problems.append("candidate maturity not represented in runtime registry")

    if problems:
        for problem in problems:
            fail(problem)
        return 1

    print(
        "Investing architecture validation passed: "
        f"{len(REQUIRED_SKILLS)} skills, {len(REQUIRED_WORKFLOWS)} workflows, "
        f"{len(input_files)} isolated workflow evals, {len(REQUIRED_RELATIONAL_ENTITIES)} relational entities."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
