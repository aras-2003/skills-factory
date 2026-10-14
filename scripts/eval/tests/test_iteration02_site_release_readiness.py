from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "iteration02_site_release_readiness.py"
spec = importlib.util.spec_from_file_location("iteration02_site_release_readiness", SOURCE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)
OLD = "f" * 40
NEW = "a" * 40
SITE = "b" * 40
ARTIFACT = "c" * 64
OLD_PAYLOAD = "d" * 64
NEW_PAYLOAD = "e" * 64
SCHEMA = "1" * 64
CATALOG = "2" * 64


def fixture():
    candidate = {
        "channel": "lab", "source_revision": NEW,
        "release_id": "lab-candidate-id", "payload_content_sha256": NEW_PAYLOAD,
    }
    site = {
        "channel": "site", "attestation_status": "verified",
        "identity_source": "site_environment",
        "source_revision": SITE, "release_id": "site-release-id",
        "tool_schema_digest": "sha256:" + SCHEMA,
        "deployed_at": "2026-10-13T11:32:41.669Z",
        "tool_receipt": {
            "tool_name": "runtime_info", "status": "SUCCESS",
            "source_revision": SITE, "completed_at": "2026-10-13T11:50:07Z",
        },
        "lab_release": {
            "channel": "lab", "source_revision": OLD,
            "catalog_digest": CATALOG, "artifact_sha256": ARTIFACT,
            "payload_content_sha256": OLD_PAYLOAD,
        },
        "runtime_release": {
            "channel": "lab", "source_revision": OLD,
        },
    }
    rollback = {
        "channel": "lab", "source_revision": OLD,
        "payload_content_sha256": OLD_PAYLOAD,
        "artifact_sha256": ARTIFACT,
        "immutable_artifact_reference": "github://actions/runs/123/artifacts/987?sha256=" + ARTIFACT,
    }
    return candidate, site, rollback


class SiteReleaseReadinessTests(unittest.TestCase):
    def test_consistent_metadata_never_grants_publish(self):
        r = mod.assess(*fixture())
        self.assertEqual("INPUTS_CONSISTENT_APPROVAL_REQUIRED", r["status"], r["blockers"])
        self.assertEqual(OLD, r["current_embedded_lab_source_revision"])
        self.assertEqual(SITE, r["site_runtime_source_revision"])
        self.assertFalse(r["release_approved"])
        self.assertFalse(r["publish_performed"])
        self.assertEqual("NOT_RUN", r["rollback_rehearsal"])

    def test_site_receipt_missing_previous_payload_fails_closed(self):
        a, b, c = fixture()
        b["lab_release"].pop("payload_content_sha256")
        r = mod.assess(a, b, c)
        self.assertEqual("BLOCKED_EVIDENCE", r["status"])
        self.assertTrue(any("ZIP" in msg for msg in r["blockers"]))

    def test_site_source_and_embedded_lab_are_separate(self):
        a, b, c = fixture()
        b["runtime_release"]["source_revision"] = SITE
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])
        b["runtime_release"]["source_revision"] = OLD
        b["tool_receipt"]["source_revision"] = OLD
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])

    def test_target_already_installed_or_mismatched_rollback(self):
        a, b, c = fixture()
        a["source_revision"] = OLD
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])
        a["source_revision"] = NEW
        c["source_revision"] = NEW
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])
        c["source_revision"] = OLD
        c["artifact_sha256"] = NEW_PAYLOAD
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])

    def test_branch_latest_not_immutable_rollback(self):
        for loc in ("main", "https://example.invalid/latest",
                    "git://repo/refs/heads/main", ""):
            with self.subTest(loc=loc):
                a, b, c = fixture()
                c["immutable_artifact_reference"] = loc
                self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])

    def test_missing_independent_site_identity_blocks(self):
        a, b, c = fixture()
        b["attestation_status"] = "unattested"
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])
        b["attestation_status"] = "verified"
        b["tool_schema_digest"] = "not-a-sha"
        self.assertEqual("BLOCKED_EVIDENCE", mod.assess(a, b, c)["status"])

    def test_invalid_or_missing_json_objects_are_safe(self):
        for x in (None, 1, [], "foo"):
            result = mod.assess(x, {}, {})
            self.assertEqual("BLOCKED_EVIDENCE", result["status"])
            self.assertFalse(result["release_approved"])

    def test_real_site_schema_without_payload_does_not_become_ready(self):
        a, b, c = fixture()
        # Current Site MCP exposes a ZIP SHA but not embedded decoded payload.
        b["lab_release"].pop("payload_content_sha256")
        c["payload_content_sha256"] = b["lab_release"]["artifact_sha256"]
        r = mod.assess(a, b, c)
        self.assertEqual("BLOCKED_EVIDENCE", r["status"])
        self.assertFalse(r["release_approved"])


if __name__ == "__main__":
    unittest.main()
