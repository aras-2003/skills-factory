import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iteration02_site_native_receipt import canonical_sha, verify_identity, verify_call, unwrap


class NativeReceiptTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"source_revision": "a"*40, "release_id": "lab-fixture", "payload_content_sha256": "b"*64}
        self.identity = {"channel": "site", "source_revision": "c"*40, "release_id": "site-fixture", "attestation_status": "verified", "identity_source": "site_environment", "lab_release": self.candidate.copy()}
        self.identity["tool_receipt"] = self.receipt("runtime_info", self.identity)

    def receipt(self, tool, body):
        return {"kind": "unsigned_mcp_tool_call_receipt", "tool_name": tool, "status": "SUCCESS", "execution_state": "executed", "source_revision": "c"*40, "output_sha256": canonical_sha(body)}

    def test_native_wrappers_and_distinct_sources(self):
        for raw in (self.identity, {"structuredContent": self.identity}, {"content": [{"type": "text", "text": json.dumps(self.identity)}]}):
            self.assertEqual("c"*40, verify_identity(raw, self.candidate)["source_revision"])
        self.assertNotEqual(self.identity["source_revision"], self.candidate["source_revision"])

    def test_zip_hash_is_not_decoded_payload(self):
        d = copy.deepcopy(self.identity)
        d["lab_release"].pop("payload_content_sha256")
        d["lab_release"]["artifact_sha256"] = "b"*64
        with self.assertRaises(ValueError): verify_identity(d, self.candidate)

    def test_tampered_body_and_wrong_worker_block(self):
        d = copy.deepcopy(self.identity); d["release_id"] = "other"
        with self.assertRaises(ValueError): verify_identity(d, self.candidate)
        with self.assertRaises(ValueError): verify_call(self.identity, "runtime_info", "a"*40)

    def test_native_svg_full_output_hash_is_not_data_hash(self):
        body = {"kind": "bar", "svg": '<svg xmlns="http://www.w3.org/2000/svg"/>', "data": {"values": [-5,0,3]}}
        d = {**body, "tool_receipt": self.receipt("render_bar_chart", body)}
        self.assertEqual(body["svg"], verify_call(d,"render_bar_chart","c"*40)["svg"])
        d["tool_receipt"]["output_sha256"] = canonical_sha(body["data"])
        with self.assertRaises(ValueError): verify_call(d,"render_bar_chart","c"*40)

    def test_failed_or_ambiguous_output_blocks(self):
        for raw in ({"isError": True,"structuredContent": self.identity}, {"content": []}, None):
            with self.assertRaises(ValueError): unwrap(raw)

    def test_integral_float_matches_site_integer(self):
        self.assertEqual(canonical_sha({"v":1}),canonical_sha({"v":1.0}))
