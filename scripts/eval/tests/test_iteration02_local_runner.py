from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "scripts/eval/iteration02_local_runner.py"
spec = importlib.util.spec_from_file_location("iteration02_local_runner", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

SHA = "a" * 40
PAYLOAD = "b" * 64
CASE = "I02-240-local-runner"


class LocalRunnerControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pack = self.root / "pack"
        self.archive = self.root / "archive"
        (self.pack / "executor-inputs").mkdir(parents=True)
        (self.pack / "lab-plugin").mkdir()
        self.prompt = b"Synthetic task without secrets or private data.\n"
        (self.pack / f"executor-inputs/{CASE}.input.md").write_bytes(self.prompt)
        self.lock = {
            "source_revision": SHA, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD, "runtime_execution_state": "NOT_RUN",
            "release_approved": False, "cases": [
                {"id": CASE, "channel": "lab", "dispatch": "LAB_ONLY_PENDING_EXECUTOR",
                 "repetitions": 2,
                 "input_path": f"executor-inputs/{CASE}.input.md",
                 "input_sha256": hashlib.sha256(self.prompt).hexdigest(),
                 "rubric_sha256": "c" * 64},
                {"id": "I02-257-production-fallback", "channel": "production",
                 "dispatch": "BLOCKED_NEEDS_SEPARATE_PROVIDER_AND_APPROVAL",
                 "repetitions": 1, "input_path": None,
                 "input_sha256": "d" * 64, "rubric_sha256": "e" * 64},
            ],
        }
        self.write_lock()
        self.write_release()
        self.adapter = self.root / "stub_adapter.py"
        self.write_adapter()

    def write_lock(self):
        (self.pack / "lock.json").write_text(json.dumps(self.lock), encoding="utf-8")

    def write_release(self):
        (self.pack / "lab-plugin/release-manifest.json").write_text(json.dumps({
            "source_revision": SHA, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD, "channel": "lab",
        }), encoding="utf-8")

    def write_adapter(self, *, state="executed", steps=True, stale=False):
        revision_expr = "'0' * 40" if stale else "data['source_revision']"
        code = (
            "#!/usr/bin/env python3\n"
            "import json,sys,pathlib\n"
            "data=json.loads(sys.stdin.buffer.read())\n"
            "pathlib.Path('called.marker').open('a').write('call\\n')\n"
            f"state={state!r}\n"
            f"steps={{'step':'synthetic_adapter_only'}} if {steps!r} else None\n"
            "out={'case_id':data['case_id'],'attempt':data['attempt'],"
            f"'source_revision':{revision_expr},"
            "'execution_state':state,'steps':[steps] if steps else []}\n"
            "print(json.dumps(out))\n"
        )
        self.adapter.write_text(code, encoding="utf-8")
        self.adapter.chmod(0o700)
        self.pin = hashlib.sha256(self.adapter.read_bytes()).hexdigest()

    def call(self, **kwargs):
        return mod.run_one(self.pack, self.archive, CASE, 1, self.adapter, self.pin,
                           authorized=True, **kwargs)

    def test_one_command_pack_preparation_plus_exec_controller_flow(self):
        lab = self.root / "lab-candidate"
        lab.mkdir()
        (lab / "release-manifest.json").write_text(json.dumps({
            "source_revision": SHA, "release_id": "lab-fixture",
            "payload_content_sha256": PAYLOAD, "channel": "lab",
        }), encoding="utf-8")
        (lab / "plugin.json").write_text('{"test":true}', encoding="utf-8")
        generated = self.root / "newpack"
        with patch.dict(os.environ, {"SOURCE_REVISION": SHA}):
            prepared = mod.ensure_locked_pack(lab, generated, source_root=ROOT)
        self.assertTrue(prepared["prepared"])
        self.assertTrue((generated / "lock.json").is_file())
        self.assertEqual("NOT_RUN", json.loads((generated / "lock.json").read_text())["runtime_execution_state"])
        # The real iteration manifest correctly routes ENG-08 #240 to Desktop.
        # This Lab-only controller must NOT silently convert it into a Lab case.
        with self.assertRaisesRegex(mod.RunBlocked, "external/unauthorized"):
            mod.run_one(generated, self.archive, CASE, 1,
                        self.adapter, self.pin, authorized=True)
        lab_case = "I02-242-catalog-flow"
        result = mod.run_one(generated, self.archive, lab_case, 1,
                             self.adapter, self.pin, authorized=True)
        self.assertEqual("ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED", result["status"])
        with patch.dict(os.environ, {"SOURCE_REVISION": SHA}):
            resumed = mod.ensure_locked_pack(lab, generated, source_root=ROOT)
        self.assertFalse(resumed["prepared"])
        self.assertEqual("ALREADY_ARCHIVED_NO_REEXECUTION",
                         mod.run_one(generated, self.archive, lab_case, 1,
                                     self.adapter, self.pin, authorized=True)["status"])
        release_file = lab / "release-manifest.json"
        altered = json.loads(release_file.read_text(encoding="utf-8"))
        altered["source_revision"] = "f" * 40
        release_file.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaisesRegex(mod.RunBlocked, "different Lab release"):
            mod.ensure_locked_pack(lab, generated, source_root=ROOT)

    def test_adapter_execution_archives_once_no_behavioral_pass(self):
        first = self.call()
        self.assertEqual("ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED", first["status"])
        run = self.archive / "runs" / CASE / "001"
        report = json.loads((run / "record.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_EVALUATED", report["model_behavior_verdict"])
        self.assertFalse(report["provider_execution_attested"])
        self.assertFalse(report["release_approved"])
        self.assertEqual(1, report["reported"]["steps_reported"])
        raw_response = (run / "adapter-response.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw_response).hexdigest(),
                         report["reported"]["response_sha256"])
        self.assertEqual(1, (run / "called.marker").read_text().count("call"))
        second = self.call()
        self.assertEqual("ALREADY_ARCHIVED_NO_REEXECUTION", second["status"])
        self.assertEqual(1, (run / "called.marker").read_text().count("call"))

    def test_requires_explicit_approval_and_adapter_sha(self):
        with self.assertRaisesRegex(mod.RunBlocked, "approve-isolated"):
            mod.run_one(self.pack, self.archive, CASE, 1, self.adapter, self.pin)
        self.assertFalse(self.archive.exists())
        with self.assertRaisesRegex(mod.RunBlocked, "digest mismatch"):
            mod.run_one(self.pack, self.archive, CASE, 1, self.adapter, "f" * 64,
                        authorized=True)
        self.assertFalse(self.archive.exists())

    def test_site_browser_production_cannot_be_executed(self):
        with self.assertRaisesRegex(mod.RunBlocked, "external/unauthorized"):
            mod.run_one(self.pack, self.archive, "I02-257-production-fallback", 1,
                        self.adapter, self.pin, authorized=True)
        self.assertFalse(self.archive.exists())

    def test_tampered_input_blocks_before_execution(self):
        (self.pack / f"executor-inputs/{CASE}.input.md").write_text("changed\n")
        with self.assertRaisesRegex(mod.RunBlocked, "digest/size mismatch"):
            self.call()
        self.assertFalse(self.archive.exists())

    def test_stale_lab_identity_blocks(self):
        self.lock["source_revision"] = "d" * 40
        self.write_lock()
        with self.assertRaisesRegex(mod.RunBlocked, "release mismatch"):
            self.call()
        self.assertFalse(self.archive.exists())

    def test_adapter_claim_executed_without_steps_is_rejected(self):
        self.write_adapter(steps=False)
        result = self.call()
        self.assertEqual("BLOCKED_ADAPTER", result["status"])
        self.assertEqual("NOT_EVALUATED", result["model_behavior_verdict"])
        self.assertEqual("PRIOR_BLOCKED_NO_REEXECUTION", self.call()["status"])

    def test_adapter_claim_with_wrong_source_blocks(self):
        self.write_adapter(stale=True)
        self.assertEqual("BLOCKED_ADAPTER", self.call()["status"])

    def test_crashed_run_is_not_rerun_or_overwritten(self):
        path = self.archive / "runs" / CASE / "001"
        path.mkdir(parents=True)
        with self.assertRaisesRegex(mod.RunBlocked, "incomplete prior run"):
            self.call()
        self.assertFalse((path / "called.marker").exists())

    def test_tampered_completed_adapter_response_is_not_reused(self):
        self.call()
        output = self.archive / "runs" / CASE / "001" / "adapter-response.json"
        output.write_text('{"forged": true}', encoding="utf-8")
        with self.assertRaisesRegex(mod.RunBlocked, "evidence was modified"):
            self.call()

    def test_incomplete_or_corrupted_prior_record_cannot_resume(self):
        self.call()
        record = self.archive / "runs" / CASE / "001" / "record.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        data["release_id"] = "other-release"
        record.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(mod.RunBlocked, "identity mismatch"):
            self.call()

    def test_executor_does_not_receive_evaluator_rubric(self):
        self.call()
        raw = (self.archive / "runs" / CASE / "001" / "adapter-response.json").read_text(encoding="utf-8")
        self.assertNotIn("rubric_sha256", raw)
        self.assertNotIn("evaluation", raw)

    def test_attempts_strict_and_archive_cannot_modify_pack(self):
        with self.assertRaisesRegex(mod.RunBlocked, "attempt exceeds"):
            mod.run_one(self.pack, self.archive, CASE, 3, self.adapter, self.pin,
                        authorized=True)
        with self.assertRaisesRegex(mod.RunBlocked, "archives must be separate"):
            mod.run_one(self.pack, self.pack / "runs", CASE, 1, self.adapter,
                        self.pin, authorized=True)

    def test_symlink_adapter_and_input_are_rejected(self):
        link = self.root / "linked-adapter"
        link.symlink_to(self.adapter)
        with self.assertRaisesRegex(mod.RunBlocked, "no symlinks"):
            mod.run_one(self.pack, self.archive, CASE, 1, link, self.pin,
                        authorized=True)
        prompt_file = self.pack / f"executor-inputs/{CASE}.input.md"
        prompt_file.unlink()
        prompt_file.symlink_to(self.adapter)
        with self.assertRaisesRegex(mod.RunBlocked, "symlink case input"):
            self.call()


if __name__ == "__main__":
    unittest.main()
