from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
import zipfile

import yaml
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
PACKAGE_DIR = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(PACKAGE_DIR))

import artifact_validation
import build_chatgpt_skills
import build_lab_plugin
import build_plugin
from build_utils import assert_source_revision, validate_output_path
from workflow_entrypoints import dependency_availability


class PackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_revision = os.environ.get("SOURCE_REVISION")
        os.environ["SOURCE_REVISION"] = "0123456789abcdef0123456789abcdef01234567"
        (ROOT / ".tmp").mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if self.old_revision is None:
            os.environ.pop("SOURCE_REVISION", None)
        else:
            os.environ["SOURCE_REVISION"] = self.old_revision

    def test_optional_dependency_has_explicit_missing_behavior(self) -> None:
        item = {
            "name": "workflow-x",
            "dependencies": {
                "required": ["required-skill"],
                "optional": [
                    {
                        "name": "optional-skill",
                        "on_missing": "Continue in reduced scope and disclose that optional-skill did not run.",
                    }
                ],
            },
        }
        missing_required, missing_optional = dependency_availability(item, {"required-skill"})
        self.assertEqual([], missing_required)
        self.assertEqual("optional-skill", missing_optional[0]["name"])
        self.assertIn("reduced scope", missing_optional[0]["on_missing"])

    def test_required_dependency_is_detected(self) -> None:
        item = {
            "name": "workflow-x",
            "dependencies": {"required": ["required-skill"], "optional": []},
        }
        missing_required, missing_optional = dependency_availability(item, set())
        self.assertEqual(["required-skill"], missing_required)
        self.assertEqual([], missing_optional)

    def test_stale_source_revision_is_rejected(self) -> None:
        assert_source_revision("abc", "abc")
        with self.assertRaises(RuntimeError):
            assert_source_revision("abc", "def")

    def test_prebuild_failure_preserves_previous_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "plugin"
            out.mkdir()
            sentinel = out / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            original = build_plugin.ensure_source_valid
            build_plugin.ensure_source_valid = lambda _root: (_ for _ in ()).throw(ValueError("broken reference"))
            try:
                with self.assertRaisesRegex(ValueError, "broken reference"):
                    build_plugin.build(ROOT, out, "production")
            finally:
                build_plugin.ensure_source_valid = original
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_invalid_maturity_preserves_previous_plugin_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "plugin"
            out.mkdir()
            sentinel = out / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_plugin.build(ROOT, out, "does-not-exist")
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_invalid_maturity_preserves_previous_zip_output(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "zips"
            out.mkdir()
            sentinel = out / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_chatgpt_skills.build(ROOT, out, "does-not-exist")
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))

    def test_unsafe_output_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / ".git").mkdir()
            (root / "skills" / "career").mkdir(parents=True)
            for out in (root, root / ".git", root / "skills", root / "skills" / "career", Path("/")):
                with self.assertRaises(ValueError):
                    validate_output_path(root, out)

    def test_deterministic_zip_bytes(self) -> None:
        a = build_chatgpt_skills._zip_bytes([
            ("x/SKILL.md", b"hello"),
            ("x/references/a.md", b"world"),
        ])
        b = build_chatgpt_skills._zip_bytes([
            ("x/references/a.md", b"world"),
            ("x/SKILL.md", b"hello"),
        ])
        self.assertEqual(a, b)
        changed = build_chatgpt_skills._zip_bytes([
            ("x/SKILL.md", b"HELLO"),
            ("x/references/a.md", b"world"),
        ])
        self.assertNotEqual(a, changed)

    def test_plugin_runtime_allowlist_excludes_tests_and_eval_reports(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "plugin"
            build_plugin.build(ROOT, out, "production")
            skill_dirs = [p for p in (out / "skills").iterdir() if p.is_dir()]
            for skill_dir in skill_dirs:
                interface_path = skill_dir / "agents" / "openai.yaml"
                self.assertTrue(interface_path.is_file(), skill_dir.name)
                interface = yaml.safe_load(interface_path.read_text(encoding="utf-8"))
                self.assertTrue(interface["interface"]["display_name"])
                self.assertTrue(interface["interface"]["short_description"])
                icon_path = skill_dir / interface["interface"]["icon_small"]
                self.assertTrue(icon_path.is_file(), skill_dir.name)
            paths = [p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()]
            self.assertFalse(any("/tests/" in f"/{p}/" for p in paths))
            self.assertFalse(any("/evals/" in f"/{p}/" for p in paths))
            self.assertFalse(any(p.endswith(".rubric.yaml") for p in paths))
            self.assertTrue((out / "capabilities.json").is_file())
            self.assertTrue((out / "release-manifest.json").is_file())
            self.assertTrue((out / "mcp.json").is_file())
            self.assertTrue((out / ".mcp.json").is_file())
            self.assertTrue((out / "mcp" / "chart_renderer.py").is_file())
            self.assertTrue((out / "mcp" / "investment_runtime.py").is_file())
            self.assertTrue((out / "mcp" / "server.py").is_file())

            plugin_manifest = json.loads((out / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(
                "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
                plugin_manifest["$schema"],
            )
            portable_mcp = json.loads((out / "mcp.json").read_text(encoding="utf-8"))
            self.assertEqual({"skills-factory-runtime"}, set(portable_mcp["mcpServers"]))
            self.assertEqual("stdio", portable_mcp["mcpServers"]["skills-factory-runtime"]["type"])

            compat_manifest = json.loads((out / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual("./.mcp.json", compat_manifest["mcpServers"])

            capabilities = json.loads((out / "capabilities.json").read_text(encoding="utf-8"))
            self.assertEqual("repository-side-v1", capabilities["capability_contract"]["contract_id"])
            production_skill = next(x for x in capabilities["capabilities"] if x.get("kind") == "skill")
            self.assertEqual("UNASSESSED", production_skill["capability_assessment"]["status"])
            self.assertIn("unassessed", production_skill["capability_assessment"]["requirements"].values())
            release = json.loads((out / "release-manifest.json").read_text(encoding="utf-8"))
            release_skill = next(x for x in release["components"] if x.get("kind") == "skill")
            self.assertEqual(production_skill["capability_assessment"], release_skill["capability_assessment"])
            runtime_tools = {item["name"]: item for item in capabilities["runtime_tools"]}
            self.assertEqual({"skills-factory-runtime"}, set(runtime_tools))
            runtime = runtime_tools["skills-factory-runtime"]
            self.assertEqual("skills-factory-runtime", runtime["runtime_class"])
            self.assertEqual(
                [
                    "runtime_info",
                    "list_skills",
                    "load_skill",
                    "route_investment_request",
                    "render_bar_chart",
                    "render_line_chart",
                ],
                runtime["tools"],
            )

    def test_skills_only_profile_has_no_local_mcp_dependency(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "chat-mobile"
            build_plugin.build(ROOT, out, "production", runtime_mode="skills-only")
            self.assertFalse((out / "mcp.json").exists())
            self.assertFalse((out / ".mcp.json").exists())
            self.assertFalse((out / "mcp").exists())
            manifest = json.loads((out / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertNotIn("mcpServers", manifest)
            capabilities = json.loads((out / "capabilities.json").read_text(encoding="utf-8"))
            self.assertEqual("skills-only", capabilities["runtime_mode"])
            self.assertTrue(capabilities["surface_support"]["chat_mobile"])
            self.assertEqual([], capabilities["runtime_tools"])

    def test_remote_profile_uses_https_mcp_without_bundling_stdio(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "chat-web"
            build_plugin.build(
                ROOT,
                out,
                "production",
                runtime_mode="remote",
                remote_mcp_url="https://skills.example.test/mcp",
            )
            self.assertFalse((out / "mcp").exists())
            mcp = json.loads((out / "mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {"type": "http", "url": "https://skills.example.test/mcp"},
                mcp["mcpServers"]["skills-factory-runtime"],
            )
            capabilities = json.loads((out / "capabilities.json").read_text(encoding="utf-8"))
            self.assertEqual("remote", capabilities["runtime_mode"])
            self.assertFalse(capabilities["surface_support"]["chat_mobile"])

    def test_remote_profile_rejects_non_https_endpoint(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                build_plugin.build(
                    ROOT,
                    Path(td) / "chat-web",
                    "production",
                    runtime_mode="remote",
                    remote_mcp_url="http://skills.example.test/mcp",
                )

    def test_lab_manifests_match_final_fixture_mutated_artifact(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = Path(td) / "lab"
            old_argv = sys.argv
            try:
                sys.argv = ["build_lab_plugin.py", "--output", str(out.relative_to(ROOT))]
                self.assertEqual(0, build_lab_plugin.main())
            finally:
                sys.argv = old_argv

            errors = artifact_validation.validate_tree(out, allow_lab_evals=True)
            self.assertEqual([], errors)

            index_path = out / "executor-inputs.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            original_index = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
            index["cases"][0]["input_sha256"] = "0" * 64
            index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            errors = artifact_validation.validate_tree(out, allow_lab_evals=True)
            self.assertTrue(any("digest mismatch" in error for error in errors), errors)
            index["cases"][0]["input"] = "executor-inputs/../../outside.input.md"
            index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            errors = artifact_validation.validate_tree(out, allow_lab_evals=True)
            self.assertTrue(any("unsafe or duplicate input path" in error for error in errors), errors)
            index_path.write_text(original_index, encoding="utf-8")

            plugin_manifest = json.loads((out / "plugin.json").read_text(encoding="utf-8"))
            interface = plugin_manifest["extensions"]["com.openai"]["interface"]
            self.assertEqual("https://aras-2003.github.io/skills-factory/", interface["websiteURL"])
            self.assertEqual("./assets/brand-mark.svg", interface["logo"])
            self.assertEqual("./assets/brand-mark.svg", interface["composerIcon"])
            self.assertEqual("#C6812C", interface["brandColor"])
            self.assertEqual("#F0C982", interface["brandColorDark"])
            self.assertTrue((out / "assets" / "brand-mark.svg").is_file())
            compat_manifest = json.loads((out / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(interface, compat_manifest["interface"])

            capabilities = json.loads((out / "capabilities.json").read_text(encoding="utf-8"))
            self.assertEqual("repository-side-v1", capabilities["capability_contract"]["contract_id"])
            workflows = [x for x in capabilities["capabilities"] if x.get("kind") == "workflow"]
            self.assertTrue(workflows)
            self.assertTrue(all(x.get("version") for x in workflows))

            draft_targets = {"skill-test-design", "skill-evaluation", "skill-release-review"}
            draft_components = {
                x["name"]: x
                for x in capabilities["capabilities"]
                if x.get("kind") == "skill" and x.get("maturity") == "draft"
            }
            self.assertEqual(draft_targets, set(draft_components))
            self.assertTrue(all((out / "skills" / name / "SKILL.md").is_file() for name in draft_targets))

            eval_index = json.loads((out / "executor-inputs.json").read_text(encoding="utf-8"))
            self.assertEqual("1.0", eval_index["schema_version"])
            self.assertTrue(eval_index["cases"])
            self.assertTrue(all((out / item["input"]).is_file() for item in eval_index["cases"]))
            self.assertTrue(all(len(item["input_sha256"]) == 64 for item in eval_index["cases"]))
            self.assertTrue(all("rubric" not in item for item in eval_index["cases"]))
            self.assertTrue((out / "executor-inputs").is_dir())
            self.assertFalse(any((out / "skills").rglob("evals")))
            for skill_file in (out / "skills").rglob("SKILL.md"):
                text = skill_file.read_text(encoding="utf-8")
                self.assertNotIn("references/evals/", text, skill_file)
                self.assertNotIn("## Lab runtime eval inputs", text, skill_file)

            fixture_component = next(
                x for x in capabilities["capabilities"]
                if x.get("kind") == "skill" and x["name"] in {item["target"] for item in eval_index["cases"]}
            )
            skill_md = out / "skills" / fixture_component["name"] / "SKILL.md"
            skill_md.write_text(skill_md.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
            errors = artifact_validation.validate_tree(out, allow_lab_evals=True)
            self.assertTrue(any("content_sha256 mismatch" in e for e in errors))

    def _build_zip_channel(self, parent: Path) -> Path:
        out = parent / "zips"
        build_chatgpt_skills.build(ROOT, out, "production")
        self.assertEqual([], artifact_validation.validate_zips(out))
        return out

    def test_zip_skill_content_mutation_with_unchanged_index_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = self._build_zip_channel(Path(td))
            index = json.loads((out / "index.json").read_text(encoding="utf-8"))
            item = index["skills"][0]
            zp = out / item["zip"]
            with zipfile.ZipFile(zp) as zf:
                files = [(info.filename, zf.read(info)) for info in zf.infolist()]
            skill_member = f"{item['name']}/SKILL.md"
            mutated = [
                (name, data + b"\n# mutation\n" if name == skill_member else data)
                for name, data in files
            ]
            zp.write_bytes(build_chatgpt_skills._zip_bytes(mutated))
            errors = artifact_validation.validate_zips(out)
        self.assertTrue(any("archive_sha256 mismatch" in e for e in errors), errors)
        self.assertTrue(any("content_sha256 mismatch" in e for e in errors), errors)

    def test_zip_manifest_identity_mismatches_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out = self._build_zip_channel(Path(td))
            capabilities_path = out / "capabilities.json"
            capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
            capabilities["skills"][0]["version"] = "0.0.0-mutated"
            capabilities_path.write_text(json.dumps(capabilities, indent=2) + "\n", encoding="utf-8")
            errors = artifact_validation.validate_zips(out)
            self.assertTrue(any("index/capabilities version mismatch" in e for e in errors), errors)

            build_chatgpt_skills.build(ROOT, out, "production")
            capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
            capabilities["capability_contract"]["contract_id"] = "mutated"
            capabilities_path.write_text(json.dumps(capabilities, indent=2) + "\n", encoding="utf-8")
            errors = artifact_validation.validate_zips(out)
            self.assertTrue(any("capability_contract mismatch" in e for e in errors), errors)

            build_chatgpt_skills.build(ROOT, out, "production")
            release_path = out / "release-manifest.json"
            release = json.loads(release_path.read_text(encoding="utf-8"))
            release["components"][0]["content_sha256"] = "0" * 64
            release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            errors = artifact_validation.validate_zips(out)
        self.assertTrue(any("index/release content_sha256 mismatch" in e for e in errors), errors)

    def test_duplicate_and_unsafe_zip_entries_are_rejected(self) -> None:
        duplicate_infos = [
            zipfile.ZipInfo("demo/SKILL.md"),
            zipfile.ZipInfo("demo/SKILL.md"),
        ]
        errors = artifact_validation._zip_member_errors("demo.zip", "demo", duplicate_infos)
        self.assertTrue(any("duplicate ZIP entries" in e for e in errors), errors)

        unsafe_infos = [zipfile.ZipInfo("demo/../escape.txt")]
        errors = artifact_validation._zip_member_errors("demo.zip", "demo", unsafe_infos)
        self.assertTrue(any("unsafe ZIP entry name" in e for e in errors), errors)
    def test_chatgpt_channel_manifest_declares_workflow_limitations(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            out1 = Path(td) / "zip1"
            out2 = Path(td) / "zip2"
            build_chatgpt_skills.build(ROOT, out1, "production")
            build_chatgpt_skills.build(ROOT, out2, "production")
            index1 = (out1 / "index.json").read_bytes()
            index2 = (out2 / "index.json").read_bytes()
            self.assertEqual(index1, index2)
            import json
            data = json.loads(index1)
            self.assertTrue(data["workflows"])
            self.assertTrue(all(x["status"] == "unavailable" for x in data["workflows"]))
            zips1 = sorted(p for p in out1.glob("*.zip"))
            self.assertTrue(zips1)
            with zipfile.ZipFile(zips1[0]) as archive:
                names = archive.namelist()
                agent_path = next(p for p in names if p.endswith("/agents/openai.yaml"))
                interface = yaml.safe_load(archive.read(agent_path).decode("utf-8"))
                icon_path = (Path(agent_path).parent.parent / interface["interface"]["icon_small"]).as_posix()
                self.assertIn(icon_path, names)
                self.assertIn("display_name", interface["interface"])
            for p1 in zips1:
                p2 = out2 / p1.name
                self.assertEqual(p1.read_bytes(), p2.read_bytes())


if __name__ == "__main__":
    unittest.main()
