from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "iteration02_site_promotion_preflight.py"
spec = importlib.util.spec_from_file_location("iteration02_site_promotion_preflight", FILE)
preflight = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(preflight)

A = "a" * 40
B = "b" * 40
C = "c" * 64
D = "d" * 64


def fixture():
    candidate = {"channel": "lab", "source_revision": A,
                 "release_id": "0.36.0+candidate", "payload_content_sha256": C}
    site = {
        "attestation_status": "verified",
        "observed_at": "2026-10-13T12:00:00+02:00",
        "observation_source": "synthetic Fixture, not an authenticated provider receipt",
        "lab_release": {"source_revision": B, "release_id": "0.35.0+previous",
                        "payload_content_sha256": D},
    }
    rollback = {
        "source_revision": B, "release_id": "0.35.0+previous",
        "payload_content_sha256": D, "artifact_sha256": C,
        "immutable_artifact_reference": "fixture-sha256:ccc",
    }
    return candidate, site, rollback


class SitePromotionPreflightTests(unittest.TestCase):
    def test_valid_fixture_cannot_publish_or_attest(self):
        p = preflight.plan(*fixture())
        self.assertEqual("PLAN_ONLY_REVIEW_REQUIRED", p["state"])
        self.assertFalse(p["publish_performed"])
        self.assertFalse(p["rollback_performed"])
        self.assertFalse(p["release_approved"])
        self.assertEqual("NOT_RUN", p["post_publish_attestation"])

    def test_no_exact_site_identity_blocks(self):
        a, b, c = fixture()
        b["attestation_status"] = "unattested"
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])

    def test_missing_previous_payload_blocks_even_if_zip_hash_known(self):
        a, b, c = fixture()
        b["lab_release"].pop("payload_content_sha256")
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])

    def test_rollback_must_match_prior_exact_source_and_payload(self):
        a, b, c = fixture()
        c["source_revision"] = A
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])
        c["source_revision"] = B
        c["payload_content_sha256"] = C
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])

    def test_candidate_already_installed_is_not_new_deployment(self):
        a, b, c = fixture()
        b["lab_release"].update(
            source_revision=A, release_id=a["release_id"],
            payload_content_sha256=C,
        )
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])

    def test_missing_time_observation_or_rollback_locator_blocks(self):
        for key, invalid in (
            ("observed_at", "not-a-time"), ("observed_at", "2026-10-13T12:00:00"),
            ("observation_source", ""),):
            a, b, c = fixture()
            b[key] = invalid
            self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])
        a, b, c = fixture()
        c["immutable_artifact_reference"] = ""
        self.assertEqual("BLOCKED_INPUT", preflight.plan(a, b, c)["state"])

    def test_invalid_types_never_trigger_publish(self):
        for val in ([], None, "string"):
            p = preflight.plan(val, {}, {})
            self.assertEqual("BLOCKED_INPUT", p["state"])
            self.assertFalse(p["publish_performed"])


if __name__ == "__main__":
    unittest.main()
