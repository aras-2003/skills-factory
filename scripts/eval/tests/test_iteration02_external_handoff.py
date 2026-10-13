from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import iteration02_handoff as parent  # noqa: E402

FILE = ROOT / "scripts/eval/iteration02_external_handoff.py"
spec = importlib.util.spec_from_file_location("iteration02_external_handoff", FILE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class ExternalHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.pack = self.folder / "lab"
        self.pack.mkdir()
        cfg, errors = parent.validate(ROOT)
        self.assertFalse(errors, errors)
        self.config = cfg
        self.lock = {
            "source_revision": "a" * 40, "release_id": "fixture-lab",
            "payload_content_sha256": "b" * 64,
            "runtime_execution_state": "NOT_RUN", "release_approved": False,
            "manifest_sha256": parent.digest((ROOT / parent.MANIFEST).read_bytes()),
            "cases": [],
        }
        for case in cfg["cases"]:
            external = case["channel"] != "lab"
            payload = (case["input"] if external else case["input"].strip() + "\n").encode()
            self.lock["cases"].append({
                "id": case["id"], "channel": case["channel"],
                "repetitions": case["repetitions"],
                "input_sha256": hashlib.sha256(payload).hexdigest(),
                "input_path": None if external else "executor-inputs/" + case["id"] + ".input.md",
                "rubric_sha256": parent.digest(parent.canonical(case["assertions"])),
                "dispatch": "BLOCKED_NEEDS_SEPARATE_PROVIDER_AND_APPROVAL" if external else "LAB_ONLY_PENDING_EXECUTOR",
            })
        self.save_lock()

    def save_lock(self):
        (self.pack / "lock.json").write_text(json.dumps(self.lock), encoding="utf-8")

    def test_all_external_cases_are_separate_unexecuted_inputs(self):
        out = self.folder / "external"
        result = mod.prepare(ROOT, self.pack, out)
        self.assertEqual(7, result["external_case_count"])
        self.assertEqual(7, len(result["cases"]))
        self.assertFalse(result["provider_calls_executed"])
        self.assertFalse(result["release_approved"])
        self.assertEqual("NOT_RUN", result["runtime_evidence"])
        self.assertEqual({"site", "browser", "desktop", "production"}, {
            item["channel"] for item in result["cases"]
        })
        for item in result["cases"]:
            prompt = (out / item["input_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(prompt).hexdigest(), item["input_sha256"])
            self.assertEqual("NOT_RUN", item["execution_state"])
        self.assertFalse(any(out.rglob("*.rubric.*")))
        self.assertNotIn('"must"', (out / "external-lock.json").read_text(encoding="utf-8"))

    def test_no_overwrite_protects_previous_campaign(self):
        out = self.folder / "external"
        mod.prepare(ROOT, self.pack, out)
        with self.assertRaisesRegex(ValueError, "overwrite"):
            mod.prepare(ROOT, self.pack, out)

    def test_wrong_rubric_digest_blocks(self):
        entry = next(x for x in self.lock["cases"] if x["channel"] != "lab")
        entry["rubric_sha256"] = "0" * 64
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "rubric digest"):
            mod.prepare(ROOT, self.pack, self.folder / "out")

    def test_falsified_manifest_or_execution_state_blocks(self):
        self.lock["manifest_sha256"] = "f" * 64
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            mod.prepare(ROOT, self.pack, self.folder / "out")
        self.lock["manifest_sha256"] = parent.digest((ROOT / parent.MANIFEST).read_bytes())
        self.lock["runtime_execution_state"] = "PASS"
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "non-pristine"):
            mod.prepare(ROOT, self.pack, self.folder / "out")

    def test_external_channel_tamper_blocks(self):
        ext = next(x for x in self.lock["cases"] if x["channel"] != "lab")
        ext["channel"] = "lab"
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "identity/channel"):
            mod.prepare(ROOT, self.pack, self.folder / "out")

    def test_external_inputs_without_output_path_never_mutate(self):
        ext = next(x for x in self.lock["cases"] if x["channel"] != "lab")
        ext["input_path"] = "../private"
        self.save_lock()
        with self.assertRaisesRegex(ValueError, "Lab isolation"):
            mod.prepare(ROOT, self.pack, self.folder / "out")


if __name__ == "__main__":
    unittest.main()
