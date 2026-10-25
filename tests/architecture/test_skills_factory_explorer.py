"""Source-derived ARC-04 explorer contracts."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.architecture.skills_factory_explorer import (
    ExplorerError, SKILLS, WORKFLOWS, dependency_cycles, extract_model,
    gate_report, traverse,
)
from scripts.architecture.visualization_ir import verify_sources


def make_repo(root: Path) -> str:
    for name in SKILLS:
        path = root / "skills" / "investing" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        ref = f"Uses `{SKILLS[3]}` as its documented canonical store.\n" if name != SKILLS[3] else ""
        path.write_text(
            f"---\nname: {name}\n---\n# {name.replace('-', ' ').title()}\n\n{ref}",
            encoding="utf-8",
        )
    for index, name in enumerate(WORKFLOWS):
        path = root / "workflows" / name / "WORKFLOW.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        body = f"Select `{SKILLS[index]}` for the documented route.\n"
        if index == 0:
            body += "If the child receipt is missing, stop before producing a result.\n"
        path.write_text(f"# {name.replace('-', ' ').title()} Workflow\n\n{body}", encoding="utf-8")
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()
    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-qm", "fixture")
    return git("rev-parse", "HEAD")


class SkillsFactoryExplorerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.revision = make_repo(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_extracts_pinned_13_skill_slice_with_verified_sources(self):
        model = extract_model(self.root, self.revision)
        skills = [node for node in model["nodes"] if node["type"] == "skill"]
        workflows = [node for node in model["nodes"] if node["type"] == "workflow"]
        self.assertEqual(len(skills), 13)
        self.assertEqual(len(workflows), 7)
        self.assertEqual(verify_sources(model, self.root)["source_revision"], self.revision)
        self.assertTrue(all(node["evidence"] for node in skills + workflows))

    def test_traversal_follows_documented_dependencies(self):
        model = extract_model(self.root, self.revision)
        reachable = traverse(model, "workflow:investment-attention-review")
        self.assertIn(f"skill:{SKILLS[0]}", reachable)
        self.assertIn(f"skill:{SKILLS[3]}", reachable)

    def test_missing_and_unexecuted_gates_are_explicit_unknowns(self):
        model = extract_model(self.root, self.revision)
        report = gate_report(model)
        self.assertEqual(report["missing_gate_documentation"], [
            "gate:investment-portfolio-review:undocumented",
            "gate:investment-security-review:undocumented",
            "gate:investment-theme-discovery:undocumented",
        ])
        self.assertEqual(len(report["runtime_not_run"]), len(WORKFLOWS))
        unknown_edges = [edge for edge in model["edges"] if edge["state"] == "unknown"]
        self.assertGreaterEqual(len(unknown_edges), len(WORKFLOWS))

    def test_cycle_detector_reports_documented_workflow_cycle(self):
        model = extract_model(self.root, self.revision)
        model["edges"].extend([
            {"id":"cycle-a","type":"calls","from":"workflow:investment-attention-review",
             "to":"workflow:investment-opportunity-hunter","state":"observed",
             "evidence":[{"uri":"repo://workflows/investment-attention-review/WORKFLOW.md",
                          "revision":self.revision,"locator":"L1"}]},
            {"id":"cycle-b","type":"calls","from":"workflow:investment-opportunity-hunter",
             "to":"workflow:investment-attention-review","state":"observed",
             "evidence":[{"uri":"repo://workflows/investment-opportunity-hunter/WORKFLOW.md",
                          "revision":self.revision,"locator":"L1"}]},
        ])
        cycles = dependency_cycles(model)
        self.assertEqual(cycles, [[
            "workflow:investment-attention-review",
            "workflow:investment-opportunity-hunter",
        ]])

    def test_bad_revision_fails_closed(self):
        with self.assertRaises(ExplorerError):
            extract_model(self.root, "not-a-commit")


if __name__ == "__main__":
    unittest.main()
