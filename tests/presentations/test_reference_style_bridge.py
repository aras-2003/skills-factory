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
    def test_cio_ten_slide_fixture_all_patterns_and_official_lineage(self):
        fixture = json.loads((ROOT / "docs/presentations/examples/cio-reference-golden-v1.json").read_text())
        result = plan(fixture, REGISTRY)
        self.assertEqual(len(result["slides"]), 10)
        self.assertEqual(len(set(x["layout_id"] for x in result["slides"])), 10)
        self.assertEqual({x["status"] for x in result["slides"]}, {"PLANNED_NOT_RENDERED"})
        self.assertTrue(all(x["reference_evidence"] for x in result["slides"]))
        self.assertTrue(all(
            any(e["official"] and e["anchor"] for e in x["reference_evidence"].values())
            for x in result["slides"]
        ))
        self.assertEqual(result["render_status"], "NOT_RUN")
        self.assertEqual(result["editable_export_status"], "NOT_RUN")

    def test_registry_rejects_unknown_source(self):
        edited = dict(REGISTRY)
        edited["patterns"] = [dict(REGISTRY["patterns"][0], source_ids=["MISSING"])]
        with self.assertRaises(ContractError):
            plan({"schema_version":"1.0","slides":[slide("S01","decision")]}, edited)

    def test_registry_rejects_duplicate_ids(self):
        edited = dict(REGISTRY)
        edited["patterns"] = REGISTRY["patterns"] + [REGISTRY["patterns"][0]]
        with self.assertRaises(ContractError):
            plan({"schema_version":"1.0","slides":[slide("S01","decision")]}, edited)

    def test_all_official_sources_have_rights_and_anchor(self):
        official = [s for s in REGISTRY["sources"] if s["id"].startswith("OFF-")]
        self.assertEqual(len(official), 9)
        self.assertEqual({s["publisher"] for s in official}, {"BCG", "McKinsey", "Accenture"})
        self.assertTrue(all(s["source_anchor"] and s["rights"] == "PUBLIC_REVIEW_ONLY"
                            and s["visual_review"] == "NOT_RUN" for s in official))

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
