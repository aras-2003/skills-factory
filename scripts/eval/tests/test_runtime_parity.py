from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "runtime_parity.py"
spec = importlib.util.spec_from_file_location("runtime_parity", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

S = "a" * 40
D = "b" * 64
C = "c" * 64
T = "d" * 64
F = "e" * 64


def observation():
    return {
        "attestation_status": "verified",
        "observed_at": "2026-10-13T00:00:00+02:00",
        "observation_source": "synthetic fixture, NOT independent live proof",
        "source_revision": S, "release_id": "lab-123",
        "payload_content_sha256": D, "catalog_digest": C,
        "tool_schema_digest": T, "capabilities": ["runtime_info", "load_skill", "render_bar_chart"],
        "flows": [
            {"flow": f, "execution_state": "executed", "tool_trace_sha256": F,
             "semantic_result_sha256": C,
             "client_display_state": "observed" if f.endswith("chart") else "not_applicable"}
            for f in mod.FLOWS
        ],
    }


class RuntimeParityTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"source_revision": S, "payload_content_sha256": D, "release_id": "lab-123"}

    def test_synthetic_match_is_not_runtime_certification(self):
        report = mod.assess(self.candidate, observation(), observation())
        self.assertEqual("MATCH_PENDING_INDEPENDENT_REVIEW", report["status"])
        self.assertFalse(report["release_approved"])
        self.assertEqual("NOT_RUN_BY_PREFLIGHT", report["runtime_execution"])

    def test_future_dated_observation_is_blocked(self):
        site = observation()
        site["observed_at"] = "2099-12-31T23:59:59+00:00"
        result = mod.assess(self.candidate, observation(), site)
        self.assertEqual("BLOCKED", result["status"])
        self.assertTrue(any("observed_at" in s for s in result["blockers"]))

    def test_stale_site_is_mismatch(self):
        site = observation()
        site["source_revision"] = "1" * 40
        report = mod.assess(self.candidate, observation(), site)
        self.assertEqual("MISMATCH", report["status"])
        self.assertTrue(any("source_revision" in s for s in report["mismatches"]))

    def test_missing_trace_blocks(self):
        site = observation()
        site["flows"][0]["execution_state"] = "awaiting_runner"
        report = mod.assess(self.candidate, observation(), site)
        self.assertEqual("BLOCKED", report["status"])

    def test_unobserved_chart_does_not_pass(self):
        site = observation()
        site["flows"][2]["client_display_state"] = "not_observable"
        self.assertEqual("BLOCKED", mod.assess(self.candidate, observation(), site)["status"])

    def test_site_prefixed_sha256_tool_schema_digest_is_normalized(self):
        site = observation()
        site["tool_schema_digest"] = "sha256:" + T
        report = mod.assess(self.candidate, observation(), site)
        self.assertEqual("MATCH_PENDING_INDEPENDENT_REVIEW", report["status"])
        self.assertFalse(report["release_approved"])

    def test_other_hash_algorithm_is_not_accepted(self):
        site = observation()
        site["tool_schema_digest"] = "md5:" + T
        report = mod.assess(self.candidate, observation(), site)
        self.assertEqual("BLOCKED", report["status"])

    def test_tool_schema_change_is_explicit_mismatch(self):
        site = observation()
        site["tool_schema_digest"] = "f" * 64
        report = mod.assess(self.candidate, observation(), site)
        self.assertEqual("MISMATCH", report["status"])

    def test_bad_manifest_and_unattested_observation_fail_closed(self):
        broken = observation()
        broken["attestation_status"] = "unattested"
        report = mod.assess({}, broken, observation())
        self.assertEqual("BLOCKED", report["status"])

    def test_duplicate_flow_blocks(self):
        site = observation()
        site["flows"].append(site["flows"][0])
        self.assertEqual("BLOCKED", mod.assess(self.candidate, observation(), site)["status"])

    def test_observations_are_not_executed_by_preflight(self):
        self.assertEqual(set(mod.FLOWS), set(x["flow"] for x in observation()["flows"]))
        self.assertEqual("NOT_RUN_BY_PREFLIGHT", mod.assess(self.candidate, observation(), observation())["runtime_execution"])


if __name__ == "__main__":
    unittest.main()
