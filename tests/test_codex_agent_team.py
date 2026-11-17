"""Contract tests for issue #748 project-scoped Codex agent configuration.

These tests validate static structure/policy only. They cannot prove that
Codex actually spawned agents, honored model routing or executed test cases.
"""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".codex" / "agents"
EXPECTED = {
    "sf-solution-architect": ("gpt-6.2-sol", "high"),
    "sf-developer-medium": ("gpt-6-luna", "medium"),
    "sf-developer-high": ("gpt-6-luna", "high"),
    "sf-test-designer": ("gpt-6-luna", "medium"),
    "sf-test-executor": ("gpt-6-luna", "low"),
    "sf-independent-reviewer": ("gpt-6-luna", "high"),
    "sf-skill-evaluator": ("gpt-6-luna", "high"),
    "sf-research-analyst": ("gpt-6-luna", "low"),
    "sf-research-medium": ("gpt-6-luna", "medium"),
    "sf-release-evidence": ("gpt-6-luna", "low"),
}


class CodexTeamContractTest(unittest.TestCase):
    def test_primary_medium_and_bounded_threads(self):
        with (ROOT / ".codex" / "config.toml").open("rb") as handle:
            data = tomllib.load(handle)
        self.assertEqual(data["model"], "gpt-6-luna")
        self.assertEqual(data["model_reasoning_effort"], "medium")
        self.assertTrue(data["agents"]["enabled"])
        self.assertEqual(data["agents"]["max_concurrent_threads_per_session"], 2)
        self.assertEqual(data["agents"]["default_subagent_model"], "gpt-6-luna")

    def test_roles_are_unique_and_match_requested_models(self):
        actual = {file.stem for file in AGENTS.glob("*.toml")}
        self.assertTrue(set(EXPECTED).issubset(actual))
        self.assertNotIn("sf-test-engineer", actual)
        names = []
        for name, (model, effort) in EXPECTED.items():
            with (AGENTS / f"{name}.toml").open("rb") as handle:
                data = tomllib.load(handle)
            self.assertEqual(data["name"], name)
            self.assertEqual(data["model"], model)
            self.assertEqual(data["model_reasoning_effort"], effort)
            self.assertTrue(data["description"].strip())
            self.assertTrue(data["developer_instructions"].strip())
            names.append(data["name"])
        self.assertEqual(len(names), len(set(names)))

    def test_context_and_evidence_policy(self):
        guide = (ROOT / "docs" / "governance" / "CODEX-SUBAGENT-PILOT.md").read_text()
        instructions = (ROOT / "AGENTS.md").read_text()
        for marker in (
            "Context isolation contract",
            "candidate_sha",
            "NOT_RUN",
            "BLOCKED",
            "new Codex chat",
        ):
            self.assertIn(marker, guide)
        for marker in (
            "sf-developer-medium",
            "sf-developer-high",
            "sf-test-designer",
            "sf-test-executor",
            "sf-solution-architect",
        ):
            self.assertIn(marker, instructions)
        self.assertIn("SDLC-OPERATING-PROCESS.md", instructions)


if __name__ == "__main__":
    unittest.main()
