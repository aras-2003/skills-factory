from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "iteration02_parity_capture_bridge.py"
spec = importlib.util.spec_from_file_location("iteration02_parity_capture_bridge", MODULE)
bridge = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(bridge)

OLD = "a" * 40
SITE = "b" * 40
PAYLOAD = "c" * 64
ZIP = "d" * 64
CATALOG = "e" * 64
TOOL_SCHEMA = "f" * 64
TRACE = "1" * 64
OUTPUT = "2" * 64


def fixture():
    candidate = {"source_revision": OLD, "release_id": "LabReleasePinned",
                 "payload_content_sha256": PAYLOAD}
    site = {
        "channel": "site", "attestation_status": "verified", "identity_source": "site_environment",
        "source_revision": SITE, "release_id": "SiteWorkerReleaseDifferent",
        "tool_schema_digest": "sha256:" + TOOL_SCHEMA,
        "capabilities": ["runtime_info", "load_skill", "render_bar_chart", "render_line_chart"],
        "tool_receipt": {"tool_name": "runtime_info", "execution_state": "executed",
                         "status": "SUCCESS", "source_revision": SITE},
        "lab_release": {"channel": "lab", "source_revision": OLD,
                        "release_id": "LabReleasePinned",
                        "payload_content_sha256": PAYLOAD,
                        "artifact_sha256": ZIP, "catalog_digest": CATALOG},
    }
    flows = [
        {"flow": name, "execution_state": "executed",
         "tool_trace_sha256": TRACE, "semantic_result_sha256": OUTPUT,
         "observed_lab_source_revision": OLD,
         "observed_site_server_revision": SITE,
         "client_display_state": "observed" if name.endswith("chart") else "not_required"}
        for name in bridge.FLOW_NAMES
    ]
    return candidate, site, flows


class ParityCaptureBridgeTests(unittest.TestCase):
    def call(self, a, b, c):
        return bridge.normalize(a, b, c, label="site",
                                observation_source="TEST fixture, not independent provider receipt",
                                observed_at="2026-10-13T15:00:00+02:00")

    def test_structurally_matching_site_still_not_model_or_provider_pass(self):
        out = self.call(*fixture())
        self.assertEqual("STRUCTURAL_MATCH_PENDING_INDEPENDENT_REVIEW", out["status"], out["errors"])
        self.assertEqual(OLD, out["source_revision"])
        self.assertEqual(SITE, out["site_runtime_source_revision"])
        self.assertNotEqual(out["source_revision"], out["site_runtime_source_revision"])
        self.assertEqual("LabReleasePinned", out["release_id"])
        self.assertEqual("NOT_INDEPENDENTLY_VERIFIED", out["provider_authenticity"])
        self.assertFalse(out["release_approved"])

    def test_site_worker_release_id_cannot_replace_embedded_lab_release_id(self):
        a, b, c = fixture()
        b["lab_release"].pop("release_id")
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])

    def test_existing_site_zip_digest_cannot_substitute_payload_sha(self):
        a, b, c = fixture()
        b["lab_release"].pop("payload_content_sha256")
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])
        b["lab_release"]["payload_content_sha256"] = ZIP
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])

    def test_absent_or_wrong_client_display_and_wrong_server_trace_blocks(self):
        a, b, c = fixture()
        c[2]["client_display_state"] = "not_observable"
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])
        c[2]["client_display_state"] = "observed"
        c[2]["observed_site_server_revision"] = OLD
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])

    def test_missing_trace_duplicate_flow_and_absent_flow_rejected(self):
        a, b, c = fixture()
        c[0]["tool_trace_sha256"] = ""
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])
        c[0]["tool_trace_sha256"] = TRACE
        c[0]["flow"] = "architecture-review"
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])
        c.pop()
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])

    def test_site_and_lab_digests_cannot_be_equated_by_name_only(self):
        a, b, c = fixture()
        b["lab_release"]["source_revision"] = SITE
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])
        b["lab_release"]["source_revision"] = OLD
        b["tool_receipt"]["source_revision"] = OLD
        self.assertEqual("BLOCKED_EVIDENCE", self.call(a, b, c)["status"])

    def test_future_capture_cannot_be_treated_as_observed_evidence(self):
        a, b, c = fixture()
        result = bridge.normalize(
            a, b, c, label="site",
            observation_source="TEST future-dated fixture",
            observed_at="2099-01-01T00:00:00+00:00",
        )
        self.assertEqual("BLOCKED_EVIDENCE", result["status"])
        self.assertIn("observation source and offset-aware time required", result["errors"])

    def test_no_provenance_missing_candidate_or_wrong_channel(self):
        a, b, c = fixture()
        self.assertEqual("BLOCKED_EVIDENCE", bridge.normalize(
            a, b, c, label="site", observation_source="",
            observed_at="2026-10-13T15:00:00")["status"])
        self.assertEqual("BLOCKED_INPUT", bridge.normalize(
            None, b, c, label="site",
            observation_source="test", observed_at="2026-10-13T15:00:00+02:00")["status"])
        self.assertEqual("BLOCKED_EVIDENCE", bridge.normalize(
            a, b, c, label="production",
            observation_source="test", observed_at="2026-10-13T15:00:00+02:00")["status"])


if __name__ == "__main__":
    unittest.main()
