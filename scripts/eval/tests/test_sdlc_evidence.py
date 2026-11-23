import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import artifact_bundle
import evidence_index
import historical_support
import campaign


class ArtifactTests(unittest.TestCase):
    def bundle(self, root):
        (root / "render.txt").write_text("synthetic")
        data = artifact_bundle.pack(root, "a" * 40, "b" * 64)
        (root / artifact_bundle.MANIFEST).write_text(json.dumps(data))

    def test_matching_artifact_is_usable_but_not_behavioral_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.bundle(root)
            data = artifact_bundle.verify(root, "a" * 40, "b" * 64)
            self.assertFalse(data["runtime_pass_claim"])

    def test_wrong_candidate_fixture_changed_and_added_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self.bundle(root)
            for candidate, fixture in [("c" * 40, "b" * 64), ("a" * 40, "c" * 64)]:
                with self.assertRaises(ValueError):
                    artifact_bundle.verify(root, candidate, fixture)
            (root / "extra.txt").write_text("extra")
            with self.assertRaises(ValueError):
                artifact_bundle.verify(root, "a" * 40, "b" * 64)
            (root / "extra.txt").unlink()
            (root / "render.txt").write_text("tampered")
            with self.assertRaises(ValueError):
                artifact_bundle.verify(root, "a" * 40, "b" * 64)

    def test_symlinks_cannot_escape_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "outside").symlink_to(ROOT / "README.md")
            with self.assertRaises(ValueError):
                artifact_bundle.pack(root, "a" * 40)


class HistoricalSupportTests(unittest.TestCase):
    def test_administrative_reconciliation_is_bound_to_manifest_commit_not_runtime(self):
        manifest = "evals/campaigns/iteration-08-investing-monitoring-2026-11/campaign.yaml"
        cfg = yaml.safe_load((ROOT / manifest).read_text())
        path = "release/production-readiness.yaml"
        expected = cfg["source_sha256"][path]
        self.assertTrue(historical_support.matches_support_pin(
            ROOT, path, expected, cfg["candidate_source_revision"], manifest))
        self.assertFalse(historical_support.matches_support_pin(
            ROOT, path, "0" * 64, cfg["candidate_source_revision"], manifest))
    def test_admin_changes_use_archived_pin_not_current_date(self):
        import subprocess
        path = "release/production-readiness.yaml"
        raw = subprocess.check_output(["git", "show", f"{historical_support.ANCHOR}:{path}"], cwd=ROOT)
        self.assertTrue(historical_support.matches_support_pin(ROOT, path, hashlib.sha256(raw).hexdigest()))
        self.assertFalse(historical_support.matches_support_pin(ROOT, path, "0" * 64))

    def test_support_pin_uses_its_recorded_candidate_not_a_global_anchor(self):
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            path = root / "CATALOG.md"
            path.write_text("archived candidate\\n")
            subprocess.run(["git", "-C", str(root), "add", "CATALOG.md"], check=True)
            subprocess.run([
                "git", "-C", str(root), "-c", "user.name=Test", "-c",
                "user.email=test@example.invalid", "commit", "-m", "archive support file"
            ], check=True, capture_output=True)
            revision = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
            ).strip()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_text("new live candidate\\n")
            self.assertTrue(historical_support.matches_support_pin(root, "CATALOG.md", digest, revision))
            self.assertFalse(historical_support.matches_support_pin(root, "CATALOG.md", "0" * 64, revision))

    def test_runtime_source_cannot_use_historical_support_exemption(self):
        self.assertFalse(historical_support.matches_support_pin(ROOT, "skills/investing/thesis-monitor/SKILL.md", "a" * 64))

    def test_legacy_campaign_still_rejects_changed_runtime(self):
        path = ROOT / "skills/investing/thesis-monitor/SKILL.md"
        original = Path.read_bytes
        def read_bytes(p):
            return original(p) + b"\nchanged runtime" if p == path else original(p)
        with patch.object(Path, "read_bytes", read_bytes):
            self.assertEqual(set(), campaign.separately_validated_iteration08_investing_monitoring_paths(ROOT))


class IndexTests(unittest.TestCase):
    def _receipt_root(self, payload):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        directory = root / "evals/results"
        directory.mkdir(parents=True)
        if payload is not None:
            (directory / "receipt.json").write_text(json.dumps(payload))
        return root

    def _receipt_payload(self, **overrides):
        data = {
            "case": {"id": "synthetic"},
            "component": {"name": "demo", "version": "1", "content_sha256": "same"},
            "evaluation": {"status": "NOT_RUN", "timestamp_utc": "2026-11-20T12:00:00Z"},
            "source_revision": "a" * 40,
            "evidence_scope": "historical",
            "prompt": "PRIVATE_PROMPT_SENTINEL",
            "output": "PRIVATE_OUTPUT_SENTINEL",
            "tool_trace": "PRIVATE_TRACE_SENTINEL",
        }
        data.update(overrides)
        return data

    def test_cov_10_age_anchor_is_exact_candidate_commit_time(self):
        import subprocess
        raw = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", "HEAD"], cwd=ROOT, text=True
        ).strip()
        expected = evidence_index._parse_timestamp(raw)
        self.assertIsNotNone(expected)
        self.assertEqual(
            (evidence_index._utc_text(expected), "git_commit_committer_timestamp"),
            evidence_index._candidate_commit_time(ROOT),
        )

    def test_cov_10_safe_projection_and_candidate_commit_age(self):
        root = self._receipt_root(self._receipt_payload())
        with patch.object(evidence_index, "_candidate_commit_time",
                          return_value=("2026-11-23T12:00:00Z", "git_commit_committer_timestamp")), \
             patch.object(evidence_index, "_candidate_source_revision", return_value="a" * 40), \
             patch.object(evidence_index.receipt, "validate_receipt_data", return_value=[]), \
             patch.object(evidence_index.receipt, "current_component_identity", return_value=("1", "same")):
            report = evidence_index.build_index(root)
        serialized = json.dumps(report)
        for secret in ("PRIVATE_PROMPT_SENTINEL", "PRIVATE_OUTPUT_SENTINEL", "PRIVATE_TRACE_SENTINEL"):
            self.assertNotIn(secret, serialized)
        row = report["receipts"][0]
        self.assertEqual("2026-11-20T12:00:00Z", row["evaluation_timestamp_utc"])
        self.assertEqual("a" * 40, row["source_revision"])
        self.assertEqual("historical", row["evidence_scope"])
        self.assertEqual(3.0, row["age_days"])
        self.assertEqual("KNOWN", row["age_state"])
        self.assertEqual("2026-11-23T12:00:00Z", row["age_as_of_utc"])
        self.assertEqual("git_commit_committer_timestamp", row["age_basis"])
        self.assertEqual("NOT_RUN", row["recorded_status"])
        self.assertFalse(report["runtime_pass_claim"])

    def test_cov_11_unknown_timestamp_and_no_receipt_stay_explicit(self):
        for timestamp, expected_state in ((None, "MISSING_TIMESTAMP"),
                                          ("not-a-time", "MALFORMED_TIMESTAMP"),
                                          ("2026-11-20T12:00:00", "MALFORMED_TIMESTAMP"),
                                          ("2026-11-24T12:00:00Z", "FUTURE_TIMESTAMP")):
            with self.subTest(timestamp=timestamp):
                evaluation = {"status": "NOT_RUN"}
                if timestamp is not None:
                    evaluation["timestamp_utc"] = timestamp
                root = self._receipt_root(self._receipt_payload(evaluation=evaluation))
                with patch.object(evidence_index, "_candidate_commit_time",
                                  return_value=("2026-11-23T12:00:00Z", "git_commit_committer_timestamp")), \
                     patch.object(evidence_index, "_candidate_source_revision", return_value="a" * 40), \
                     patch.object(evidence_index.receipt, "validate_receipt_data", return_value=[]), \
                     patch.object(evidence_index.receipt, "current_component_identity", return_value=("1", "same")):
                    row = evidence_index.build_index(root)["receipts"][0]
                self.assertIsNone(row["age_days"])
                self.assertEqual(expected_state, row["age_state"])

        root = self._receipt_root(self._receipt_payload())
        with patch.object(evidence_index, "_candidate_commit_time",
                          return_value=(None, "CANDIDATE_COMMIT_TIME_UNAVAILABLE")), \
             patch.object(evidence_index, "_candidate_source_revision", return_value=None), \
             patch.object(evidence_index.receipt, "validate_receipt_data", return_value=[]), \
             patch.object(evidence_index.receipt, "current_component_identity", return_value=("1", "same")):
            row = evidence_index.build_index(root)["receipts"][0]
        self.assertIsNone(row["age_days"])
        self.assertEqual("AS_OF_UNAVAILABLE", row["age_state"])

        unreadable_root = self._receipt_root(None)
        (unreadable_root / "evals/results/receipt.json").write_text("not json")
        unreadable = evidence_index.build_index(unreadable_root)["receipts"][0]
        self.assertIsNone(unreadable["age_days"])
        self.assertEqual("RECEIPT_UNREADABLE", unreadable["age_state"])

        empty_root = self._receipt_root(None)
        self.assertEqual([], evidence_index.build_index(empty_root)["receipts"])

    def test_cov_12_source_and_identity_mismatch_remain_visible(self):
        root = self._receipt_root(self._receipt_payload())
        with patch.object(evidence_index, "_candidate_commit_time",
                          return_value=("2026-11-23T12:00:00Z", "git_commit_committer_timestamp")), \
             patch.object(evidence_index, "_candidate_source_revision", return_value="b" * 40), \
             patch.object(evidence_index.receipt, "validate_receipt_data", return_value=["source mismatch"]), \
             patch.object(evidence_index.receipt, "current_component_identity", return_value=("2", "new")):
            row = evidence_index.build_index(root)["receipts"][0]
        self.assertEqual("MISMATCH", row["source_revision_state"])
        self.assertFalse(row["component_identity_matches"])
        self.assertEqual("FAIL", row["receipt_validation"])

    def test_public_projection_never_copies_raw_prompt_or_promotes_old_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); directory = root / "evals/results"; directory.mkdir(parents=True)
            data = {"case": {"id": "synthetic"}, "component": {"name": "demo", "version": "1", "content_sha256": "old"},
                    "evaluation": {"status": "FAIL"}, "source_revision": "a" * 40,
                    "prompt": "PRIVATE_SENTINEL", "notes": "PRIVATE_SENTINEL", "tool_trace": "PRIVATE_SENTINEL"}
            (directory / "receipt.json").write_text(json.dumps(data))
            with patch.object(evidence_index.receipt, "validate_receipt_data", return_value=["invalid"]), \
                 patch.object(evidence_index.receipt, "current_component_identity", return_value=("2", "new")):
                report = evidence_index.build_index(root)
            self.assertNotIn("PRIVATE_SENTINEL", json.dumps(report))
            row = report["receipts"][0]
            self.assertEqual("FAIL", row["recorded_status"])
            self.assertEqual("FAIL", row["receipt_validation"])
            self.assertFalse(row["component_identity_matches"])
            self.assertEqual("NOT_VERIFIED", row["compatibility"])
            self.assertFalse(report["production_approved"])
