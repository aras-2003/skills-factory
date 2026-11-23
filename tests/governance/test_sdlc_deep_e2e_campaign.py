"""The #768 case plan is declarative and must not claim runtime evidence."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "evals/campaigns/sdlc-deep-e2e-2026-11/campaign.yaml"


class SdlcDeepE2ECampaignTests(unittest.TestCase):
    def test_five_scenarios_and_native_gate_states_are_explicit(self):
        data = yaml.safe_load(CAMPAIGN.read_text(encoding="utf-8"))
        self.assertEqual("TEST_DESIGN", data["kind"])
        self.assertEqual("A0", data["architecture_impact"])
        self.assertEqual(["E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05"],
                         [row["id"] for row in data["scenarios"]])
        self.assertEqual({f"G{i}": "NOT_RUN" for i in range(8)} |
                         {f"G{i}": "NOT_RUN" for i in range(8, 11)}, data["gates"])

    def test_required_evidence_and_negative_path_fail_closed(self):
        data = yaml.safe_load(CAMPAIGN.read_text(encoding="utf-8"))
        by_id = {row["id"]: row for row in data["scenarios"]}
        self.assertEqual(["Developer", "Test Executor", "Independent Reviewer"],
                         by_id["E2E-01"]["required_roles"])
        self.assertIn("gpt-6.2-sol", by_id["E2E-03"]["required_model_visibility"])
        self.assertIn("actual_denial_receipts", by_id["E2E-04"]["pass_evidence"])
        self.assertIn("instruction-only", by_id["E2E-04"]["fallback"])
        self.assertFalse(data["evidence_policy"]["green_ci_is_runtime_pass"])
        self.assertFalse(data["evidence_policy"]["production_promotion_authorized"])
        self.assertEqual("existing_issue_and_receipts", data["evidence_policy"]["report_destination"])


if __name__ == "__main__":
    unittest.main()
