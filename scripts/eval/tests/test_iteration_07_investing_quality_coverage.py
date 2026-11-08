from __future__ import annotations

from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts" / "eval") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "eval"))

from campaign import separately_validated_iteration07_investing_quality_paths


class Iteration07InvestingQualityCoverageTests(unittest.TestCase):
    def test_candidate_hashes_and_behavior_paths_are_exactly_bound(self):
        expected = {
            "skills/investing/security-underwriting/SKILL.md",
            "skills/investing/security-underwriting/scripts/financial_quality.py",
            "skills/investing/security-underwriting/scripts/value_trap_gate.py",
            "skills/investing/valuation-scenario-review/scripts/peer_comparison.py",
            "skills/investing/valuation-scenario-review/scripts/peer_growth_plot.py",
            "skills/investing/valuation-scenario-review/SKILL.md",
            "skills/investing/valuation-scenario-review/scripts/valuation_scenarios.py",
            "skills/investing/thesis-challenge/SKILL.md",
            "workflows/investment-security-review/WORKFLOW.md",
            "workflows/runtime-registry.yaml",
            "docs/audits/investing-domain-audit-iteration-07-2026-11.md",
            "docs/governance/iterations/iteration-07-investing-quality-2026-11.md",
            "CATALOG.md",
            "docs/catalog.json",
            "scripts/eval/campaign.py",
        }
        self.assertEqual(expected, separately_validated_iteration07_investing_quality_paths(ROOT))

    def test_behavior_suite_binds_partial_runtime_evidence_without_claiming_acceptance(self):
        cfg = yaml.safe_load((ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml").read_text())
        cases = yaml.safe_load((ROOT / cfg["behavior_case_suite"]).read_text())
        self.assertEqual(set(cfg["required_case_ids"]), {item["id"] for item in cases["cases"]})
        self.assertEqual({231, 306, 307, 318}, {item["expected_issue"] for item in cases["cases"]})
        self.assertEqual("PARTIAL_BLOCKED", cfg["runtime_status"])
        self.assertIsNone(cfg["candidate_source_revision"])
        self.assertEqual("pending_local_changes", cfg["candidate_source_revision_status"])
        self.assertEqual("fff6f377c997af2b6ee4987ffb12e4464781cc15", cfg["runtime_canonical_source_revision"])
        self.assertEqual("d1cf3642042a8e4b73dd608dd12368490ea23faf", cfg["runtime_source_revision"])
        self.assertEqual("1.38.469+fff6f377c997", cfg["runtime_release_id"])
        self.assertEqual(122, cfg["runtime_site_version"])
        self.assertTrue((ROOT / cfg["runtime_evidence"]).is_file())
        self.assertEqual(
            {
                "Candidate changes remain local and have no exact-source Cloud Next runtime execution.",
                "Issue #306 is incomplete: the MU 3–5 peer cohort and required broader comparable metric coverage remain unverified.",
            },
            set(cfg["runtime_blockers"]),
        )
        runtime_evidence = (ROOT / cfg["runtime_evidence"]).read_text(encoding="utf-8")
        self.assertIn("Exact Site v121 USER_SUPPLIED_CONTEXT execution", runtime_evidence)
        self.assertIn("NOT_SCORED", runtime_evidence)
        self.assertIn("client_display=NOT_OBSERVABLE", runtime_evidence)
        self.assertIs(cfg["release_approved"], False)
        self.assertIs(cfg["historical_r20_immutable"], True)

    def test_supplemental_routing_regressions_are_registered(self):
        cfg = yaml.safe_load((ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml").read_text())
        registry = yaml.safe_load((ROOT / cfg["supplemental_routing_registry"]).read_text())
        registered = {item["id"] for item in registry["cases"]}
        required = set(cfg["supplemental_routing_case_ids"])
        self.assertTrue(required.issubset(registered))
        self.assertTrue({"investment-top-two-screen-pl", "investment-top-twenty-screen-en",
                         "investment-acronym-vat-pl", "investment-acronym-pit-pl",
                         "investment-acronym-nasa-en"}.issubset(required))
        self.assertIn("investment-security-sizing-natural-pl", required)
        base = yaml.safe_load((ROOT / cfg["routing_registry"]).read_text())
        base_ids = {item["id"] for item in base["cases"]}
        self.assertTrue(set(cfg["routing_case_ids"]).issubset(base_ids))


if __name__ == "__main__":
    unittest.main()
