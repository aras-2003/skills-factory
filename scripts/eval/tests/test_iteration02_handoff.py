from __future__ import annotations

import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "scripts/eval/iteration02_handoff.py"
spec = importlib.util.spec_from_file_location("iteration02_handoff", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class Iteration02HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def fixture(self, modify=lambda x: None):
        original, errors = mod.validate(ROOT)
        self.assertFalse(errors, errors)
        content = copy.deepcopy(original)
        modify(content)
        root = self.base / "repo"
        manifest = root / mod.MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(content), encoding="utf-8")
        return root

    def fake_lab(self):
        folder = self.base / "lab"
        folder.mkdir()
        (folder / "release-manifest.json").write_text(json.dumps({
            "source_revision": "a" * 40, "payload_content_sha256": "b" * 64,
            "channel": "lab", "release_id": "fixture-release",
        }), encoding="utf-8")
        (folder / "plugin.json").write_text('{"name":"skills-factory-lab"}', encoding="utf-8")
        return folder

    def test_every_eighteen_issue_and_channel_is_explicit(self):
        cfg, errors = mod.validate(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(18, len(cfg["legacy_issues"]))
        self.assertEqual(18, len(cfg["cases"]))
        self.assertTrue(all(x["execution_state"] == "NOT_RUN" for x in cfg["cases"]))

    def test_duplicate_case_is_blocked(self):
        root = self.fixture(lambda x: x["cases"].append(copy.deepcopy(x["cases"][0])))
        _, errors = mod.validate(root)
        self.assertTrue(any("duplicate" in x for x in errors))

    def test_uncovered_issue_blocked(self):
        root = self.fixture(lambda x: x["cases"].pop())
        _, errors = mod.validate(root)
        self.assertTrue(any("uncovered" in x for x in errors))

    def test_faked_pass_is_rejected(self):
        root = self.fixture(lambda x: x["cases"][0].update(execution_state="PASS"))
        _, errors = mod.validate(root)
        self.assertTrue(any("premature" in x for x in errors))

    def test_exact_lab_pack_separates_assessor_and_provider(self):
        folder = self.fake_lab()
        with patch.dict(os.environ, {"SOURCE_REVISION": "a" * 40}):
            lock = mod.prepare(folder, self.base / "executor", ROOT)
        self.assertEqual("NOT_RUN", lock["runtime_execution_state"])
        self.assertFalse(lock["release_approved"])
        self.assertEqual(18, len(lock["cases"]))
        lab_cases = [c for c in lock["cases"] if c["channel"] == "lab"]
        external = [c for c in lock["cases"] if c["channel"] != "lab"]
        self.assertEqual(11, len(lab_cases))
        self.assertEqual(7, len(external))
        self.assertTrue(all(c["input_path"] is None for c in external))
        self.assertEqual(11, len(list((self.base / "executor/executor-inputs").glob("*.input.md"))))
        self.assertNotIn('"must"', json.dumps(lock))

    def test_stale_lab_and_overwrite_rejected(self):
        folder = self.fake_lab()
        with patch.dict(os.environ, {"SOURCE_REVISION": "c" * 40}):
            with self.assertRaisesRegex(ValueError, "mismatch"):
                mod.prepare(folder, self.base / "out", ROOT)
        (self.base / "out").mkdir()
        with patch.dict(os.environ, {"SOURCE_REVISION": "a" * 40}):
            with self.assertRaisesRegex(ValueError, "overwrite"):
                mod.prepare(folder, self.base / "out", ROOT)


if __name__ == "__main__":
    unittest.main()
