from __future__ import annotations
import hashlib, json, zipfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
BUNDLE = ROOT / "evals/results/strategy-runtime-site65-2026-10.zip"
EXPECTED_BUNDLE_SHA256 = "96468249dbae2d62c0e9422a81764362e8fa9794f652cc5c244f40bc8ca7b2ec"
class StrategyRuntimeEvidenceTests(unittest.TestCase):
    def test_bundle_hash_and_all_nested_file_manifests(self):
        self.assertEqual(EXPECTED_BUNDLE_SHA256, hashlib.sha256(BUNDLE.read_bytes()).hexdigest())
        with zipfile.ZipFile(BUNDLE) as archive:
            market=json.loads(archive.read("agent-market-sizing/manifest.json"))
            corrected=json.loads(archive.read("agent-market-sizing/manifest.integrity-corrected.json"))
            self.assertEqual("988a53b89a5d73aba496bd250b65ad5702c061faa4394e7f72e709431b87998c",hashlib.sha256(archive.read("agent-market-sizing/manifest.integrity-corrected.json")).hexdigest())
            self.assertEqual(7,len(corrected["cases"]))
            self.assertEqual(7,len(market["cases"]))
            self.assertEqual("bb49685a42fc944815ff0f36759821e2b5667469d8f13fc67db34ec589ee8696",market["skill"]["content_sha256"])
            for case in corrected["cases"]:
                root=f"agent-market-sizing/{case['case_id']}/"
                self.assertEqual(case["input_file_sha256"],hashlib.sha256(archive.read(root+case["input_file"])).hexdigest())
                self.assertEqual(case["host_response_sha256"],hashlib.sha256(archive.read(root+case["host_response_file"])).hexdigest())
                receipt=json.loads(archive.read(root+case["corrected_receipt_file"]))
                self.assertEqual(case["input_file_sha256"],receipt["input_sha256"])
                self.assertEqual(case["host_response_sha256"],receipt["host_response_sha256"])
                self.assertEqual(case["corrected_receipt_sha256"],hashlib.sha256(archive.read(root+case["corrected_receipt_file"])).hexdigest())
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
