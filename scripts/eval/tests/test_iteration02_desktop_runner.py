from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import iteration02_desktop_runner as desktop  # noqa: E402

CASE = "I02-240-local-runner"
SOURCE = "a" * 40
PAYLOAD = "b" * 64
SCHEMA = "sha256:" + "d" * 64


class DesktopAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root / "external"
        self.pack.mkdir()
        (self.pack / "desktop").mkdir()
        self.archive = self.root / "evidence"
        self.prompt = b"Evaluate a fictional calendar workflow, no external calls.\n"
        (self.pack / "desktop" / f"{CASE}.input.md").write_bytes(self.prompt)
        self.item = {
            "case_id": CASE, "channel": "desktop", "repetitions": 2,
            "input_path": f"desktop/{CASE}.input.md",
            "input_sha256": hashlib.sha256(self.prompt).hexdigest(),
            "rubric_sha256": "e" * 64,
            "source_revision": SOURCE, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD, "execution_state": "NOT_RUN",
            "provider_dispatch": "BLOCKED_PENDING_APPROVAL_AND_INSTALLED_IDENTITY",
        }
        self.lock = {
            "kind": "external_test_inputs_only",
            "runtime_evidence": "NOT_RUN",
            "provider_calls_executed": False,
            "release_approved": False,
            "source_revision": SOURCE, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD,
            "cases": [self.item],
        }
        self.save_lock()
        self.observed_at = dt.datetime(2026, 10, 13, 12, tzinfo=dt.timezone.utc)
        self.now = self.observed_at + dt.timedelta(minutes=5)
        self.identity = self.root / "desktop-identity.json"
        self.raw_identity = {
            "channel": "desktop", "attestation_status": "verified",
            "source_revision": SOURCE, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD,
            "tool_schema_digest": SCHEMA,
            "observed_at": self.observed_at.isoformat(),
            "observation_source": "synthetic fixture / NOT independently authenticated",
        }
        self.save_identity()
        self.adapter = self.root / "fake_desktop_adapter.py"
        self.make_adapter()

    def save_lock(self):
        (self.pack / "external-lock.json").write_text(
            json.dumps(self.lock), encoding="utf-8"
        )

    def save_identity(self):
        self.identity.write_text(json.dumps(self.raw_identity), encoding="utf-8")

    def make_adapter(self, *, state="executed", steps=True, stale=False):
        revision = "'0' * 40" if stale else "request['source_revision']"
        source = (
            "#!/usr/bin/env python3\n"
            "import json,sys,pathlib\n"
            "request=json.loads(sys.stdin.buffer.read())\n"
            "pathlib.Path('marker').open('a').write('run\\n')\n"
            f"reply={{'case_id':request['case_id'],'attempt':request['attempt'],'source_revision':{revision},"
            f"'execution_state':{state!r},'steps':"
            f"[{{'tool':'synthetic','status':'stub'}}] if {steps!r} else []}}\n"
            "print(json.dumps(reply))\n"
        )
        self.adapter.write_text(source, encoding="utf-8")
        self.adapter.chmod(0o700)
        self.adapter_sha = hashlib.sha256(self.adapter.read_bytes()).hexdigest()

    def execute(self, **extra):
        params = dict(
            approval_reference="fixture-owner-TEMP-001",
            approved=True, now=self.now,
        )
        params.update(extra)
        return desktop.execute_desktop(
            self.pack, self.archive, self.identity, CASE, 1,
            self.adapter, self.adapter_sha, **params
        )

    def test_real_stub_executes_once_with_independent_review_pending(self):
        result = self.execute()
        self.assertEqual("ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED", result["status"])
        observed = self.archive / "desktop" / CASE / "001"
        receipt = json.loads((observed / "record.json").read_text(encoding="utf-8"))
        raw = (observed / "adapter-response.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt["adapter_response_sha256"])
        self.assertEqual("NOT_EVALUATED", receipt["model_behavior_verdict"])
        self.assertFalse(receipt["provider_execution_authenticated"])
        self.assertFalse(receipt["release_approved"])
        self.assertEqual("OPERATOR_ASSERTED_NOT_ENFORCED_BY_SCRIPT", receipt["isolation"])
        self.assertEqual("ALREADY_ARCHIVED_NO_REEXECUTION", self.execute()["status"])
        self.assertEqual(1, (observed / "marker").read_text().count("run"))
        self.assertNotIn("rubric_sha256", raw.decode())

    def test_consent_and_binary_pin_required_before_any_subprocess(self):
        with self.assertRaisesRegex(desktop.RunBlocked, "approval"):
            self.execute(approved=False)
        with self.assertRaisesRegex(desktop.RunBlocked, "approval"):
            self.execute(approval_reference="")
        with self.assertRaisesRegex(desktop.RunBlocked, "digest mismatch"):
            desktop.execute_desktop(
                self.pack, self.archive, self.identity, CASE, 1,
                self.adapter, "f" * 64,
                approval_reference="fixture", approved=True, now=self.now,
            )
        self.assertFalse(self.archive.exists())

    def test_channel_escapes_are_blocked(self):
        for channel in ("lab", "site", "browser", "production"):
            with self.subTest(channel=channel):
                self.item["channel"] = channel
                self.save_lock()
                with self.assertRaisesRegex(desktop.RunBlocked, "only pristine, pinned Desktop"):
                    self.execute()
        self.assertFalse(self.archive.exists())

    def test_previously_executed_external_case_is_not_dispatched(self):
        self.item["execution_state"] = "executed"
        self.save_lock()
        with self.assertRaisesRegex(desktop.RunBlocked, "pristine, pinned"):
            self.execute()
        self.assertFalse(self.archive.exists())

    def test_installed_identity_must_match_and_be_fresh(self):
        self.raw_identity["source_revision"] = "f" * 40
        self.save_identity()
        with self.assertRaisesRegex(desktop.RunBlocked, "identity mismatch"):
            self.execute()
        self.raw_identity["source_revision"] = SOURCE
        self.save_identity()
        with self.assertRaisesRegex(desktop.RunBlocked, "stale"):
            self.execute(now=self.observed_at + dt.timedelta(hours=49))
        with self.assertRaisesRegex(desktop.RunBlocked, "future"):
            self.execute(now=self.observed_at - dt.timedelta(minutes=1))
        self.raw_identity["tool_schema_digest"] = "md5:legacy"
        self.save_identity()
        with self.assertRaisesRegex(desktop.RunBlocked, "schema"):
            self.execute()
        self.assertFalse(self.archive.exists())

    def test_input_tamper_or_symlink_rejected(self):
        prompt = self.pack / "desktop" / f"{CASE}.input.md"
        prompt.write_text("surreptitiously modified")
        with self.assertRaisesRegex(desktop.RunBlocked, "digest/size"):
            self.execute()
        prompt.unlink()
        prompt.symlink_to(self.adapter)
        with self.assertRaisesRegex(desktop.RunBlocked, "untrusted/symlink"):
            self.execute()

    def test_claimed_execution_with_no_steps_blocks(self):
        self.make_adapter(state="executed", steps=False)
        self.assertEqual("BLOCKED_ADAPTER", self.execute()["status"])
        self.assertEqual("PRIOR_BLOCKED_NO_REEXECUTION", self.execute()["status"])

    def test_malformed_adapter_step_receipt_blocks(self):
        self.make_adapter()
        source = self.adapter.read_text(encoding="utf-8")
        source = source.replace("'status':'stub'", "'status':None")
        self.adapter.write_text(source, encoding="utf-8")
        self.adapter_sha = hashlib.sha256(self.adapter.read_bytes()).hexdigest()
        self.assertEqual("BLOCKED_ADAPTER", self.execute()["status"])
        self.assertEqual("PRIOR_BLOCKED_NO_REEXECUTION", self.execute()["status"])

    def test_stale_adapter_output_blocks(self):
        self.make_adapter(stale=True)
        self.assertEqual("BLOCKED_ADAPTER", self.execute()["status"])

    def test_missing_archived_output_blocks_replay(self):
        self.execute()
        output = self.archive / "desktop" / CASE / "001" / "adapter-response.json"
        output.write_text('{"forged":true}', encoding="utf-8")
        with self.assertRaisesRegex(desktop.RunBlocked, "altered"):
            self.execute()

    def test_symlinked_archive_parent_cannot_redirect_evidence(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.archive.mkdir()
        (self.archive / "desktop").symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaisesRegex(desktop.RunBlocked, "must not be symlink"):
            self.execute()
        self.assertFalse(list(elsewhere.iterdir()))

    def test_symlinked_archive_root_rejected_before_resolve(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.archive.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(desktop.RunBlocked, "symlink path component"):
            self.execute()
        self.assertEqual([], list(outside.iterdir()))

    def test_symlinked_input_package_root_rejected_before_resolve(self):
        alias = self.root / "alias"
        alias.symlink_to(self.pack, target_is_directory=True)
        with self.assertRaisesRegex(desktop.RunBlocked, "symlink path component"):
            desktop.execute_desktop(
                alias, self.archive, self.identity, CASE, 1,
                self.adapter, self.adapter_sha,
                approval_reference="fixture", approved=True, now=self.now,
            )
        self.assertFalse(self.archive.exists())

    def test_crashed_reservation_is_not_rerun(self):
        prior = self.archive / "desktop" / CASE / "001"
        prior.mkdir(parents=True)
        with self.assertRaisesRegex(desktop.RunBlocked, "regular file"):
            self.execute()
        self.assertFalse((prior / "marker").exists())

    def test_wrong_attempt_denied(self):
        with self.assertRaisesRegex(desktop.RunBlocked, "invalid attempt"):
            desktop.execute_desktop(
                self.pack, self.archive, self.identity, CASE, 3,
                self.adapter, self.adapter_sha, approval_reference="fixture",
                approved=True, now=self.now,
            )

    def test_nested_archive_or_external_existing_lock_rejected(self):
        with self.assertRaisesRegex(desktop.RunBlocked, "outside input package"):
            desktop.execute_desktop(
                self.pack, self.pack / "evidence", self.identity, CASE, 1,
                self.adapter, self.adapter_sha, approval_reference="fixture",
                approved=True, now=self.now,
            )


if __name__ == "__main__":
    unittest.main()
