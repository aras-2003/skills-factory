from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys
import zipfile
import json
import subprocess
import importlib.util
import os
from unittest.mock import patch

HERE = Path(__file__).resolve()
PACKAGE_DIR = HERE.parents[1]
ROOT = HERE.parents[3]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from build_chatgpt_skills import _write_deterministic_zip
from build_plugin import copy_skill
from build_utils import atomic_output, copy_runtime_support, package_runtime_mcp, sha256_file, validate_output_path


class BuildIntegrityTests(unittest.TestCase):
    def test_strategy_calculators_survive_packaging_and_host_loading(self) -> None:
        spec = importlib.util.spec_from_file_location("source_catalog", ROOT / "runtime/mcp/skill_catalog.py")
        catalog = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(catalog)
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            for name in ("financial-modeling", "market-economics", "strategy-economics", "value-realization"):
                source = ROOT / "skills/strategy-ea" / name
                copy_skill(source, output)
                with patch.dict(os.environ, {"SKILLS_FACTORY_SKILLS_ROOT": str(output)}):
                    loaded = catalog.load_skill(name)
                references = {item["path"]: item["content"] for item in loaded["reference_files"]}
                self.assertEqual((source / "engine.py").read_text(), references.get("engine.py"), name)
                self.assertFalse(any("tests" in Path(path).parts or "evals" in Path(path).parts for path in references))

    def test_site_reference_sync_preserves_declared_scripts_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / "lab/skills/sample"
            skill.mkdir(parents=True)
            lib = root / "site/lib"
            lib.mkdir(parents=True)
            source = "raise RuntimeError('must not execute')\n"
            (skill / "engine.py").write_text(source)
            target = lib / "skill-catalog.ts"
            command = ["node", str(ROOT / "adapters/skills-factory-cloud-next/scripts/sync-lab-references.mjs"), str(root / "lab"), str(root / "site")]

            def generate(relative: str = "engine.py", content: str = source) -> None:
                target.write_text("export const SKILL_CATALOG = " + json.dumps([{
                    "name": "sample", "reference_files": {relative: content},
                }]) + " as const;\n")

            generate()
            subprocess.run(command, check=True, capture_output=True)
            self.assertIn(json.dumps(source), target.read_text())
            generate(content="tampered")
            self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
            for relative in ("../engine.py", "scripts/tests/engine.py", "/engine.py"):
                generate(relative)
                self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
            (skill / "engine.py").unlink()
            (root / "outside.py").write_text(source)
            (skill / "engine.py").symlink_to(root / "outside.py")
            generate()
            self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)

    def test_explicit_root_calculator_is_packaged_as_exact_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "source", Path(td) / "output"
            source.mkdir()
            output.mkdir()
            (source / "SKILL.md").write_text("Use `python engine.py input.json` with supplied JSON.")
            code = "raise RuntimeError('loading must not execute code')\n"
            (source / "engine.py").write_text(code)
            (source / "unreferenced.py").write_text("not runtime support")
            self.assertEqual(["engine.py"], copy_runtime_support(source, output))
            self.assertEqual(code, (output / "engine.py").read_text())
            self.assertFalse((output / "unreferenced.py").exists())

    def test_root_calculator_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            source, output = Path(td) / "source", Path(td) / "output"
            source.mkdir()
            output.mkdir()
            (source / "SKILL.md").write_text("Use `engine.py`.")
            outside = Path(td) / "outside.py"
            outside.write_text("not packaged")
            (source / "engine.py").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                copy_runtime_support(source, output)

    def test_local_mcp_configs_disable_python_bytecode_writes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stage = Path(td) / "stage"
            stage.mkdir()
            package_runtime_mcp(ROOT, stage, mode="local")
            for name in ("mcp.json", ".mcp.json"):
                config = json.loads((stage / name).read_text(encoding="utf-8"))
                server = config["mcpServers"]["skills-factory-runtime"]
                self.assertEqual("1", server["env"]["PYTHONDONTWRITEBYTECODE"])

    def test_site_catalog_generation_does_not_mutate_lab_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / "lab"
            mcp = artifact / "mcp"
            mcp.mkdir(parents=True)
            (mcp / "skill_catalog.py").write_text(
                "def entries(): return [{'name': 'sample', 'content_sha256': 'a' * 64, 'kind': 'skill', 'domain': 'sample', 'description': 'sample', 'version': '1.0.0', 'maturity': 'production'}]\n"
                "def load_skill(_name): return {'name': 'sample', 'content_sha256': 'a' * 64, 'kind': 'skill', 'domain': 'sample', 'description': 'sample', 'version': '1.0.0', 'maturity': 'production', 'instructions': 'hello', 'reference_files': [], 'execution_mode': 'host_model_executes_loaded_instructions', 'source_revision': 'b' * 40}\n"
                "def catalog_digest(): return 'c' * 64\n",
                encoding="utf-8",
            )
            (artifact / "release-manifest.json").write_text(json.dumps({
                "channel": "lab", "version": "0.37.0", "source_revision": "b" * 40,
                "release_id": "0.37.0+test", "payload_content_sha256": "d" * 64,
                "components": [{"name": "sample", "kind": "skill"}],
            }), encoding="utf-8")
            archive = root / "lab.zip"
            archive.write_bytes(b"synthetic archive")
            site = root / "site"
            (site / "lib").mkdir(parents=True)
            before = {path.relative_to(artifact).as_posix() for path in artifact.rglob("*") if path.is_file()}

            subprocess.run(
                [sys.executable, str(ROOT / "adapters/skills-factory-cloud-next/scripts/sync-lab-catalog.py"), str(artifact), str(archive), "--site-root", str(site)],
                check=True,
            )

            after = {path.relative_to(artifact).as_posix() for path in artifact.rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertFalse((mcp / "__pycache__").exists())

    def test_source_root_and_nested_source_tree_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / "skills" / "career").mkdir(parents=True)
            for unsafe in (root, root / "skills", root / "skills" / "career"):
                with self.assertRaises(ValueError):
                    validate_output_path(root, unsafe)

    def test_only_artifact_roots_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            for rel in ("plugins/pkg", "dist/zips", ".tmp/lab"):
                expected = (root / rel).resolve()
                self.assertEqual(expected, validate_output_path(root, root / rel))
            with self.assertRaises(ValueError):
                validate_output_path(root, root / "docs" / "generated")

    def test_symlink_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            source = root / "skills" / "career"
            source.mkdir(parents=True)
            plugins = root / "plugins"
            plugins.mkdir()
            link = plugins / "escape"
            link.symlink_to(source, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_output_path(root, link / "artifact")

    def test_output_outside_repo_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(ValueError):
                validate_output_path(Path(td), Path(outside) / "artifact")

    def test_failed_build_preserves_previous_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            out = root / "dist" / "artifact"
            out.mkdir(parents=True)
            (out / "known.txt").write_text("good", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                with atomic_output(root, out) as stage:
                    (stage / "broken.txt").write_text("broken", encoding="utf-8")
                    raise RuntimeError("synthetic failure")
            self.assertEqual("good", (out / "known.txt").read_text(encoding="utf-8"))
            self.assertFalse((out / "broken.txt").exists())

    def test_deterministic_zip_ignores_source_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            src.mkdir()
            f = src / "SKILL.md"
            f.write_text("same bytes\n", encoding="utf-8")
            zip1 = root / "a.zip"
            zip2 = root / "b.zip"
            _write_deterministic_zip(src, zip1, "skill")
            f.touch()
            _write_deterministic_zip(src, zip2, "skill")
            self.assertEqual(sha256_file(zip1), sha256_file(zip2))
            self.assertEqual(zip1.read_bytes(), zip2.read_bytes())

    def test_content_change_changes_zip_digest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            src.mkdir()
            f = src / "SKILL.md"
            f.write_text("one\n", encoding="utf-8")
            zip1 = root / "a.zip"
            zip2 = root / "b.zip"
            _write_deterministic_zip(src, zip1, "skill")
            f.write_text("two\n", encoding="utf-8")
            _write_deterministic_zip(src, zip2, "skill")
            self.assertNotEqual(sha256_file(zip1), sha256_file(zip2))

    def test_zip_permissions_and_timestamp_are_fixed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            src.mkdir()
            (src / "SKILL.md").write_text("x", encoding="utf-8")
            zp = root / "a.zip"
            _write_deterministic_zip(src, zp, "skill")
            with zipfile.ZipFile(zp) as zf:
                info = zf.infolist()[0]
                self.assertEqual((1980, 1, 1, 0, 0, 0), info.date_time)
                self.assertEqual(0o100644, info.external_attr >> 16)


if __name__ == "__main__":
    unittest.main()
