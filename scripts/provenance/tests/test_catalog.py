from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from scripts.provenance.catalog import (
    discover_sources,
    migrate_registry,
    projection,
    registry_digest,
    registry_errors,
)


ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "scripts/validate/schemas/provenance-registry.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
HASH = "a" * 64


def record(classification: str) -> dict:
    base = {
        "kind": "skill",
        "name": "sample",
        "source": "skills/demo/sample/SKILL.md",
        "source_sha256": HASH,
        "classification": classification,
        "upstream": None,
        "components": [],
        "dependencies": [],
        "basis_evidence": [],
        "local_modifications": {"status": "UNKNOWN", "items": []},
        "license": {"status": "UNKNOWN", "spdx_id": None, "attribution": []},
        "update_policy": "MANUAL_REVIEW",
        "verification": {"state": "NOT_CLASSIFIED", "reviewed_at": None, "owner": "demo-owner"},
    }
    if classification == "OWN":
        base.update({
            "basis_evidence": ["docs/source-review.md"],
            "local_modifications": {"status": "NONE", "items": []},
        })
        base["verification"] = {"state": "VERIFIED", "reviewed_at": "2026-11-13", "owner": "demo-owner"}
    elif classification == "IMPORTED":
        base["upstream"] = {
            "provider": "demo", "url": "https://example.test/skill",
            "path": "skills/sample/SKILL.md", "version": "1.0", "commit": None,
            "content_sha256": HASH, "attribution": ["Demo author"],
        }
        base["basis_evidence"] = ["docs/upstream-source-review.md"]
        base["local_modifications"] = {"status": "NONE", "items": []}
        base["verification"] = {"state": "VERIFIED", "reviewed_at": "2026-11-13", "owner": "demo-owner"}
    elif classification == "EXTENDED":
        base = record("IMPORTED")
        base["classification"] = "EXTENDED"
        base["local_modifications"] = {"status": "DOCUMENTED", "items": ["Adds a locally authored validation step"]}
    elif classification == "COMPOSED":
        base["components"] = ["skills/demo/one/SKILL.md", "skills/demo/two/SKILL.md"]
        base["basis_evidence"] = ["docs/composition-review.md"]
        base["verification"] = {"state": "VERIFIED", "reviewed_at": "2026-11-13", "owner": "demo-owner"}
    return base


class ProvenanceSchemaTests(unittest.TestCase):
    def test_four_types_unknown_and_mixed_origin_composition_fixtures_validate(self) -> None:
        for classification in ("OWN", "IMPORTED", "EXTENDED", "UNKNOWN"):
            with self.subTest(classification=classification):
                self.assertEqual([], list(VALIDATOR.iter_errors({"schema_version": 1, "records": [record(classification)]})))
        composed = record("COMPOSED")
        self.assertEqual([], list(VALIDATOR.iter_errors({"schema_version": 1, "records": [composed]})))
        own_child = record("OWN")
        own_child.update({"name": "one", "source": "skills/demo/one/SKILL.md"})
        imported_child = record("IMPORTED")
        imported_child.update({"name": "two", "source": "skills/demo/two/SKILL.md"})
        by_source = {item["source"]: item for item in (own_child, imported_child, composed)}
        children = projection(composed, by_source)["components"]
        self.assertEqual({"OWN", "IMPORTED"}, {item["classification"] for item in children})
        self.assertTrue(children[1]["upstream"] or children[0]["upstream"])

    def test_hybrid_external_base_with_local_changes_is_extended_not_own(self) -> None:
        hybrid = record("EXTENDED")
        self.assertEqual([], list(VALIDATOR.iter_errors({"schema_version": 1, "records": [hybrid]})))
        self.assertEqual("EXTENDED", hybrid["classification"])
        self.assertIsNotNone(hybrid["upstream"])
        self.assertEqual("DOCUMENTED", hybrid["local_modifications"]["status"])

    def test_invalid_claims_fail_closed(self) -> None:
        cases = []
        own_without_evidence = record("OWN")
        own_without_evidence["basis_evidence"] = []
        own_without_evidence["verification"]["state"] = "UNVERIFIED"
        cases.append(own_without_evidence)

        imported_without_immutable_hash = record("IMPORTED")
        imported_without_immutable_hash["upstream"]["content_sha256"] = "unverified"
        cases.append(imported_without_immutable_hash)

        extended_without_change_log = record("EXTENDED")
        extended_without_change_log["local_modifications"] = {"status": "UNKNOWN", "items": []}
        cases.append(extended_without_change_log)

        composed_with_one_component = record("COMPOSED")
        composed_with_one_component["components"] = ["skills/demo/one/SKILL.md"]
        cases.append(composed_with_one_component)

        unknown_claiming_upstream = record("UNKNOWN")
        unknown_claiming_upstream["upstream"] = record("IMPORTED")["upstream"]
        cases.append(unknown_claiming_upstream)

        for invalid in cases:
            with self.subTest(classification=invalid["classification"], record=invalid):
                self.assertTrue(list(VALIDATOR.iter_errors({"schema_version": 1, "records": [invalid]})))


class ProvenanceMigrationTests(unittest.TestCase):
    def create_source_tree(self, root: Path) -> None:
        skill = root / "skills" / "demo" / "sample" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(
            "---\nname: sample\ndescription: Sample skill for a migration fixture.\n"
            "metadata:\n  owner: demo-owner\n---\n\n# Sample\n",
            encoding="utf-8",
        )
        workflow = root / "workflows" / "demo-flow" / "WORKFLOW.md"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("# Demo workflow\n", encoding="utf-8")
        registry = root / "workflows" / "runtime-registry.yaml"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(
            "workflows:\n  - name: demo-flow\n    workflow: workflows/demo-flow/WORKFLOW.md\n"
            "    metadata:\n      owner: demo-owner\n",
            encoding="utf-8",
        )
        schema = root / "scripts" / "validate" / "schemas" / "provenance-registry.schema.json"
        schema.parent.mkdir(parents=True)
        schema.write_text(json.dumps(SCHEMA), encoding="utf-8")

    def test_migration_classifies_every_source_unknown_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_source_tree(root)
            first = migrate_registry(root)
            second = migrate_registry(root)
            self.assertEqual(first, second)
            self.assertEqual(2, len(discover_sources(root)))
            self.assertEqual(2, len(first["records"]))
            self.assertTrue(all(row["classification"] == "UNKNOWN" for row in first["records"]))
            self.assertTrue(all(row["verification"]["state"] == "NOT_CLASSIFIED" for row in first["records"]))
            self.assertEqual([], registry_errors(first, root))
            self.assertEqual(registry_digest(first), registry_digest(second))

    def test_changed_source_hash_requires_registry_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_source_tree(root)
            registry = migrate_registry(root)
            skill = root / "skills/demo/sample/SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
            errors = registry_errors(registry, root)
            self.assertTrue(any("stale source_sha256" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
