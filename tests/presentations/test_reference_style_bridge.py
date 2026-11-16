import json
import unittest
from pathlib import Path
from scripts.presentations.reference_style_bridge import ContractError, plan

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "docs/presentations/consulting-reference-patterns-v1.json").read_text())

def slide(sid, role, status="USER_PROVIDED"):
    return {"slide_id": sid, "role": role,
            "claims": [{"claim_id": "C-" + sid, "statement": "Scenario input",
                        "epistemic_status": status}]}

class ReferenceStyleBridgeTests(unittest.TestCase):
    def test_fixture_has_traceable_sources(self):
        result = plan({"schema_version":"1.0","deck_id":"CIO","slides":[
            slide("S01","decision"), slide("S02","architecture"), slide("S03","roadmap")]}, REGISTRY)
        self.assertEqual([x["status"] for x in result["slides"]], ["PLANNED_NOT_RENDERED"]*3)
        self.assertTrue(all(x["reference_revisions"] for x in result["slides"]))
        self.assertEqual(result["render_status"], "NOT_RUN")
    def test_unknown_role_never_claims_quality(self):
        r = plan({"schema_version":"1.0","slides":[slide("S01","decorative")]}, REGISTRY)
        self.assertEqual(r["slides"][0]["status"], "NO_PATTERN")
    def test_missing_evidence_requires_review(self):
        r = plan({"schema_version":"1.0","slides":[
            {"slide_id":"S01","role":"kpi","claims":[]}]}, REGISTRY)
        self.assertEqual(r["slides"][0]["status"], "REVIEW_REQUIRED")
    def test_contradiction_requires_review(self):
        r = plan({"schema_version":"1.0","slides":[slide("S01","options","CONTRADICTED")]}, REGISTRY)
        self.assertEqual(r["slides"][0]["status"], "REVIEW_REQUIRED")
    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(ContractError):
            plan({"schema_version":"1.0","slides":[slide("S01","decision"),slide("S01","kpi")]}, REGISTRY)
    def test_invalid_status_fails_closed(self):
        with self.assertRaises(ContractError):
            plan({"schema_version":"1.0","slides":[slide("S01","decision","FAKE_VERIFIED")]}, REGISTRY)

if __name__ == "__main__":
    unittest.main()
