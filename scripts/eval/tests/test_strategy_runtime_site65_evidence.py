from __future__ import annotations

import hashlib
import json
import zipfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "evals/results/strategy-runtime-site65-2026-10.zip"
EXPECTED_BUNDLE_SHA256 = "3136c6de1c156dde2eb799b114583e80a4372b73741947ba4ab8f966c5dba920"

class StrategyRuntimeEvidenceTests(unittest.TestCase):
    def test_site65_bundle_and_nested_manifests_are_integrity_pinned(self):
        self.assertEqual(EXPECTED_BUNDLE_SHA256, hashlib.sha256(BUNDLE.read_bytes()).hexdigest())
        with zipfile.ZipFile(BUNDLE) as archive:
            for folder in ("agent-market-sizing", "agent-value-realization"):
                manifest = json.loads(archive.read(f"{folder}/manifest.json"))
                for item in manifest["files"]:
                    raw = archive.read(f"{folder}/{item['path']}")
                    self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest(), item["path"])

    def test_runtime_verdicts_match_verified_site_identity(self):
        with zipfile.ZipFile(BUNDLE) as archive:
            expected = {
                "market-results.json": ("market-economics", 7),
                "value-realization-results.json": ("value-realization", 6),
            }
            for path, (campaign, count) in expected.items():
                result = json.loads(archive.read(path))
                self.assertEqual(campaign, result["campaign"])
                self.assertEqual(65, result["site_version"])
                self.assertEqual("1.38.388", result["lab_version"])
                self.assertEqual("verified", result["runtime_attestation"])
                self.assertEqual("c3f5144399c00af432c578685e5419534649b4d0", result["canonical_source_revision"])
                self.assertEqual(count, len(result["case_verdicts"]))
                self.assertTrue(all(row["verdict"] == "PASS" for row in result["case_verdicts"]))
                self.assertFalse(result["release_approved"])

if __name__ == "__main__":
    unittest.main()
