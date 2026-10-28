from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch
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


def payload_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path for path in root.rglob("*") if path.is_file()):
        if item.relative_to(root).as_posix() == "release-manifest.json":
            continue
        relative = item.relative_to(root).as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


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

    def test_packaged_payload_integrity_matches_manifest_and_detects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_root = Path(temp_dir) / "package"
            (package_root / "mcp").mkdir(parents=True)
            payload = package_root / "mcp" / "server.py"
            payload.write_text("runtime", encoding="utf-8")
            manifest = {
                "channel": "lab",
                "version": "1.38.313",
                "release_id": "1.38.313+aaaaaaaaaaaa",
                "source_revision": "a" * 40,
                "payload_content_sha256": payload_digest(package_root),
            }
            (package_root / "release-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            previous = os.environ.get("PLUGIN_ROOT")
            previous_revision = os.environ.get("SKILLS_FACTORY_SOURCE_REVISION")
            os.environ["PLUGIN_ROOT"] = str(package_root)
            os.environ.pop("SKILLS_FACTORY_SOURCE_REVISION", None)
            try:
                self.assertEqual(
                    {"status": "verified", "payload_content_sha256": manifest["payload_content_sha256"]},
                    self.catalog.packaged_payload_integrity(),
                )
                self.assertEqual(
                    "a" * 40, self.catalog.packaged_runtime_value("source_revision")
                )
                payload.write_text("mutated runtime", encoding="utf-8")
                self.assertEqual(
                    "mismatch", self.catalog.packaged_payload_integrity()["status"]
                )
                self.assertEqual(
                    "unattested", self.catalog.packaged_runtime_value("source_revision")
                )

                external_dir = Path(temp_dir) / "external"
                external_dir.mkdir()
                (external_dir / "injected.py").write_text("unbound runtime", encoding="utf-8")
                (package_root / "linked-runtime").symlink_to(
                    external_dir, target_is_directory=True
                )
                self.assertEqual(
                    "mismatch", self.catalog.packaged_payload_integrity()["status"]
                )
            finally:
                if previous is None:
                    os.environ.pop("PLUGIN_ROOT", None)
                else:
                    os.environ["PLUGIN_ROOT"] = previous
                if previous_revision is not None:
                    os.environ["SKILLS_FACTORY_SOURCE_REVISION"] = previous_revision

    def test_packaged_payload_integrity_ignores_python_bytecode_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_root = Path(temp_dir) / "package"
            module_dir = package_root / "mcp"
            module_dir.mkdir(parents=True)
            (module_dir / "server.py").write_text("runtime source", encoding="utf-8")
            manifest = {
                "channel": "lab",
                "version": "1.38.318",
                "release_id": "1.38.318+aaaaaaaaaaaa",
                "source_revision": "a" * 40,
                "payload_content_sha256": payload_digest(package_root),
            }
            (package_root / "release-manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            cache = module_dir / "__pycache__" / "server.cpython-312.pyc"
            cache.parent.mkdir()
            cache.write_bytes(b"interpreter-generated bytecode")

            previous = os.environ.get("PLUGIN_ROOT")
            os.environ["PLUGIN_ROOT"] = str(package_root)
            try:
                result = self.catalog.packaged_payload_integrity()
                self.assertEqual("verified", result["status"])
                self.assertEqual(manifest["payload_content_sha256"], result["payload_content_sha256"])
                cache.write_bytes(b"regenerated bytecode")
                self.assertEqual("verified", self.catalog.packaged_payload_integrity()["status"])
            finally:
                if previous is None:
                    os.environ.pop("PLUGIN_ROOT", None)
                else:
                    os.environ["PLUGIN_ROOT"] = previous

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

    def test_load_skill_returns_declared_calculator_without_executing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "calculator"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: calculator\n---\nUse `python engine.py input.json`.\n")
            code = "raise RuntimeError('must never execute during loading')\n"
            (skill / "engine.py").write_text(code)
            (skill / "unreferenced.py").write_text("not exposed")
            with patch.dict(os.environ, {"SKILLS_FACTORY_SKILLS_ROOT": str(root)}):
                result = self.catalog.load_skill("calculator")
            self.assertEqual([{"path": "engine.py", "content": code}], result["reference_files"])
            self.assertIn("host code runner", result["supporting_code_execution"])

    def test_declared_scripts_exclude_traversal_evals_and_symlink_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "example"
            (skill / "scripts").mkdir(parents=True)
            (skill / "tests").mkdir()
            outside = Path(temp_dir) / "outside.py"
            outside.write_text("private")
            (skill / "scripts" / "engine.py").write_text("public")
            (skill / "tests" / "case.py").write_text("rubric")
            (skill / "linked.py").symlink_to(outside)
            (skill / "scripts" / "linked").symlink_to(Path(temp_dir), target_is_directory=True)
            text = " ".join(f"`{path}`" for path in (
                "scripts/engine.py", "tests/case.py", "../outside.py", "linked.py",
                "scripts/linked/outside.py", "scripts/../linked.py", "missing.py",
            ))
            self.assertEqual(
                [{"path": "scripts/engine.py", "content": "public"}],
                self.catalog._declared_script_sources(skill, text),
            )

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
