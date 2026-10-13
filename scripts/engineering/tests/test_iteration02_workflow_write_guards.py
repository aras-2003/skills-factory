from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
FLOWS = {
    "oaf-strategy-execution-reset",
    "investment-attention-review",
    "investment-security-review",
    "investment-theme-discovery",
}


class Iteration02WorkflowWriteGuards(unittest.TestCase):
    def test_all_four_workflows_have_entry_disclosure_and_stop_boundaries(self):
        for name in FLOWS:
            with self.subTest(workflow=name):
                text = (ROOT / "workflows" / name / "WORKFLOW.md").read_text(encoding="utf-8")
                self.assertIn("## Entry criteria", text)
                self.assertIn("## Stop conditions", text)
                self.assertIn("## Output contract", text)

    def test_security_and_theme_do_not_treat_analysis_as_write_authorization(self):
        for name in ("investment-security-review", "investment-theme-discovery"):
            with self.subTest(workflow=name):
                text = (ROOT / "workflows" / name / "WORKFLOW.md").read_text(encoding="utf-8")
                self.assertIn("NOT_WRITTEN", text)
                self.assertIn("WRITE_FAILED", text)
                self.assertIn("SAVED", text)
                self.assertIn("explicit", text.lower())
                self.assertIn("append", text.lower())
                self.assertIn("canonical WRITE receipt", text)
                self.assertNotIn("12. Persist sources, research events", text)
                self.assertNotIn("9. Persist a new theme version", text)

    def test_security_and_theme_have_real_authorization_near_miss_fixtures(self):
        for name in ("investment-security-review", "investment-theme-discovery"):
            suite = ROOT / "workflows" / name / "tests/cases.yaml"
            data = yaml.safe_load(suite.read_text(encoding="utf-8"))
            cases = data["cases"]
            self.assertGreaterEqual(len(cases), 4)
            self.assertEqual(len({x["id"] for x in cases}), len(cases))
            self.assertTrue(any(c["expected"].get("should_trigger") is False for c in cases))
            self.assertTrue(any(c["expected"].get("should_trigger") is True for c in cases))
            self.assertTrue(any("NOT_WRITTEN" in str(c["expected"]) for c in cases))
            self.assertTrue(any("WRITE receipt" in str(c["expected"]) for c in cases))
            self.assertTrue(all(c.get("input") and isinstance(c.get("expected"), dict) for c in cases))

    def test_noninvestment_reset_workflow_routes_bounded_requests_directly(self):
        source = (ROOT / "workflows/oaf-strategy-execution-reset/WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("route directly to the relevant specialist", source)
        self.assertIn("only when initiative evidence is comparable", source)


if __name__ == "__main__":
    unittest.main()
