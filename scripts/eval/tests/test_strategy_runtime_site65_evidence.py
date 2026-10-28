from __future__ import annotations
import hashlib, json, zipfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "evals/results/strategy-runtime-site65-2026-10.zip"
EXPECTED_BUNDLE_SHA256 = "84b77f2e2d1dbc4c12938c1b17fd2b3e61284b06dca08e95bdf4c48aef86eb38"
class StrategyRuntimeEvidenceTests(unittest.TestCase):
    def test_bundle_hash_and_all_nested_file_manifests(self):
        self.assertEqual(EXPECTED_BUNDLE_SHA256, hashlib.sha256(BUNDLE.read_bytes()).hexdigest())
        with zipfile.ZipFile(BUNDLE) as archive:
            market=json.loads(archive.read("agent-market-sizing/manifest.json"))
            self.assertEqual(7,len(market["cases"]))
            self.assertEqual("bb49685a42fc944815ff0f36759821e2b5667469d8f13fc67db34ec589ee8696",market["skill"]["content_sha256"])
            for case in market["cases"]:
                receipt=json.loads(archive.read(f"agent-market-sizing/{case['case_id']}/receipt.json"))
                self.assertEqual(case["input_sha256"],receipt["input_sha256"])
                self.assertEqual(case["host_response_sha256"],receipt["host_response_sha256"])
                root=f"agent-market-sizing/{case['case_id']}/"
                self.assertEqual(case["input_sha256"],hashlib.sha256(archive.read(root+"input.prompt.txt")).hexdigest())
                self.assertEqual(case["host_response_sha256"],hashlib.sha256(archive.read(root+"host_response.txt")).hexdigest())
            value=json.loads(archive.read("agent-value-realization/manifest.json"))
            for item in value["files"]:
                self.assertEqual(item["sha256"],hashlib.sha256(archive.read(f"agent-value-realization/{item['path']}")).hexdigest(),item["path"])
            for line in archive.read("agent-strategy-economics/SHA256SUMS.txt").decode().splitlines():
                digest,relative=line.split(None,1)
                self.assertEqual(digest,hashlib.sha256(archive.read("agent-strategy-economics/"+relative.removeprefix("./"))).hexdigest(),relative)
    def test_result_records_match_verified_site_identity_and_counts(self):
        expected={"market-results.json":("market-economics",7),"strategy-economics-results.json":("strategy-economics",7),"value-realization-results.json":("value-realization",6)}
        with zipfile.ZipFile(BUNDLE) as archive:
            for path,(campaign,count) in expected.items():
                result=json.loads(archive.read(path))
                self.assertEqual(campaign,result["campaign"])
                self.assertEqual(65,result["site_version"])
                self.assertEqual("1.38.388",result["lab_version"])
                self.assertEqual("verified",result["runtime_attestation"])
                self.assertEqual("c3f5144399c00af432c578685e5419534649b4d0",result["canonical_source_revision"])
                self.assertEqual(count,len(result["case_verdicts"]))
                self.assertTrue(all(row["verdict"]=="PASS" for row in result["case_verdicts"]))
                self.assertFalse(result["release_approved"])
if __name__=="__main__": unittest.main()
