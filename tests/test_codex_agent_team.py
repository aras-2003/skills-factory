"""Static contract tests for the project-scoped Codex agent team."""

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".codex" / "config.toml"
AGENT_DIR = ROOT / ".codex" / "agents"
EXPECTED = {
    "sf-architect": ("gpt-6.2-sol", "high"),
    "sf-developer-medium": ("gpt-6-luna", "medium"),
    "sf-developer-high": ("gpt-6-luna", "high"),
    "sf-test-designer": ("gpt-6-luna", "medium"),
    "sf-test-executor": ("gpt-6-luna", "low"),
    "sf-independent-reviewer": ("gpt-6-luna", "high"),
    "sf-skill-evaluator": ("gpt-6-luna", "high"),
    "sf-researcher-low": ("gpt-6-luna", "low"),
    "sf-researcher-medium": ("gpt-6-luna", "medium"),
    "sf-release-evidence": ("gpt-6-luna", "low"),
}


def load_toml(path):
    with path.open("rb") as stream:
        return tomllib.load(stream)


class CodexAgentTeamContractTests(unittest.TestCase):
    def test_project_config_bounds_child_threads_without_pinning_primary(self):
        agents = load_toml(CONFIG)["agents"]
        self.assertIs(agents["enabled"], True)
        self.assertEqual(agents["max_concurrent_threads_per_session"], 2)
        self.assertEqual(agents["default_subagent_model"], "gpt-6-luna")
        self.assertEqual(agents["default_subagent_reasoning_effort"], "medium")
        self.assertNotIn("model", agents)
        self.assertNotIn("primary_model", agents)

    def test_exact_role_inventory_and_model_effort(self):
        files = {path.stem: path for path in AGENT_DIR.glob("*.toml")}
        self.assertEqual(set(files), set(EXPECTED))
        for name, (model, effort) in EXPECTED.items():
            with self.subTest(agent=name):
                agent = load_toml(files[name])
                self.assertEqual(agent["name"], name)
                self.assertEqual(agent["model"], model)
                self.assertEqual(agent["model_reasoning_effort"], effort)
                self.assertTrue(agent["description"].strip())
                self.assertTrue(agent["developer_instructions"].strip())

    def test_roles_preserve_design_execution_and_write_boundaries(self):
        designer = load_toml(AGENT_DIR / "sf-test-designer.toml")["developer_instructions"]
        executor = load_toml(AGENT_DIR / "sf-test-executor.toml")["developer_instructions"]
        developer = load_toml(AGENT_DIR / "sf-developer-medium.toml")["developer_instructions"]
        reviewer = load_toml(AGENT_DIR / "sf-independent-reviewer.toml")["developer_instructions"]
        self.assertIn("stable case IDs", designer)
        self.assertIn("do not edit implementation", designer)
        self.assertIn("Do not edit source", executor)
        self.assertIn("exact candidate SHA", executor)
        self.assertIn("NOT_RUN or BLOCKED", executor)
        self.assertIn("Implement only the assigned issue", developer)
        self.assertIn("Do not implement fixes", reviewer)

    def test_evaluator_and_release_roles_fail_closed(self):
        evaluator = load_toml(AGENT_DIR / "sf-skill-evaluator.toml")["developer_instructions"]
        release = load_toml(AGENT_DIR / "sf-release-evidence.toml")["developer_instructions"]
        self.assertIn("held-out cases", evaluator)
        self.assertIn("NOT_SCORABLE", evaluator)
        self.assertIn("Do not alter status fields", release)
        self.assertIn("NOT_RUN/BLOCKED", release)

    def test_project_instructions_route_to_distinct_roles(self):
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        runbook = (ROOT / "docs" / "governance" / "CODEX-SUBAGENT-PILOT.md").read_text(encoding="utf-8")
        self.assertIn("sf-test-designer", instructions)
        self.assertIn("sf-test-executor", instructions)
        self.assertIn("sf-independent-reviewer", instructions)
        self.assertIn("sf-architect", runbook)
        self.assertIn("sf-developer-high", runbook)
        self.assertNotIn("sf-test-engineer", instructions)
        self.assertNotIn("sf-test-engineer", runbook)

    def test_smoke_protocol_keeps_missing_delegation_blocked(self):
        runbook = (ROOT / "docs" / "governance" / "CODEX-SUBAGENT-PILOT.md").read_text(encoding="utf-8")
        for expected in (
            "Include a negative case",
            "BLOCKED/NOT_RUN",
            "CONFIG_PARSED",
            "SUBAGENT_SPAWN",
            "MODEL_IDENTITY",
            "TEST_DESIGN",
            "TEST_EXECUTION",
            "REVIEW_INDEPENDENCE",
            "GitHub issue and source tree at that exact revision as the source of truth",
            "exclude stale chat context",
            "RUNTIME",
        ):
            with self.subTest(contract=expected):
                self.assertIn(expected, runbook)
