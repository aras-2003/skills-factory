from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = ROOT / "evals/campaigns/design-critique-2026-10/campaign.yaml"
REPORT = ROOT / "evals/results/design-critique-2026-10/2026-10-28-site-runtime/run.json"


class DesignCritiqueRuntimeCoverageTests(unittest.TestCase):
    def test_campaign_is_bound_to_the_verified_candidate_and_report(self):
        campaign = CAMPAIGN.read_text()
        self.assertIn("runtime_status: PASS", campaign)
        self.assertIn("release_approved: false", campaign)
        self.assertIn("result_record: evals/results/design-critique-2026-10/2026-10-28-site-runtime/run.json", campaign)
        candidate_sha = re.search(r"^  sha256: ([a-f0-9]{64})$", campaign, re.M)
        self.assertIsNotNone(candidate_sha)
        self.assertEqual(candidate_sha.group(1), hashlib.sha256((ROOT / "skills/web-design/design-critique/SKILL.md").read_bytes()).hexdigest())

    def test_behavior_routing_outputs_and_receipts_are_complete_and_pinned(self):
        report = json.loads(REPORT.read_text())
        self.assertEqual("ad9c7305d22d4ac276bf2762207a79b081888730", report["candidate"]["canonical_source_sha"])
        self.assertEqual("999433e57e9ef98388692f4c16076c187da3fe849f2a144031b338818725db8d", report["candidate"]["content_sha256"])
        required = {
            "design-critique-comparative-fixture", "design-critique-single-screen",
            "design-critique-no-artifact", "design-critique-hidden-behavior",
            "design-critique-implementation-nearmiss", "design-critique-copy-edit-nearmiss",
            "design-critique-single-viewport",
        }
        recorded = {case["case_id"]: case for case in report["cases"]}
        self.assertEqual(required, set(recorded))
        self.assertTrue(all(case["result"] == "PASS" for case in recorded.values()))
        self.assertEqual({"design-critique-natural-en", "design-critique-implementation-nearmiss-en"}, {case["case_id"] for case in report["routing_cases"]})
        self.assertTrue(all(case["result"] == "PASS" for case in report["routing_cases"]))
        for case in [*report["cases"], *report["routing_cases"]]:
            output = REPORT.parent / case["executor_output"]
            self.assertEqual(case["output_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            for artifact in case.get("artifacts", []):
                self.assertEqual(artifact["sha256"], hashlib.sha256((REPORT.parent / artifact["path"]).read_bytes()).hexdigest())
        self.assertTrue(report["receipt_integrity"])
        self.assertTrue(all(item["integrity_verified"] for item in report["receipt_integrity"]))
        self.assertTrue(all(item["status"] == "SUCCESS" for item in report["receipt_integrity"]))


if __name__ == "__main__":
    unittest.main()
