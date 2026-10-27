from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "scripts/catalog/validate_runtime_registry_parity.py"
spec = importlib.util.spec_from_file_location("validate_runtime_registry_parity", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


class RegistryParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = yaml.safe_load((ROOT / "workflows/runtime-registry.yaml").read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))
        cls.contract = yaml.safe_load((ROOT / "release/capability-contract.yaml").read_text(encoding="utf-8"))

    def check(self, *, catalog=None, registry=None, contract=None):
        return mod.assess(ROOT, registry=registry if registry is not None else copy.deepcopy(self.registry),
                          catalog=catalog if catalog is not None else copy.deepcopy(self.catalog),
                          contract=contract if contract is not None else copy.deepcopy(self.contract))

    def test_current_sources_have_static_parity_only(self):
        report = self.check()
        self.assertEqual("SOURCE_PARITY_ONLY_REVIEW_REQUIRED", report["status"], report["errors"])
        self.assertEqual(19, report["workflow_count"])
        self.assertEqual(len(self.catalog["skills"]), report["skill_count"])
        self.assertEqual("NOT_OBSERVED", report["runtime_installation"])
        self.assertFalse(report["release_approved"])

    def test_missing_workflow_is_detected(self):
        cat = copy.deepcopy(self.catalog)
        cat["workflows"].pop()
        result = self.check(catalog=cat)
        self.assertEqual("BLOCKED", result["status"])
        self.assertTrue(any("workflow mismatch" in x for x in result["errors"]))

    def test_duplicate_catalog_workflow_is_detected(self):
        cat = copy.deepcopy(self.catalog)
        cat["workflows"].append(copy.deepcopy(cat["workflows"][0]))
        self.assertEqual("BLOCKED", self.check(catalog=cat)["status"])

    def test_channel_availability_drift_is_detected(self):
        cat = copy.deepcopy(self.catalog)
        cat["workflows"][0]["declared_channels"]["lab"] = "unavailable"
        result = self.check(catalog=cat)
        self.assertEqual("BLOCKED", result["status"])
        self.assertTrue(any("declared_channels" in x for x in result["errors"]))

    def test_unassessed_is_not_ready(self):
        cat = copy.deepcopy(self.catalog)
        cat["workflows"][0]["capability_assessment"] = "DECLARED"
        self.assertEqual("BLOCKED", self.check(catalog=cat)["status"])

    def test_source_inventory_gap_blocks(self):
        cat = copy.deepcopy(self.catalog)
        cat["skills"].pop()
        self.assertEqual("BLOCKED", self.check(catalog=cat)["status"])

    def test_no_installed_claim_allowed(self):
        cat = copy.deepcopy(self.catalog)
        cat["metadata"]["runtime_installation"] = "verified"
        self.assertEqual("BLOCKED", self.check(catalog=cat)["status"])


if __name__ == "__main__":
    unittest.main()
