from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "iteration02_route_evidence.py"
spec = importlib.util.spec_from_file_location("iteration02_route_evidence", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

SOURCE = "a" * 40
PAYLOAD = "b" * 64


class RouteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lock = {
            "source_revision": SOURCE, "release_id": "fixture-release",
            "payload_content_sha256": PAYLOAD, "runtime_evidence": "NOT_RUN",
            "release_approved": False, "cases": [{
                "case_id": "I02-251-browser-mcp", "channel": "browser",
                "input_sha256": PAYLOAD, "repetitions": 1,
            }],
        }
        self.capture = {
            "case_id": "I02-251-browser-mcp", "source_revision": SOURCE,
            "release_id": "fixture-release", "payload_content_sha256": PAYLOAD,
            "input_sha256": PAYLOAD,
            "chat_reference": "fixture://not-a-live-chat",
            "installed_identity_reference": "fixture://not-a-live-identity",
            "correlation_id": "route-call-01",
            "router_correlation_id": "route-call-01",
            "child_correlation_id": "route-call-01",
            "child_execution_claim": "not_verified",
        }
        self.router = {
            "is_investment_request": True,
            "must_invoke_child_workflow": True,
            "child_workflow": "investment-portfolio-review",
            "workflow_execution_state": "not_executed",
            "response_policy": "load_child_workflow_then_follow",
            "outcome": None,
            "tool_receipt": {
                "tool_name": "route_investment_request",
                "status": "SUCCESS", "execution_state": "executed",
                "source_revision": SOURCE,
            },
        }
        self.child = {
            "name": "investment-portfolio-review",
            "instructions": "Synthetic case only",
            "tool_receipt": {
                "tool_name": "load_skill",
                "status": "SUCCESS", "execution_state": "executed",
                "source_revision": SOURCE,
            },
        }
        self.write()

    def write(self):
        for field, data in (("router", self.router), ("child", self.child)):
            path = self.root / (field + ".json")
            path.write_text(json.dumps(data), encoding="utf-8")
            self.capture[f"{field}_raw_path"] = path.name
            self.capture[f"{field}_raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    def assess(self):
        return mod.assess(self.lock, self.capture, self.root)

    def test_synthetic_route_and_child_only_never_certifies_model_behavior(self):
        r = self.assess()
        self.assertEqual("ROUTE_AND_LOAD_STRUCTURALLY_LINKED_REVIEW_REQUIRED", r["status"], r["problems"])
        self.assertEqual("NOT_VERIFIED", r["child_model_execution"])
        self.assertEqual("NOT_EVALUATED", r["final_answer_behavior"])
        self.assertFalse(r["release_approved"])
        self.assertEqual(2, len(r["bound_receipts"]))

    def test_router_only_is_not_child_execution(self):
        (self.root / "child.json").unlink()
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_alternative_child_disagrees_with_router(self):
        self.child["name"] = "investment-opportunity-hunter"
        self.write()
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_route_only_contract_cannot_claim_child_executed(self):
        self.router["workflow_execution_state"] = "executed"
        self.write()
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])
        self.router["workflow_execution_state"] = "not_executed"
        self.capture["child_execution_claim"] = "executed"
        self.write()
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_missing_tool_or_wrong_source_blocks(self):
        self.child["tool_receipt"]["source_revision"] = "c" * 40
        self.write()
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_hash_tampering_blocks(self):
        self.capture["router_raw_sha256"] = "f" * 64
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_wrong_channel_or_release_blocks(self):
        self.lock["cases"][0]["channel"] = "production"
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])
        self.lock["cases"][0]["channel"] = "browser"
        self.capture["source_revision"] = "d" * 40
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])

    def test_traversal_and_nested_case_id_fail_closed(self):
        self.capture["router_raw_path"] = "../private.json"
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])
        self.capture["router_raw_path"] = "router.json"
        self.capture["case_id"] = ["I02-251-browser-mcp"]
        self.assertEqual("BLOCKED_TRACE", self.assess()["status"])


if __name__ == "__main__":
    unittest.main()
