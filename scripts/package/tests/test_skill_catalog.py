from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "runtime" / "mcp" / "skill_catalog.py"


def load_catalog():
    spec = importlib.util.spec_from_file_location("skills_factory_skill_catalog", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load skill catalog")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog()

    def test_catalog_lists_packaged_lab_skills(self) -> None:
        result = self.catalog.list_skills()
        names = {item["name"] for item in result["skills"]}
        self.assertIn("skill-test-design", names)
        self.assertIn("skill-evaluation", names)
        self.assertTrue(result["catalog_digest"])

    def test_catalog_keeps_packaged_inventory_distinct_from_governance_acceptance(self) -> None:
        result = self.catalog.list_skills()
        boundary = result["evidence_boundary"]
        self.assertIn("not historical backlog", boundary["scope"])
        self.assertIn("exact source revision", boundary["reconciliation"])
        self.assertIn("BLOCKED_SOURCE_REVISION", boundary["unverified_revision"])
        self.assertNotIn("project_membership_verified", result)
        self.assertNotIn("runtime_acceptance", result)

    def test_load_skill_returns_exact_instructions_and_digest(self) -> None:
        result = self.catalog.load_skill("skill-test-design")
        self.assertIn("Skill Test Design", result["instructions"])
        self.assertEqual("host_model_executes_loaded_instructions", result["execution_mode"])
        self.assertTrue(result["content_sha256"])

    def test_skill_name_cannot_escape_catalog(self) -> None:
        with self.assertRaises(ValueError):
            self.catalog.load_skill("../README")

    def test_configured_catalog_root_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "skills"
            skill = root / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: Example\nmetadata:\n  version: '1'\n  maturity: candidate\n---\n\n# Example\n",
                encoding="utf-8",
            )
            previous = os.environ.get("SKILLS_FACTORY_SKILLS_ROOT")
            os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = str(root)
            try:
                result = self.catalog.list_skills()
                self.assertEqual(["example"], [item["name"] for item in result["skills"]])
            finally:
                if previous is None:
                    os.environ.pop("SKILLS_FACTORY_SKILLS_ROOT", None)
                else:
                    os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = previous

    def test_packaged_catalog_overrides_stale_host_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_root = root / "package"
            packaged_skill = package_root / "skills" / "example"
            stale_root = root / "stale-skills"
            stale_skill = stale_root / "example"
            packaged_skill.mkdir(parents=True)
            stale_skill.mkdir(parents=True)
            (package_root / "release-manifest.json").write_text("{}", encoding="utf-8")
            (packaged_skill / "SKILL.md").write_text(
                "---\\nname: example\\n---\\n\\n# Packaged version\\n", encoding="utf-8"
            )
            (stale_skill / "SKILL.md").write_text(
                "---\\nname: example\\n---\\n\\n# Stale version\\n", encoding="utf-8"
            )
            previous_plugin_root = os.environ.get("PLUGIN_ROOT")
            previous_skills_root = os.environ.get("SKILLS_FACTORY_SKILLS_ROOT")
            os.environ["PLUGIN_ROOT"] = str(package_root)
            os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = str(stale_root)
            try:
                result = self.catalog.load_skill("example")
            finally:
                if previous_plugin_root is None:
                    os.environ.pop("PLUGIN_ROOT", None)
                else:
                    os.environ["PLUGIN_ROOT"] = previous_plugin_root
                if previous_skills_root is None:
                    os.environ.pop("SKILLS_FACTORY_SKILLS_ROOT", None)
                else:
                    os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = previous_skills_root
            self.assertIn("Packaged version", result["instructions"])
            self.assertNotIn("Stale version", result["instructions"])

    def test_load_skill_includes_safe_references_but_excludes_eval_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "skills"
            skill = root / "example"
            references = skill / "references"
            (references / "evals").mkdir(parents=True)
            skill.mkdir(parents=True, exist_ok=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: Example\n---\n\n# Example\n",
                encoding="utf-8",
            )
            (references / "WORKFLOW.md").write_text("# Workflow\nDo the work.\n", encoding="utf-8")
            (references / "evals" / "secret.md").write_text("hidden rubric", encoding="utf-8")
            (references / "binary.bin").write_bytes(b"not text")
            previous = os.environ.get("SKILLS_FACTORY_SKILLS_ROOT")
            os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = str(root)
            try:
                result = self.catalog.load_skill("example")
            finally:
                if previous is None:
                    os.environ.pop("SKILLS_FACTORY_SKILLS_ROOT", None)
                else:
                    os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = previous
            self.assertEqual(
                [{"path": "references/WORKFLOW.md", "content": "# Workflow\nDo the work.\n"}],
                result["reference_files"],
            )

    def test_reference_symlinks_are_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "skills"
            skill = root / "example"
            references = skill / "references"
            references.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: example\n---\nbody\n", encoding="utf-8")
            outside = Path(temp_dir) / "outside.md"
            outside.write_text("not packaged", encoding="utf-8")
            (references / "linked.md").symlink_to(outside)
            previous = os.environ.get("SKILLS_FACTORY_SKILLS_ROOT")
            os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = str(root)
            try:
                result = self.catalog.load_skill("example")
            finally:
                if previous is None:
                    os.environ.pop("SKILLS_FACTORY_SKILLS_ROOT", None)
                else:
                    os.environ["SKILLS_FACTORY_SKILLS_ROOT"] = previous
            self.assertEqual([], result["reference_files"])

    def test_public_digest_excludes_eval_and_test_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "example"
            (skill / "references" / "evals").mkdir(parents=True)
            (skill / "tests").mkdir()
            (skill / "SKILL.md").write_text("# Example\nPublic instructions.\n", encoding="utf-8")
            (skill / "references" / "evals" / "case.input.md").write_text("one", encoding="utf-8")
            (skill / "tests" / "cases.yaml").write_text("one", encoding="utf-8")
            initial = self.catalog._tree_digest(skill)
            (skill / "references" / "evals" / "case.input.md").write_text("two", encoding="utf-8")
            (skill / "tests" / "cases.yaml").write_text("two", encoding="utf-8")
            self.assertEqual(initial, self.catalog._tree_digest(skill))

    def test_legacy_eval_appendix_is_removed_from_loaded_instructions(self) -> None:
        instructions = "# Example\nPublic text.\n\n## Lab runtime eval inputs\n- `references/evals/case.input.md`\n"
        self.assertEqual("# Example\nPublic text.", self.catalog._public_instructions(instructions))


if __name__ == "__main__":
    unittest.main()
