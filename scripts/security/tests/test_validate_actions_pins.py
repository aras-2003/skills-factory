from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/security"))
from validate_actions_pins import validate_directory, validate_workflow  # noqa: E402


class ActionPinTests(unittest.TestCase):
    def check(self, reference):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.yml"
            path.write_text(f'jobs:\n  test:\n    steps:\n      - uses: {reference}\n', encoding="utf-8")
            return validate_workflow(path)

    def test_immutable_commit_passes(self):
        self.assertFalse(self.check("actions/checkout@" + "a" * 40))

    def test_mutable_tags_and_branches_fail(self):
        for ref in ["actions/checkout@v4", "someone/action@main", "actions/checkout"]:
            with self.subTest(ref=ref):
                self.assertTrue(self.check(ref))

    def test_docker_requires_digest(self):
        self.assertTrue(self.check("docker://alpine:latest"))
        self.assertFalse(self.check("docker://alpine@sha256:" + "b" * 64))

    def test_local_action_is_allowed(self):
        self.assertFalse(self.check("./.github/actions/local"))

    def test_repository_workflows_pinned(self):
        self.assertEqual([], validate_directory(ROOT))


if __name__ == "__main__":
    unittest.main()
