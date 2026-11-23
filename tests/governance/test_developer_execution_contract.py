"""Static contract checks for the delegated Developer execution path (#767)."""

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "workflows" / "skill-development" / "WORKFLOW.md"


class DeveloperExecutionContractTests(unittest.TestCase):
    def test_workflow_binds_development_to_existing_process_and_tools(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for contract in (
            "exact base SHA", "distinct worktree", "dirty checkout",
            "delivery_control.py", "bootstrap.py", "change_gate.py",
            "test first", "root-cause hypothesis", "stale",
            "diff stats", "exit codes", "host denied the write",
            "DEV-01", "DEV-09", "BLOCKED", "NOT_RUN",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract.lower(), text.lower())
        self.assertNotIn("new task registry", text.lower())

    def test_developer_profiles_carry_worktree_rework_and_evidence_rules(self):
        for profile in ("sf-developer-medium.toml", "sf-developer-high.toml"):
            path = ROOT / ".codex" / "agents" / profile
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            instructions = data["developer_instructions"]
            with self.subTest(profile=profile):
                for required in (
                    "worktree", "base SHA", "shared", "TEST FIRST",
                    "candidate", "fixture", "exit codes", "receipts",
                ):
                    self.assertIn(required.lower(), instructions.lower())


if __name__ == "__main__":
    unittest.main()
