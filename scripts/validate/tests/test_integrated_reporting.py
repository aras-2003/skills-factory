from __future__ import annotations

from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[3]

TARGET_WORKFLOWS = [
    "investment-opportunity-hunter",
    "investment-security-review",
    "investment-portfolio-review",
    "investment-attention-review",
    "investment-theme-discovery",
    "oaf-health-check",
    "oaf-operating-model-redesign",
    "oaf-governance-redesign",
    "oaf-enterprise-architecture-review",
    "oaf-transformation-design",
    "commerce-opportunity-review",
    "commerce-product-deep-dive",
]


class IntegratedReportingTests(unittest.TestCase):
    def test_target_workflows_use_integrated_report_section(self) -> None:
        for name in TARGET_WORKFLOWS:
            with self.subTest(name=name):
                text = (ROOT / "workflows" / name / "WORKFLOW.md").read_text(encoding="utf-8")
                self.assertIn("## Integrated report presentation", text)
                self.assertIn("report-composer", text)
                self.assertIn("directly in the chat response by default", text)
                self.assertIn("only when the user explicitly requests", text)
                self.assertNotIn("## Visual presentation", text)

    def test_runtime_registry_exposes_composer_before_renderer(self) -> None:
        registry = yaml.safe_load((ROOT / "workflows" / "runtime-registry.yaml").read_text(encoding="utf-8"))
        by_name = {item["name"]: item for item in registry["workflows"]}
        for name in TARGET_WORKFLOWS:
            with self.subTest(name=name):
                optional = [item["name"] for item in by_name[name]["dependencies"]["optional"]]
                self.assertIn("report-composer", optional)
                self.assertIn("visual-output-design", optional)
                self.assertLess(optional.index("report-composer"), optional.index("visual-output-design"))

    def test_composer_and_renderer_contracts_are_separate(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("The report is the product", composer)
        self.assertIn("inline visual", composer.lower())
        self.assertIn("in the chat response by default", composer)
        self.assertIn("Do not create an HTML/PDF/Figma/deck/file unless the user explicitly requests", composer)
        self.assertIn("does not own the structure of a full report", renderer)
        self.assertIn("external-artifact renderer", renderer)

    def test_external_artifact_is_opt_in_not_fallback(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        routing = (ROOT / "skills/meta/visual-output-design/references/tool-routing.md").read_text(encoding="utf-8")
        composition = (ROOT / "skills/meta/report-composer/references/composition-rules.md").read_text(encoding="utf-8")
        self.assertIn("Never generate an external file merely as a fallback", composer)
        self.assertIn("Never create HTML/PDF/Figma/deck/file output merely because", routing)
        self.assertIn("Default delivery is the report itself in the chat response", composition)

    def test_quality_standard_is_intrinsic(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        standard = (ROOT / "skills/meta/report-composer/references/report-quality-standard.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        design = (ROOT / "skills/meta/visual-output-design/references/design-system.md").read_text(encoding="utf-8")
        self.assertIn("report-quality-standard.md", composer)
        self.assertIn("without requiring the user to spell out formatting", composer)
        self.assertIn("Start with an executive summary of 3–5", standard)
        self.assertIn("default to 2–3 detailed candidates", standard)
        self.assertIn("Do not expose raw Mermaid code fences", renderer)
        self.assertIn("Mermaid xychart", design)
        self.assertIn("external market data", standard.lower())

    def test_visual_floor_is_intrinsic(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        standard = (ROOT / "skills/meta/report-composer/references/report-quality-standard.md").read_text(encoding="utf-8")
        profiles = (ROOT / "skills/meta/report-composer/references/report-profiles.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("visual-floor rule", composer)
        self.assertIn("Visual floor:", standard)
        self.assertIn("attempt at least one portfolio-composition/concentration visual", standard)
        self.assertIn("required visual-floor slot", profiles)
        self.assertIn("text-only is not a successful substitute", renderer)

    def test_required_visuals_fail_closed_without_renderer(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        standard = (ROOT / "skills/meta/report-composer/references/report-quality-standard.md").read_text(encoding="utf-8")
        routing = (ROOT / "skills/meta/visual-output-design/references/tool-routing.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        quality_cases = (ROOT / "skills/meta/report-composer/tests/quality-cases.yaml").read_text(encoding="utf-8")

        for text in (composer, standard, routing, renderer, quality_cases):
            self.assertIn("BLOCKED_NO_RENDERER", text)

        self.assertIn("capability_preflight", composer)
        self.assertIn("capability_preflight", renderer)
        self.assertIn("qualifying deterministic data renderer", routing)
        self.assertIn("image generation", routing)
        self.assertIn("diagnostic fallback", standard)
        self.assertIn("claim renderer success for a text-only fallback", quality_cases)

    def test_render_and_client_states_are_separated(self) -> None:
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/meta/report-composer/references/report-state-and-evidence-contract.md").read_text(encoding="utf-8")
        quality_cases = (ROOT / "skills/meta/report-composer/tests/quality-cases.yaml").read_text(encoding="utf-8")

        self.assertIn("PAYLOAD_RENDERED", composer)
        self.assertIn("NOT_OBSERVABLE", composer)
        self.assertIn("analysis_state", composer)
        self.assertIn("Do not emit `report_status: PASS`", composer)
        self.assertIn("PAYLOAD_RENDERED", renderer)
        self.assertIn("NOT_OBSERVABLE", renderer)
        self.assertIn("Do not emit `UI_CONFIRMED`, `UI_RENDER_UNCONFIRMED`", renderer)
        self.assertIn("PENDING_CLIENT_VALIDATION", contract)
        self.assertIn("USER_PROVIDED", contract)
        self.assertIn("causal attribution", contract.lower())
        self.assertIn("zero-row", contract.lower())
        self.assertIn("quality-payload-client-not-observable", quality_cases)
        self.assertIn("quality-user-provided-unreproducible-metric", quality_cases)

    def test_portfolio_attribution_fails_closed_without_causal_evidence(self) -> None:
        workflow = (ROOT / "workflows/investment-portfolio-review/WORKFLOW.md").read_text(encoding="utf-8")
        state = (ROOT / "skills/investing/portfolio-state-review/SKILL.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/portfolio-state-review/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("attribution `UNKNOWN`", workflow)
        self.assertIn("zero-row transaction result is not evidence", workflow.lower())
        self.assertIn('never infer "market-driven"', state)
        self.assertIn("empty or zero-row canonical query result", state.lower())
        self.assertIn("portfolio-attribution-insufficient", cases)
        self.assertIn("portfolio-attribution-empty-transactions", cases)

    def test_investment_front_door_routes_portfolio_to_full_orchestration(self) -> None:
        registry = yaml.safe_load((ROOT / "workflows/runtime-registry.yaml").read_text(encoding="utf-8"))
        by_name = {item["name"]: item for item in registry["workflows"]}
        router = by_name["investment-os-review"]
        portfolio = by_name["investment-portfolio-review"]
        router_workflow = (ROOT / "workflows/investment-os-review/WORKFLOW.md").read_text(encoding="utf-8")
        portfolio_workflow = (ROOT / "workflows/investment-portfolio-review/WORKFLOW.md").read_text(encoding="utf-8")
        routing = (ROOT / "evals/routing/registry.yaml").read_text(encoding="utf-8")
        rubric = (ROOT / "evals/routing/investment-portfolio-natural-en.rubric.yaml").read_text(encoding="utf-8")

        router_description = router["description"].lower()
        self.assertIn("default investment os front door", router_description)
        self.assertIn("review their portfolio", router_description)
        self.assertIn("route first", router_description)
        self.assertIn("generic investment commentary", router_description)

        self.assertIn("investment-portfolio-review", router["dependencies"]["required"])
        self.assertIn("investment-security-review", router["dependencies"]["required"])
        self.assertIn("investment-opportunity-hunter", router["dependencies"]["required"])
        self.assertIn("investment-theme-discovery", router["dependencies"]["required"])
        self.assertIn("investment-attention-review", router["dependencies"]["required"])
        self.assertIn("investment-policy-design", router["dependencies"]["required"])

        self.assertIn("## Routing matrix", router_workflow)
        self.assertIn("MUST take this route", router_workflow)
        self.assertIn("Do not duplicate the child workflow with a generic answer", router_workflow)

        self.assertIn("child workflow for full portfolio review", portfolio["description"].lower())
        self.assertIn("do not use as the default natural investment os entry point", portfolio["description"].lower())
        self.assertIn("Do not skip canonical reads merely because", portfolio_workflow)
        self.assertIn("mandatory for substantial portfolio reviews", portfolio_workflow)

        self.assertIn("investment-portfolio-natural-en", routing)
        self.assertIn("expected_target: investment-os-review", rubric)
        self.assertIn("required_selected_capabilities:", rubric)
        self.assertIn("investment-portfolio-review", rubric)
        self.assertIn("canonical portfolio reads are attempted", rubric)
        self.assertIn("required visual-floor path", rubric)
        self.assertIn("does not stop after a prose-only concentration analysis", rubric)

    def test_investment_record_store_has_single_schema_bootstrap(self) -> None:
        skill = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        governance = (ROOT / "skills/investing/investment-record-store/references/canonical-schema-governance.md").read_text(encoding="utf-8")
        portfolio = (ROOT / "workflows/investment-portfolio-review/WORKFLOW.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/investment-record-store/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("public.system_config", skill)
        self.assertIn("never silently fall back", skill.lower())
        self.assertIn("bootstrap authority", governance.lower())
        self.assertIn("cross_schema_fallback", governance)
        self.assertIn("Never infer cutover from which schema happens to contain rows", governance)
        self.assertIn("schema named in the canonical READ receipt", portfolio)
        self.assertIn("store-canonical-schema-bootstrap", cases)
        self.assertIn("store-canonical-schema-empty-no-fallback", cases)

    def test_investment_exposure_refresh_is_idempotent(self) -> None:
        skill = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/investing/investment-record-store/references/supabase-contract.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/investment-record-store/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("instrument_exposures", skill)
        self.assertIn("idempotent", skill.lower())
        self.assertIn("Canonical identity for refresh/idempotency", contract)
        self.assertIn("store-exposure-idempotency", cases)

    def test_thesis_lifecycle_separates_draft_and_active_state(self) -> None:
        store = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/investing/investment-record-store/references/supabase-contract.md").read_text(encoding="utf-8")
        monitor = (ROOT / "skills/investing/thesis-monitor/SKILL.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/thesis-monitor/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("DRAFT", store)
        self.assertIn("ACTIVE", store)
        self.assertIn("RETIRED", store)
        self.assertIn("draft_theses", contract)
        self.assertIn("only when the latest version state is `ACTIVE`", contract)
        self.assertIn("Do not use `draft_theses` as an active thesis", monitor)
        self.assertIn("monitor-draft-only", cases)
    def test_instrument_identity_rejects_composite_legacy_refs(self) -> None:
        store = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/investing/investment-record-store/references/supabase-contract.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/investment-record-store/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("SMH.L|IUIT.L", store)
        self.assertIn("non-null `isin` is globally unique", contract)
        self.assertIn("composite legacy references", contract.lower())
        self.assertIn("store-composite-instrument-ref", cases)
        self.assertIn("store-isin-identity", cases)
    def test_portfolio_observation_is_distinct_from_full_review(self) -> None:
        registry = yaml.safe_load((ROOT / "workflows/runtime-registry.yaml").read_text(encoding="utf-8"))
        by_name = {item["name"]: item for item in registry["workflows"]}
        router = by_name["investment-os-review"]
        observation = by_name["investment-portfolio-observation"]
        workflow = (ROOT / "workflows/investment-portfolio-observation/WORKFLOW.md").read_text(encoding="utf-8")
        front = (ROOT / "workflows/investment-os-review/WORKFLOW.md").read_text(encoding="utf-8")
        runtime = (ROOT / "runtime/mcp/investment_runtime.py").read_text(encoding="utf-8")
        rubric = (ROOT / "evals/routing/investment-portfolio-observation-natural-pl.rubric.yaml").read_text(encoding="utf-8")

        self.assertIn("investment-portfolio-observation", router["dependencies"]["required"])
        self.assertIn("portfolio-state-review", observation["dependencies"]["required"])
        self.assertIn("portfolio_position_changes", workflow)
        self.assertIn("REQUIRES_ATTENTION", workflow)
        self.assertIn("NO_MATERIAL_CHANGE", workflow)
        self.assertIn("Soft reference", workflow)
        self.assertIn("not policy breaches", workflow)
        self.assertIn("Portfolio observation route", front)
        self.assertIn("investment-portfolio-observation", runtime)
        self.assertIn("required_selected_capabilities:", rubric)
        self.assertIn("investment-portfolio-observation", rubric)

    def test_portfolio_observation_separates_change_from_cause(self) -> None:
        workflow = (ROOT / "workflows/investment-portfolio-observation/WORKFLOW.md").read_text(encoding="utf-8")
        state = (ROOT / "skills/investing/portfolio-state-review/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/investing/investment-record-store/references/supabase-contract.md").read_text(encoding="utf-8")

        self.assertIn("Establish observed change first", workflow)
        self.assertIn("Causal attribution is a separate evidence gate", workflow)
        self.assertIn("Observed change and causal attribution are separate outputs", state)
        self.assertIn("establishes observed change only", contract)
    def test_portfolio_observation_coverage_and_bootstrap_are_truthful(self) -> None:
        workflow = (ROOT / "workflows/investment-portfolio-observation/WORKFLOW.md").read_text(encoding="utf-8")
        state = (ROOT / "skills/investing/portfolio-state-review/SKILL.md").read_text(encoding="utf-8")
        store = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "skills/investing/investment-record-store/references/supabase-contract.md").read_text(encoding="utf-8")
        store_cases = (ROOT / "skills/investing/investment-record-store/tests/cases.yaml").read_text(encoding="utf-8")
        portfolio_cases = (ROOT / "skills/investing/portfolio-state-review/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("portfolio_exposure_source_coverage", workflow)
        self.assertIn("source coverage", workflow.lower())
        self.assertIn("decomposition completeness", workflow.lower())
        self.assertIn("never sum heterogeneous", workflow.lower())
        self.assertIn("portfolio_exposure_source_coverage", state)
        self.assertIn("Source coverage and look-through decomposition completeness", state)
        self.assertIn("do not report the bootstrap table as empty", store)
        self.assertIn("contradictory evidence", store)
        self.assertIn("portfolio_exposure_source_coverage", contract)
        self.assertIn("store-bootstrap-empty-contradiction", store_cases)
        self.assertIn("portfolio-exposure-coverage-semantics", portfolio_cases)

    def test_investment_discovery_requires_why_now_history_and_chart_visuals(self) -> None:
        scan = (ROOT / "skills/investing/market-opportunity-scan/SKILL.md").read_text(encoding="utf-8")
        hunter = (ROOT / "workflows/investment-opportunity-hunter/WORKFLOW.md").read_text(encoding="utf-8")
        underwriting = (ROOT / "skills/investing/security-underwriting/SKILL.md").read_text(encoding="utf-8")
        security = (ROOT / "workflows/investment-security-review/WORKFLOW.md").read_text(encoding="utf-8")
        profiles = (ROOT / "skills/meta/report-composer/references/report-profiles.md").read_text(encoding="utf-8")
        standard = (ROOT / "skills/meta/report-composer/references/report-quality-standard.md").read_text(encoding="utf-8")
        routing = (ROOT / "skills/meta/visual-output-design/references/tool-routing.md").read_text(encoding="utf-8")
        scan_cases = (ROOT / "skills/investing/market-opportunity-scan/tests/cases.yaml").read_text(encoding="utf-8")
        underwriting_cases = (ROOT / "skills/investing/security-underwriting/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("WHY THIS", scan)
        self.assertIn("WHY NOW", scan)
        self.assertIn("Cheap is not a thesis", scan)
        self.assertIn("10-15", hunter)
        self.assertIn("best 2-3", hunter)
        self.assertIn("5Y", hunter)
        self.assertIn("12-20", hunter)
        self.assertIn("OBSERVED", underwriting)
        self.assertIn("VERIFIED EVENT", underwriting)
        self.assertIn("CONFIDENCE", underwriting)
        self.assertIn("required inline 5y price-history visual", security.lower())
        self.assertIn("required historical price visual slot", profiles.lower())
        self.assertIn("A static inline image satisfies a visual slot", standard)
        self.assertIn("do not qualify", routing.lower())
        self.assertIn("scan-cheap-not-enough", scan_cases)
        self.assertIn("underwriting-causal-attribution", underwriting_cases)

    def test_interaction_levels_require_actual_runtime_capability(self) -> None:
        routing = (ROOT / "skills/meta/visual-output-design/references/tool-routing.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")

        for level in ("STATIC", "HOVER", "CONTROLLED", "UNKNOWN"):
            self.assertIn(level, routing)
        self.assertIn("concrete, documented, callable component/API", routing)
        self.assertIn("Do not infer support", routing)
        self.assertIn("do not invent a native `chart` call", renderer)
        self.assertIn("A control-interactive dashboard requires evidence", renderer)
        self.assertIn("interaction_level", composer)
        self.assertIn("CONTROLLED", composer)

    def test_investment_charts_use_best_callable_renderer(self) -> None:
        routing = (ROOT / "skills/meta/visual-output-design/references/tool-routing.md").read_text(encoding="utf-8")
        renderer = (ROOT / "skills/meta/visual-output-design/SKILL.md").read_text(encoding="utf-8")
        composer = (ROOT / "skills/meta/report-composer/SKILL.md").read_text(encoding="utf-8")
        hunter = (ROOT / "workflows/investment-opportunity-hunter/WORKFLOW.md").read_text(encoding="utf-8")
        security = (ROOT / "workflows/investment-security-review/WORKFLOW.md").read_text(encoding="utf-8")

        self.assertNotIn("Attempt-first rule", routing)
        self.assertNotIn("Attempt-first rendering rule", hunter)
        self.assertNotIn("Attempt-first rendering rule", security)
        for workflow in (hunter, security):
            self.assertIn("Renderer and interaction rule", workflow)
            self.assertIn("static chart renderer", workflow)
            self.assertIn("control feature blocked_no_renderer", workflow.lower())
        self.assertIn("concrete, callable renderer", composer)
        self.assertIn("best concrete renderer available", renderer)

    def test_discovery_write_authority_respects_no_save_and_test_boundaries(self) -> None:
        hunter = (ROOT / "workflows/investment-opportunity-hunter/WORKFLOW.md").read_text(encoding="utf-8")
        store = (ROOT / "skills/investing/investment-record-store/SKILL.md").read_text(encoding="utf-8")
        cases = (ROOT / "skills/investing/investment-record-store/tests/cases.yaml").read_text(encoding="utf-8")

        self.assertIn("RESEARCH_CANDIDATE", hunter)
        self.assertIn("is **not by itself** write authorization", hunter)
        self.assertIn("verifiable standing mandate", hunter)
        self.assertIn("Read-only, preview, test, no-save", hunter)
        self.assertNotIn("authorizes these bounded research-state writes by default", hunter)
        self.assertIn("request alone is not write authorization", store.lower())
        self.assertIn("never write to a canonical production backend during evaluation", store.lower())
        self.assertIn("store-research-report-opportunity-write", cases)
        self.assertIn("store-explicit-research-write", cases)

    def test_evidence_contract_requires_reproducibility_and_contradiction_check(self) -> None:
        contract = (ROOT / "skills/meta/report-composer/references/report-state-and-evidence-contract.md").read_text(encoding="utf-8")
        standard = (ROOT / "skills/meta/report-composer/references/report-quality-standard.md").read_text(encoding="utf-8")

        self.assertIn("DERIVED", contract)
        self.assertIn("USER_PROVIDED", contract)
        self.assertIn("reproduce", contract.lower())
        self.assertIn("Contradiction check", contract)
        self.assertIn("cannot be recomputed from visible inputs", standard)


if __name__ == "__main__":
    unittest.main()
