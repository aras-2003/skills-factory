from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "release_bundle.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("release_bundle", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ReleaseBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.lab, self.out = base / "source", base / "lab", base / "campaign"
        self.root.mkdir()
        self.lab.mkdir()
        suite = self.root / "skills/example/tests/cases.yaml"
        suite.parent.mkdir(parents=True)
        suite.write_text('cases:\n  - id: positive\n    case: positive\n    input: "Analyze synthetic facts."\n    expected:\n      should_trigger: true\n      must: ["secret evaluator assertion"]\n')
        registry = self.root / "evals/runtime-fixtures.yaml"
        registry.parent.mkdir()
        registry.write_text("targets: {}\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()
        (self.lab / "release-manifest.json").write_text(json.dumps({"source_revision": self.revision, "channel": "lab", "components": [{"name": "example"}]}))

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True)

    def test_executor_does_not_receive_expectations_or_results(self):
        result = mod.prepare(self.out, self.lab, self.root)
        self.assertEqual(0, result["runtime_executed"])
        self.assertEqual(2, result["cases"])
        for path in (self.out / "executor").iterdir():
            self.assertNotIn("secret evaluator assertion", path.read_text())
        mod.validate(self.out, self.root)

    def test_rejects_wrong_lab_revision(self):
        p = self.lab / "release-manifest.json"
        m = json.loads(p.read_text()); m["source_revision"] = "0" * 40; p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            mod.prepare(self.out, self.lab, self.root)

    def test_rejects_dirty_source_and_historical_overwrite(self):
        source = self.root / "evals/runtime-fixtures.yaml"
        source.write_text("targets: {}\n# changed\n")
        with self.assertRaisesRegex(ValueError, "commit source"):
            mod.prepare(self.out, self.lab, self.root)
        source.write_text("targets: {}\n")
        mod.prepare(self.out, self.lab, self.root)
        with self.assertRaisesRegex(ValueError, "preserve prior"):
            mod.prepare(self.out, self.lab, self.root)

    def test_detects_input_tampering_and_fabricated_pass(self):
        mod.prepare(self.out, self.lab, self.root)
        queue_path = self.out / "queue.json"
        queue = json.loads(queue_path.read_text())
        case = queue["cases"][0]
        inp = self.out / case["input"]
        original = inp.read_bytes()
        inp.write_text("Altered fixture")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            mod.validate(self.out, self.root)
        inp.write_bytes(original)
        case["status"] = "PASS"
        queue_path.write_text(json.dumps(queue))
        with self.assertRaisesRegex(ValueError, "fabricate"):
            mod.validate(self.out, self.root)

    def test_detects_source_drift_after_freeze(self):
        mod.prepare(self.out, self.lab, self.root)
        (self.root / "evals/runtime-fixtures.yaml").write_text("targets: {}\n# drift\n")
        with self.assertRaisesRegex(ValueError, "source content drift"):
            mod.validate(self.out, self.root)


if __name__ == "__main__":
    unittest.main()
