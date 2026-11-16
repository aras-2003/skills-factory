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
    def test_admin_changes_use_archived_pin_not_current_date(self):
        import subprocess
        path = "release/production-readiness.yaml"
        raw = subprocess.check_output(["git", "show", f"{historical_support.ANCHOR}:{path}"], cwd=ROOT)
        self.assertTrue(historical_support.matches_support_pin(ROOT, path, hashlib.sha256(raw).hexdigest()))
        self.assertFalse(historical_support.matches_support_pin(ROOT, path, "0" * 64))

    def test_support_pin_uses_its_recorded_candidate_not_a_global_anchor(self):
        path = "scripts/eval/campaign.py"
        cfg = yaml.safe_load(
            (ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml").read_text()
        )
        revision = cfg["candidate_source_revision"]
        digest = cfg["source_sha256"][path]
        self.assertTrue(historical_support.matches_support_pin(ROOT, path, digest, revision))
        self.assertFalse(historical_support.matches_support_pin(ROOT, path, digest, historical_support.ANCHOR))

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
