import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "skills/web-design/references/ui-ux-pro-max-adapter.json"
RECEIPT_PATH = ROOT / "docs/testing/evidence/ui-ux-pro-max-adapter-2026-10-26/receipt.json"


class UIUXProMaxAdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_upstream_is_pinned_to_reviewed_source_and_license(self):
        upstream = self.contract["upstream"]
        self.assertEqual(upstream["repository"], "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill")
        self.assertEqual(upstream["reviewed_commit"], "28b3b8dee8c976df4fa3e94aed4e092ad43fcb03")
        self.assertEqual(upstream["declared_skill_version"], "2.15.0")
        self.assertEqual(upstream["license"], "MIT")
        self.assertIn(upstream["reviewed_commit"], upstream["license_file"])

    def test_release_tag_and_cli_version_drift_are_explicit(self):
        upstream = self.contract["upstream"]
        self.assertEqual(upstream["latest_release_tag"], "v2.15.0")
        self.assertEqual(upstream["release_skill_version"], "2.13.0")
        self.assertEqual(upstream["cli_package_name"], "ui-ux-pro-max-cli")
        self.assertEqual(upstream["cli_package_version"], "2.5.0")
        self.assertEqual(upstream["cli_runtime_dependencies"], ["chalk", "commander", "ora", "prompts"])
        self.assertNotEqual(upstream["declared_skill_version"], upstream["release_skill_version"])

    def test_upstream_code_and_data_are_not_runtime_dependencies(self):
        decision = self.contract["decision"]
        runtime = self.contract["runtime"]
        self.assertEqual(decision["mode"], "reference_only")
        self.assertFalse(decision["copy_upstream_data"])
        self.assertFalse(decision["execute_upstream_code"])
        self.assertFalse(decision["install_upstream_cli"])
        self.assertFalse(decision["automatic_update"])
        self.assertFalse(runtime["network_required"])
        self.assertEqual(runtime["third_party_dependencies"], [])
        self.assertFalse(runtime["production_allowlist_change"])

    def test_optional_provider_has_an_offline_fallback(self):
        provider = self.contract["optional_provider"]
        self.assertEqual(provider["id"], "21st-dev-mcp")
        self.assertFalse(provider["required"])
        self.assertFalse(provider["network_required"])
        self.assertTrue(provider["unavailable_fallback"])
        self.assertEqual(provider["provider_output_trust"], "untrusted_reference")

    def test_local_design_decisions_remain_authoritative(self):
        authority = self.contract["authority"]
        self.assertEqual(authority["design_tokens"], "skills-factory-project-or-user")
        self.assertEqual(authority["accessibility_and_product_constraints"], "skills-factory-project-or-user")

    def test_evidence_receipt_records_static_package_and_runtime_scope(self):
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(receipt["issue"], 422)
        self.assertEqual(receipt["checks"]["adapter_contract_unit_tests"]["state"], "PASS")
        self.assertEqual(receipt["checks"]["repository_validate_all"]["state"], "PASS")
        self.assertEqual(receipt["checks"]["skill_security_scan"]["findings"], 0)
        self.assertEqual(receipt["checks"]["production_plugin_package"]["state"], "PASS")
        self.assertEqual(receipt["runtime_behavior"]["state"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
