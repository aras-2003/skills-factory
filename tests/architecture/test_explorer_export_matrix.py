"""ARC-07 deterministic source-to-export fixture matrix for both architecture PoCs.

These are CI/source proofs. They do not represent a ChatGPT runtime execution.
"""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.architecture.archify_adapter import (
    UPSTREAM_SHA, RenderError, archify_candidate, offline_svg_fallback, render,
)
from scripts.architecture.export_bundle import ExportError, build_export_bundle
from scripts.architecture.oaf_architecture_explorer import (
    SOURCE as OAF_SOURCE, extract_model as extract_oaf_model,
)
from scripts.architecture.skills_factory_explorer import (
    SKILLS, WORKFLOWS, extract_model as extract_skills_model,
)
from scripts.architecture.visualization_ir import (
    ModelValidationError, model_digest, validate_model, verify_sources,
)

OAF_FIXTURE = """# Fixture

## Scenario

Extract:
- Customer Management
  - Customer Onboarding
  - CRM Team
  - Customer Service Process
  - Customer Data Platform
- Payments
  - Payment Processing
  - Fraud Management
  - Payment Operations
- Data & Analytics
  - Reporting
  - Data Governance
  - Power BI
  - Advanced Analytics

Leadership wants to review the map.
Known evidence:
- ownership is incomplete;
"""


def init_git(root: Path) -> str:
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL,
        ).decode().strip()
    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-qm", "deterministic architecture fixture")
    return git("rev-parse", "HEAD")


def make_oaf_repo(root: Path) -> str:
    path = root / OAF_SOURCE
    path.parent.mkdir(parents=True)
    path.write_text(OAF_FIXTURE, encoding="utf-8")
    return init_git(root)


def make_skills_repo(root: Path) -> str:
    for name in SKILLS:
        path = root / "skills" / "investing" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        ref = (
            f"Uses `{SKILLS[3]}` as its documented canonical store.\n"
            if name != SKILLS[3] else ""
        )
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
        path.write_text(
            f"# {name.replace('-', ' ').title()} Workflow\n\n{body}",
            encoding="utf-8",
        )
    return init_git(root)


class SourceToExportMatrixTests(unittest.TestCase):
    def _assert_source_to_export(self, model, root: Path, out: Path):
        verified = verify_sources(model, root)
        candidate = archify_candidate(verified)
        svg = offline_svg_fallback(verified)
        bundle = build_export_bundle(verified, out)
        self.assertEqual(len(candidate["components"]), len(verified["nodes"]))
        self.assertEqual(len(candidate["connections"]), len(verified["edges"]))
        self.assertEqual(bundle["source_revision"], verified["source_revision"])
        self.assertEqual(bundle["model_digest"], model_digest(verified))
        self.assertEqual(set(bundle["node_ids"]), {n["id"] for n in verified["nodes"]})
        self.assertEqual(set(bundle["edge_ids"]), {e["id"] for e in verified["edges"]})
        self.assertIn("<svg", svg)
        self.assertIn("source_revision", bundle["formats"]["svg"]["diagram_semantics"])
        self.assertEqual(bundle["formats"]["html"]["mode"], "interactive")
        self.assertEqual(bundle["formats"]["pptx"]["mode"], "flattened-embed")
        return bundle

    def test_oaf_source_ir_candidate_and_static_exports_share_exact_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision = make_oaf_repo(root)
            model = extract_oaf_model(root, revision)
            bundle = self._assert_source_to_export(model, root, root / "out")
            self.assertEqual(bundle["source_revision"], revision)
            self.assertTrue(any(n["type"] == "unknown" for n in model["nodes"]))
            self.assertEqual(bundle["node_count"], len(model["nodes"]))
            self.assertEqual(bundle["edge_count"], len(model["edges"]))

    def test_skills_factory_source_ir_candidate_and_static_exports_share_exact_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision = make_skills_repo(root)
            model = extract_skills_model(root, revision)
            bundle = self._assert_source_to_export(model, root, root / "out")
            self.assertEqual(bundle["source_revision"], revision)
            self.assertEqual(sum(n["type"] == "skill" for n in model["nodes"]), len(SKILLS))
            self.assertEqual(sum(n["type"] == "workflow" for n in model["nodes"]), len(WORKFLOWS))

    def test_invalid_source_revision_and_stale_evidence_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision = make_oaf_repo(root)
            with self.assertRaises(ValueError):
                extract_oaf_model(root, "not-a-commit")
            model = extract_oaf_model(root, revision)
            stale = copy.deepcopy(model)
            stale["source_revision"] = "b" * 40
            with self.assertRaises(ModelValidationError):
                validate_model(stale)
            with self.assertRaises(ModelValidationError):
                verify_sources(stale, root)

    def test_unknown_edges_remain_explicit_in_svg_and_text_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision = make_oaf_repo(root)
            model = extract_oaf_model(root, revision)
            unknown_edges = [edge for edge in model["edges"] if edge["state"] == "unknown"]
            self.assertTrue(unknown_edges)
            out = root / "out"
            build_export_bundle(model, out)
            svg = (out / "architecture.svg").read_text(encoding="utf-8")
            text = (out / "architecture.txt").read_text(encoding="utf-8")
            for edge in unknown_edges:
                self.assertIn(edge["id"], svg)
                self.assertIn("UNKNOWN", svg)
                self.assertIn(edge["id"], text)
                self.assertIn("--unknown-->", text)

    def test_renderer_failure_does_not_emit_success_receipt_or_partial_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            cli = upstream / "archify" / "bin"
            cli.mkdir(parents=True)
            (cli / "archify.mjs").write_text("// pinned fixture", encoding="utf-8")
            out = root / "out"
            completed = type("Result", (), {"returncode": 1, "stdout": "", "stderr": ""})()
            model = {
                "schema_version": 1, "model_id": "renderer-failure",
                "source_revision": "a" * 40, "nodes": [], "edges": [],
            }
            with patch("scripts.architecture.archify_adapter.verify_sources", return_value=model), \
                 patch("scripts.architecture.archify_adapter._git_sha", return_value=UPSTREAM_SHA), \
                 patch("scripts.architecture.archify_adapter.subprocess.run", return_value=completed) as run:
                with self.assertRaisesRegex(RenderError, "sandbox image"):
                    render(model, root, upstream, out)
            self.assertEqual(run.call_count, 1)
            self.assertTrue(out.is_dir())
            self.assertEqual(list(out.iterdir()), [])

    def test_invalid_ir_export_fails_before_any_artifact_is_created(self):
        invalid = {
            "schema_version": 1, "model_id": "invalid", "source_revision": "c" * 40,
            "nodes": [], "edges": [{"id": "orphan", "type": "unknown", "from": "x",
                                    "to": "y", "state": "unknown", "evidence": []}],
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            with self.assertRaises(ModelValidationError):
                build_export_bundle(invalid, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
