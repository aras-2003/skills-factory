from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
SKILL_DIR = ROOT / "skills/seo/seo-research"


class SeoResearchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.contract = (SKILL_DIR / "references/open-seo-mcp-contract.md").read_text(encoding="utf-8")
        cls.cases = yaml.safe_load((SKILL_DIR / "tests/cases.yaml").read_text(encoding="utf-8"))["cases"]

    def test_candidate_metadata_and_upstream_pin_are_explicit(self) -> None:
        frontmatter = self.skill.split("---", 2)[1]
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual("seo-research", metadata["name"])
        self.assertEqual("candidate", metadata["metadata"]["maturity"])
        self.assertEqual("0.1.0", metadata["metadata"]["version"])
        self.assertIn("99d9a49c8cb742d54eddd64d09efbc5302f6db89", self.contract)
        self.assertIn("MIT", self.contract)

    def test_allowlist_excludes_writing_scheduling_and_publishing_tools(self) -> None:
        allowlisted = set(re.findall(r"\| `([a-z][a-z0-9_]*)` \|", self.contract))
        self.assertTrue({"run_site_audit", "research_keywords", "get_ai_visibility_results"}.issubset(allowlisted))
        forbidden = {
            "create_project", "save_keywords", "remove_saved_keywords", "save_report",
            "set_report_sharing", "set_ai_visibility_schedule", "run_ai_visibility_check",
            "submit_indexnow_urls",
        }
        self.assertTrue(allowlisted.isdisjoint(forbidden))
        self.assertIn("Do not call any unlisted tool", self.contract)

    def test_paid_actions_fail_closed_without_bounded_cost_and_current_approval(self) -> None:
        required_controls = (
            "explicit approval for that call",
            "Fail closed if cost is unknown",
            "estimate cannot bound the maximum spend",
            "Do not make a “small test” call",
            "A general request to research, previous approval, or availability of an API key is not spending approval",
        )
        for control in required_controls:
            with self.subTest(control=control):
                self.assertIn(control, self.skill)
        for tool in ("run_site_audit", "research_keywords", "get_keyword_metrics"):
            self.assertIn(f"`{tool}`", self.contract)

    def test_cases_cover_auth_cost_gate_site_scope_injection_and_near_miss(self) -> None:
        cases = {case["id"]: case for case in self.cases}
        self.assertEqual(len(self.cases), len(cases))
        self.assertEqual(
            {
                "missing-connection-blocks",
                "paid-keyword-call-without-approval",
                "bounded-paid-call-needs-current-approval",
                "crawl-target-mismatch-blocks",
                "website-prompt-injection-is-untrusted",
                "saved-visibility-read-only",
                "generic-seo-advice-near-miss",
            },
            set(cases),
        )
        self.assertTrue(any(case["expected"]["should_trigger"] for case in self.cases))
        self.assertTrue(any(not case["expected"]["should_trigger"] for case in self.cases))
        for case in self.cases:
            self.assertTrue(case["expected"].get("must") or case["expected"].get("must_not"), case["id"])

    def test_secret_collection_and_unsupported_execution_claims_are_prohibited(self) -> None:
        self.assertIn("Never ask the user to paste an API key", self.skill)
        self.assertIn("A skill load does not prove that an MCP server is connected", self.skill)
        self.assertIn("EXECUTED`, `BLOCKED`, or `NOT_RUN", self.skill)


if __name__ == "__main__":
    unittest.main()
