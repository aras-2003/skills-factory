import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("sdlc_bootstrap", Path(__file__).resolve().parents[1] / "bootstrap.py")
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def test_importable_but_wrong_version_is_not_a_valid_environment(self):
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "lock"
            lock.write_text("mcp==2.3.0 \\\n    --hash=sha256:example\n")
            with patch.object(bootstrap.importlib.metadata, "version", return_value="1.0.0"):
                self.assertEqual(["mcp: expected 2.3.0, installed 1.0.0"], bootstrap.dependency_errors(lock))
            with patch.object(bootstrap.importlib.metadata, "version", return_value="2.3.0"):
                self.assertEqual([], bootstrap.dependency_errors(lock))

    def test_failed_check_preserves_existing_user_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            lock = root / "requirements-dev.lock"
            lock.write_text("missing-test-package==9.9.9\n", encoding="utf-8")
            user_file = root / "user-change.md"
            user_file.write_text("preserve this dirty file\n", encoding="utf-8")
            with (patch.object(bootstrap, "ROOT", root),
                  patch.object(sys, "argv", ["bootstrap.py", "--check"]),
                  patch.object(bootstrap.importlib.metadata, "version",
                               side_effect=bootstrap.importlib.metadata.PackageNotFoundError)):
                self.assertEqual(1, bootstrap.main())
            self.assertEqual("preserve this dirty file\n", user_file.read_text(encoding="utf-8"))
            self.assertTrue((root / ".tmp/python-tests").is_dir())

    def test_independent_git_worktrees_keep_changes_isolated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            (root / "base.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "base.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            first, second = root.parent / "worker-a", root.parent / "worker-b"
            subprocess.run(["git", "-C", str(root), "worktree", "add", "-qb", "worker-a", str(first)], check=True)
            subprocess.run(["git", "-C", str(root), "worktree", "add", "-qb", "worker-b", str(second)], check=True)
            (first / "a.txt").write_text("worker a\n", encoding="utf-8")
            (second / "b.txt").write_text("worker b\n", encoding="utf-8")
            self.assertTrue((first / "a.txt").exists())
            self.assertFalse((second / "a.txt").exists())
            self.assertTrue((second / "b.txt").exists())
            self.assertFalse((first / "b.txt").exists())
            status = subprocess.run(["git", "-C", str(root), "worktree", "list", "--porcelain"],
                                    check=True, capture_output=True, text=True).stdout
            self.assertEqual(3, status.count("worktree "))
