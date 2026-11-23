from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/investing/build_capability_inventory.py"
SPEC = importlib.util.spec_from_file_location("build_capability_inventory", MODULE_PATH)
assert SPEC and SPEC.loader
inventory_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_mod)


class CapabilityInventoryTests(unittest.TestCase):
    def make_root(self, temp: Path):
        root = temp
        skill_source = "skills/investing/demo/SKILL.md"
        workflow_source = "workflows/investment-demo/WORKFLOW.md"
        skill = """---
name: demo
description: demo
metadata:
  version: '0.1.0'
  maturity: candidate
---
Skill text.
"""
        workflow = "# Demo workflow\n"
        (root / skill_source).parent.mkdir(parents=True)
        (root / skill_source).write_text(skill, encoding="utf-8")
        (root / workflow_source).parent.mkdir(parents=True)
        (root / workflow_source).write_text(workflow, encoding="utf-8")
        skill_sha = hashlib.sha256(skill.encode()).hexdigest()
        workflow_sha = hashlib.sha256(workflow.encode()).hexdigest()
        records = {"records": [
            {"kind": "skill", "name": "demo", "source": skill_source, "source_sha256": skill_sha, "classification": "OWN"},
            {"kind": "workflow", "name": "investment-demo", "source": workflow_source, "source_sha256": workflow_sha, "classification": "OWN"},
        ]}
        (root / "provenance").mkdir()
        (root / "provenance/registry.yaml").write_text(yaml.safe_dump(records), encoding="utf-8")
        (root / "workflows").mkdir(exist_ok=True)
        registry = {"workflows": [{
            "name": "investment-demo",
            "workflow": workflow_source,
            "metadata": {"version": "0.2.0", "maturity": "production"},
            "channels": {"plugin": "supported", "lab": "supported", "chatgpt-zip": "unavailable"},
        }]}
        (root / "workflows/runtime-registry.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")
        return root

    def test_source_metadata_and_workflow_channels_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(Path(tmp))
            result = inventory_mod.collect_inventory(root, "f" * 40)
        self.assertEqual(1, result["skill_count"])
        self.assertEqual(1, result["workflow_count"])
        self.assertEqual("0.1.0", result["skills"][0]["version"])
        self.assertEqual("NOT_DECLARED_PER_SKILL", result["skills"][0]["declared_channels"])
        self.assertEqual("supported", result["workflows"][0]["declared_channels"]["lab"])
        rendered = inventory_mod.render_markdown(result)
        self.assertIn("NOT_OBSERVED", rendered)
        self.assertIn("chatgpt-zip=unavailable", rendered)

    def test_stale_source_hash_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(Path(tmp))
            path = root / "provenance/registry.yaml"
            rows = yaml.safe_load(path.read_text(encoding="utf-8"))
            rows["records"][0]["source_sha256"] = "0" * 64
            path.write_text(yaml.safe_dump(rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale provenance SHA-256"):
                inventory_mod.collect_inventory(root, "f" * 40)

    def test_duplicate_workflow_name_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(Path(tmp))
            path = root / "workflows/runtime-registry.yaml"
            registry = yaml.safe_load(path.read_text(encoding="utf-8"))
            registry["workflows"].append(registry["workflows"][0])
            path.write_text(yaml.safe_dump(registry), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate Investment workflow"):
                inventory_mod.collect_inventory(root, "f" * 40)

    def test_invalid_source_revision_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(Path(tmp))
            with self.assertRaisesRegex(ValueError, "full 40-character"):
                inventory_mod.collect_inventory(root, "main")


    def test_baseline_snapshot_matches_all_source_metadata(self):
        source_sha = "f9dc31cdd35a323cf30006c8a91a2a48af281188"
        inventory = inventory_mod.collect_inventory(ROOT, source_sha)
        self.assertEqual(15, inventory["skill_count"])
        self.assertEqual(7, inventory["workflow_count"])
        expected = (ROOT / "docs/investing/capability-source-inventory.generated.md").read_text(encoding="utf-8")
        self.assertEqual(expected, inventory_mod.render_markdown(inventory))


if __name__ == "__main__":
    unittest.main()
