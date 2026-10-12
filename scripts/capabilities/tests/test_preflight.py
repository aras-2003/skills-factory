from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/capabilities"))
from contract import load_contract  # noqa: E402
from preflight import preflight  # noqa: E402


class CapabilityPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = load_contract(ROOT)

    def configured(self, requirements: dict[str, str]) -> dict:
        contract = dict(self.base)
        contract["component_declarations"] = {
            "fixture": {"requirements": requirements, "review_state": "STATIC_PARTIAL"}
        }
        return contract

    @staticmethod
    def requirements(**overrides: str) -> dict[str, str]:
        base = {
            "network": "none", "filesystem": "none", "shell_exec": "none",
            "credentials": "none", "external_actions": "none",
        }
        base.update(overrides)
        return base

    def test_missing_host_capability_blocks_before_dispatch(self) -> None:
        contract = self.configured(self.requirements(network="read"))
        outcome = preflight(contract, "fixture", {"network": "unavailable"})
        self.assertEqual("BLOCKED_UNAVAILABLE", outcome["decision"])
        self.assertEqual(["network"], outcome["unavailable"])
        self.assertFalse(outcome["execution_authorized"])
        self.assertFalse(outcome["provider_calls_executed"])

    def test_unknown_source_requirement_is_not_none_or_supported(self) -> None:
        contract = self.configured(self.requirements(network="unassessed"))
        outcome = preflight(contract, "fixture", {"network": "supported"})
        self.assertEqual("BLOCKED_UNVERIFIED", outcome["decision"])
        self.assertEqual("NOT_RUN", outcome["runtime_evidence"])
        self.assertIn("network:unassessed", outcome["unresolved"])

    def test_unknown_channel_does_not_claim_tool_support(self) -> None:
        contract = self.configured(self.requirements(network="read"))
        outcome = preflight(contract, "fixture", {})
        self.assertEqual("BLOCKED_UNVERIFIED", outcome["decision"])
        self.assertIn("network:availability_unknown", outcome["unresolved"])

    def test_write_request_requires_approval_even_when_host_supports_write(self) -> None:
        contract = self.configured(
            self.requirements(network="write", external_actions="approval_required")
        )
        outcome = preflight(contract, "fixture", {
            "network": "supported", "external_actions": "supported"
        })
        self.assertEqual("REQUIRES_APPROVAL", outcome["decision"])
        self.assertEqual(["external_actions", "network"], outcome["approval_gates"])
        self.assertFalse(outcome["execution_authorized"])

    def test_credential_class_must_be_verified_at_runtime(self) -> None:
        contract = self.configured(self.requirements(credentials="named_classes"))
        outcome = preflight(contract, "fixture", {"credentials": "supported"})
        self.assertEqual("BLOCKED_UNVERIFIED", outcome["decision"])
        self.assertIn("credentials:credential_classes_not_verified", outcome["unresolved"])

    def test_supported_read_only_is_not_runtime_proof(self) -> None:
        contract = self.configured(self.requirements(network="read"))
        outcome = preflight(contract, "fixture", {"network": "supported"})
        self.assertEqual("STATIC_CAPABILITY_MATCH_ONLY", outcome["decision"])
        self.assertFalse(outcome["execution_authorized"])
        self.assertEqual("NOT_RUN", outcome["runtime_evidence"])

    def test_invalid_host_state_fails_closed(self) -> None:
        contract = self.configured(self.requirements(network="read"))
        with self.assertRaises(ValueError):
            preflight(contract, "fixture", {"network": "magically-enabled"})
        with self.assertRaises(ValueError):
            preflight(contract, "fixture", {"not_a_dimension": "supported"})

    def test_existing_unassessed_inventory_is_never_auto_green(self) -> None:
        outcome = preflight(self.base, "investment-record-store", {
            "network": "supported", "external_actions": "supported",
        })
        self.assertEqual("BLOCKED_UNVERIFIED", outcome["decision"])
        self.assertFalse(outcome["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
