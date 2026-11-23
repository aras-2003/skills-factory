"""Static contract checks for SDLC Deep role profiles and architecture method."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "docs" / "governance" / "SDLC-ROLE-CAPABILITY-MATRIX.md"
ARCHITECTURE = ROOT / "docs" / "architecture" / "SOFTWARE-ARCHITECTURE-DECISIONS.md"


class RoleCapabilityContractTests(unittest.TestCase):
    def test_matrix_covers_all_roles_and_distinguishes_enforcement(self):
        text = PROFILES.read_text(encoding="utf-8")
        for role in (
            "Coordinator", "Research", "Architect", "Developer",
            "Test Designer", "Test Executor", "Independent Reviewer",
            "Skill Evaluator", "Release/Evidence",
        ):
            with self.subTest(role=role):
                self.assertIn(role, text)
        for state in ("ENFORCED", "INSTRUCTION_ONLY", "UNAVAILABLE"):
            self.assertIn(state, text)
        self.assertIn("not an OS sandbox", text)
        self.assertIn("secret", text.lower())
        self.assertIn("production", text.lower())

    def test_architecture_method_is_sha_bound_and_has_fail_closed_cases(self):
        text = ARCHITECTURE.read_text(encoding="utf-8")
        for required in (
            "REUSE", "EXTEND", "COMPOSE", "CREATE", "exact baseline SHA",
            "direct and transitive consumers", "UNKNOWN", "migration",
            "rollback", "A0", "A1", "A2", "A3", "A4",
            "ARCH-02", "ARCH-03", "ARCH-05", "ARCH-07",
            "OAF", "implementation-brief", "skill-specification",
            "changed shared contract",
        ):
            with self.subTest(contract=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
