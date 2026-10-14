from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "scripts/eval/r17_disposition.py"
spec = importlib.util.spec_from_file_location("r17_disposition", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class HistoricalR17Tests(unittest.TestCase):
    def test_real_history_is_immutable_and_no_current_pass(self):
        report = mod.audit(ROOT)
        self.assertEqual("HISTORICAL_RECEIPTS_RECONCILED_NOT_CURRENT", report["status"], report["errors"])
        self.assertEqual(45, report["historical_case_count"])
        self.assertEqual(36, report["historical_counts"]["PASS"])
        self.assertEqual(9, report["historical_counts"]["FAIL"])
        self.assertEqual(9, len(report["retest_failures"]))
        self.assertEqual(2, len(report["production_only_exclusions"]))
        self.assertEqual("NOT_RUN", report["current_candidate_runtime"])
        self.assertFalse(report["release_approved"])
        self.assertTrue(all(r["current_candidate_outcome"] == "NOT_RUN" for r in report["case_records"]))
        self.assertTrue(all(len(r["receipt_sha256"]) == 64 for r in report["case_records"]))

    def fixture(self, *, status="FAIL"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        rel = "evals/results/runtime-campaign-r17/demo/2026-10-09-chat-plus/transcript-receipt.json"
        file = root / rel
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps({
            "case_id": "demo", "status": status,
            "execution": {"behavior_source_revision": "a" * 40},
            "independent_evaluation": {"status": status},
        }), encoding="utf-8")
        manifest = file.parents[2] / "manifest.json"
        manifest.write_text(json.dumps({
            "valid_receipts": [rel],
            "counts": {"PASS": 0, "FAIL": 1, "REVIEW_REQUIRED": 0, "valid_receipt_count": 1},
            "case_count": 1, "machine_validated_runtime_receipt_count": 0,
            "excluded_production_only_case_ids": ["production-only"],
        }), encoding="utf-8")
        return root, manifest, file

    def test_source_receipt_mismatch_blocks(self):
        root, manifest, file = self.fixture()
        row = json.loads(file.read_text(encoding="utf-8"))
        row["independent_evaluation"]["status"] = "PASS"
        file.write_text(json.dumps(row), encoding="utf-8")
        report = mod.audit(root)
        self.assertEqual("BLOCKED_SOURCE", report["status"])

    def test_path_traversal_is_refused(self):
        root, manifest, file = self.fixture()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["valid_receipts"] = ["../../private/transcript-receipt.json"]
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("BLOCKED_SOURCE", mod.audit(root)["status"])

    def test_wrong_manifest_status_count_is_blocked(self):
        root, manifest, file = self.fixture()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["counts"]["FAIL"] = 0
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("BLOCKED_SOURCE", mod.audit(root)["status"])

    def test_valid_historical_fail_stays_fail_not_current_pass(self):
        root, manifest, file = self.fixture()
        report = mod.audit(root)
        self.assertEqual("HISTORICAL_RECEIPTS_RECONCILED_NOT_CURRENT", report["status"], report["errors"])
        self.assertEqual(["demo"], report["retest_failures"])
        self.assertEqual("NOT_RUN", report["case_records"][0]["current_candidate_outcome"])


if __name__ == "__main__":
    unittest.main()
