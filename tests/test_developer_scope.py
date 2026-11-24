"""Read-only Git scope checks for issue #767 developer handoffs."""

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.engineering.delegation_handoff import validate_developer_result


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "engineering" / "developer_scope.py"
SPEC = importlib.util.spec_from_file_location("developer_scope", MODULE_PATH)
developer_scope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(developer_scope)


class DeveloperScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Skills Factory Test")
        self.git("config", "user.email", "skills-factory-test@example.invalid")
        (self.repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        self.git("add", "seed.txt")
        self.git("commit", "-q", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, check=True):
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=False,
            capture_output=True,
        )
        if check and result.returncode:
            self.fail(result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("utf-8", "surrogateescape")

    def commit_candidate(self, message="candidate"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def verify(self, candidate, writable, reported):
        return developer_scope.verify_candidate_scope(
            self.repo,
            base_sha=self.base,
            candidate_sha=candidate,
            writable_paths=writable,
            reported_changed_paths=reported,
        )

    def test_dev_scope_01_accepts_exact_committed_diff_inside_directory_grant(self):
        (self.repo / "allowed").mkdir()
        (self.repo / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")
        candidate = self.commit_candidate()

        result = self.verify(candidate, ["allowed/"], ["allowed/change.txt"])

        self.assertEqual("PASS", result["scope_status"])
        self.assertEqual(self.base, result["base_sha"])
        self.assertEqual(candidate, result["candidate_sha"])
        self.assertEqual(["allowed/change.txt"], result["actual_changed_paths"])
        self.assertEqual([], result["violations"])

    def test_dev_scope_02_rejects_ungranted_and_prefix_confusable_paths(self):
        (self.repo / "allowed").mkdir()
        (self.repo / "allowed" / "ok.txt").write_text("ok\n", encoding="utf-8")
        (self.repo / "allowed2").mkdir()
        (self.repo / "allowed2" / "outside.txt").write_text("outside\n", encoding="utf-8")
        candidate = self.commit_candidate()

        result = self.verify(candidate, ["allowed/"], ["allowed/ok.txt", "allowed2/outside.txt"])

        self.assertEqual("FAIL", result["scope_status"])
        self.assertEqual(["allowed/ok.txt", "allowed2/outside.txt"], result["actual_changed_paths"])
        self.assertEqual(["allowed2/outside.txt"], result["violations"])

    def test_dev_scope_03_deletions_and_renames_require_both_paths_in_scope(self):
        (self.repo / "private").mkdir()
        (self.repo / "private" / "old.txt").write_text("old\n", encoding="utf-8")
        base = self.commit_candidate("add private source")
        self.base = base
        (self.repo / "allowed").mkdir()
        (self.repo / "private" / "old.txt").rename(self.repo / "allowed" / "moved.txt")
        candidate = self.commit_candidate("move to allowed")

        result = self.verify(candidate, ["allowed/"], ["allowed/moved.txt", "private/old.txt"])

        self.assertEqual("FAIL", result["scope_status"])
        self.assertEqual(["allowed/moved.txt", "private/old.txt"], result["actual_changed_paths"])
        self.assertEqual(["private/old.txt"], result["violations"])

    def test_dev_scope_04_requires_candidate_checkout_to_be_clean_and_exact(self):
        candidate = self.commit_candidate("empty candidate")
        (self.repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

        result = self.verify(candidate, [], [])

        self.assertEqual("BLOCKED", result["scope_status"])
        self.assertIn("untracked.txt", result["working_tree_paths"])

        (self.repo / "untracked.txt").unlink()
        (self.repo / "staged.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "staged.txt")
        result = self.verify(candidate, [], [])
        self.assertEqual("BLOCKED", result["scope_status"])
        self.assertIn("staged.txt", result["working_tree_paths"])

        self.git("reset", "--hard", "-q", candidate)
        (self.repo / "seed.txt").write_text("unstaged edit\n", encoding="utf-8")
        result = self.verify(candidate, [], [])
        self.assertEqual("BLOCKED", result["scope_status"])
        self.assertIn("seed.txt", result["working_tree_paths"])

        self.git("reset", "--hard", "-q", candidate)
        self.git("checkout", "-q", "--detach", self.base)
        result = self.verify(candidate, [], [])
        self.assertEqual("BLOCKED", result["scope_status"])
        self.assertIn("HEAD", result["violations"])

    def test_dev_scope_05_rejects_path_traversal_and_ambiguous_grants(self):
        candidate = self.commit_candidate("empty candidate")
        for grant in ("../outside", "/absolute", "allowed/../private", "", "allowed//"):
            with self.subTest(grant=grant):
                with self.assertRaises(ValueError):
                    self.verify(candidate, [grant], [])

    def test_dev_scope_06_fails_closed_for_changed_symlink(self):
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        os.symlink(outside, self.repo / "allowed-link")
        candidate = self.commit_candidate("add symlink")

        result = self.verify(candidate, ["allowed-link"], ["allowed-link"])

        self.assertEqual("FAIL", result["scope_status"])
        self.assertIn("allowed-link", result["violations"])

    def test_dev_scope_07_uses_nul_delimited_paths_and_checks_reported_list(self):
        odd_name = "allowed/line\nbreak.txt"
        (self.repo / "allowed").mkdir()
        (self.repo / odd_name).write_text("data\n", encoding="utf-8")
        candidate = self.commit_candidate()

        result = self.verify(candidate, ["allowed/"], [odd_name])

        self.assertEqual("PASS", result["scope_status"])
        self.assertEqual([odd_name], result["actual_changed_paths"])
        mismatch = self.verify(candidate, ["allowed/"], ["allowed/another.txt"])
        self.assertEqual("FAIL", mismatch["scope_status"])
        self.assertIn("reported_changed_paths_mismatch", mismatch["violations"])

    def test_dev_scope_08_rejects_non_descendant_candidate(self):
        root_commit = self.base
        self.git("checkout", "-q", "-b", "expected-base")
        (self.repo / "base-only.txt").write_text("base\n", encoding="utf-8")
        expected_base = self.commit_candidate("expected base child")
        self.base = expected_base
        self.git("checkout", "-q", "-b", "other", root_commit)
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        candidate = self.commit_candidate("unrelated candidate")

        result = self.verify(candidate, [], ["other.txt"])

        self.assertEqual("BLOCKED", result["scope_status"])
        self.assertIn("candidate_not_descendant", result["violations"])

    def test_dev_scope_09_developer_pass_requires_repository_bound_scope(self):
        (self.repo / "allowed").mkdir()
        (self.repo / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")
        candidate = self.commit_candidate()
        payload = {
            "task_id": "dev-1", "role": "sf-developer-high", "status": "PASS",
            "candidate_sha": candidate, "changed_paths": ["allowed/change.txt"],
            "test_case_outcomes": [{"case_id": "DEV-01", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["https://github.com/example/evidence"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }

        result = validate_developer_result(
            payload, repo=self.repo, expected_task_id="dev-1",
            expected_role="sf-developer-high", expected_test_case_ids=["DEV-01"],
            expected_base_sha=self.base, writable_paths=["allowed/"],
            expected_candidate_sha=candidate,
        )

        self.assertEqual("PASS", result["result"]["status"])
        self.assertEqual("PASS", result["scope_verification"]["scope_status"])

    def test_dev_scope_10_rejects_developer_pass_outside_scope(self):
        (self.repo / "secret.txt").write_text("outside\n", encoding="utf-8")
        candidate = self.commit_candidate()
        payload = {
            "task_id": "dev-1", "role": "sf-developer-high", "status": "PASS",
            "candidate_sha": candidate, "changed_paths": ["secret.txt"],
            "test_case_outcomes": [{"case_id": "DEV-01", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["https://github.com/example/evidence"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }

        with self.assertRaisesRegex(ValueError, "without a PASS scope verification"):
            validate_developer_result(
                payload, repo=self.repo, expected_task_id="dev-1",
                expected_role="sf-developer-high", expected_test_case_ids=["DEV-01"],
                expected_base_sha=self.base, writable_paths=["allowed/"],
                expected_candidate_sha=candidate,
            )

    def test_dev_scope_11_rejects_developer_pass_when_checkout_is_dirty(self):
        candidate = self.commit_candidate("empty candidate")
        (self.repo / "untracked.txt").write_text("uncommitted\n", encoding="utf-8")
        payload = {
            "task_id": "dev-1", "role": "sf-developer-high", "status": "PASS",
            "candidate_sha": candidate, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "DEV-01", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["https://github.com/example/evidence"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }

        with self.assertRaisesRegex(ValueError, "without a PASS scope verification"):
            validate_developer_result(
                payload, repo=self.repo, expected_task_id="dev-1",
                expected_role="sf-developer-high", expected_test_case_ids=["DEV-01"],
                expected_base_sha=self.base, writable_paths=[],
                expected_candidate_sha=candidate,
            )


if __name__ == "__main__":
    unittest.main()
