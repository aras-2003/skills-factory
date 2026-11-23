"""Static contract checks for SDLC Deep role profiles and architecture method."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "docs" / "governance" / "SDLC-ROLE-CAPABILITY-MATRIX.md"
ARCHITECTURE = ROOT / "docs" / "architecture" / "SOFTWARE-ARCHITECTURE-DECISIONS.md"
ADR_TEMPLATE = ROOT / "templates" / "architecture" / "software-decision.md"
ARCHITECT_PROFILE = ROOT / ".codex" / "agents" / "sf-architect.toml"
PILOT = ROOT / "docs" / "governance" / "CODEX-SUBAGENT-PILOT.md"
WORKED_DECISION = ROOT / "docs" / "architecture" / "decisions" / "2026-11-load-skill-source-pin.md"


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
            "changed shared contract", "selected source tree",
            "--graph-reviewed", "full affected-channel baseline",
        ):
            with self.subTest(contract=required):
                self.assertIn(required, text)

    def test_architecture_template_captures_evidence_migration_and_recovery(self):
        text = ADR_TEMPLATE.read_text(encoding="utf-8")
        for required in (
            "Architecture Impact", "Baseline source SHA", "Candidate source SHA",
            "Producer / interface", "Consumer", "Source path and line", "UNKNOWN",
            "Trust boundaries", "Security negative tests", "REUSE | EXTEND | COMPOSE | CREATE",
            "Compatibility/version behavior", "Ordered migration or rollout steps", "Rollback steps",
            "Case ID", "Independent review", "Stale-decision rule", "REVIEW_REQUIRED",
        ):
            with self.subTest(contract=required):
                self.assertIn(required, text)

    def test_architect_role_routes_to_method_and_source_grounded_worked_decision(self):
        profile = ARCHITECT_PROFILE.read_text(encoding="utf-8")
        pilot = PILOT.read_text(encoding="utf-8")
        decision = WORKED_DECISION.read_text(encoding="utf-8")
        for path in (ARCHITECTURE.name, "templates/architecture/software-decision.md"):
            with self.subTest(profile=path):
                self.assertIn(path, profile)
        self.assertIn("SOFTWARE-ARCHITECTURE-DECISIONS.md", pilot)
        self.assertIn("2026-11-load-skill-source-pin.md", ARCHITECTURE.read_text(encoding="utf-8"))
        for required in (
            "e0f613cbaf80cf4a278e713794662250dab2b8bc",
            "runtime/contracts/mcp-tools-v1.json",
            "runtime/mcp/server.py",
            "runtime/mcp/skill_catalog.py",
            "adapters/skills-factory-cloud-next/src/cloud-tools.ts",
            "Safe extension", "Breaking alternative", "Trust boundary",
            "Rollback", "REVIEW_REQUIRED", "NOT_RUN",
        ):
            with self.subTest(evidence=required):
                self.assertIn(required, decision)


if __name__ == "__main__":
    unittest.main()
