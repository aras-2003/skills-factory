"""Contract checks for compact, source-bound SDLC child handoffs."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "engineering" / "delegation_handoff.py"
SPEC = importlib.util.spec_from_file_location("delegation_handoff", MODULE_PATH)
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


def valid_input():
    return {
        "issue_id": 748,
        "role": "sf-test-executor",
        "objective": "Run the agreed static contract checks.",
        "acceptance_criteria": ["1. AC-D07: report exact command and outcome"],
        "source_base_sha": "a" * 40,
        "candidate_sha": "b" * 40,
        "architecture_impact": "A1",
        "readonly_paths": ["AGENTS.md", "tests/test_codex_agent_team.py"],
        "writable_paths": [],
        "dependencies": [724],
        "selected_skill_refs": [],
        "tool_profile_ref": "#765:TOOL-01",
        "test_case_ids": ["AGENT-01", "HANDOFF-01"],
        "stop_conditions": ["candidate SHA mismatch"],
        "context_budget": 2400,
        "output_contract_version": "1",
    }


class DelegationHandoffTests(unittest.TestCase):
    def test_handoff_01_requires_bounded_input_fields_and_references(self):
        payload = valid_input()
        encoded = handoff.serialize_input(payload)
        decoded = handoff.read_input(encoded)
        self.assertEqual(decoded, payload)
        self.assertLessEqual(len(encoded), handoff.MAX_HANDOFF_BYTES)

    def test_handoff_02_round_trip_does_not_require_parent_transcript(self):
        encoded = handoff.serialize_input(valid_input())
        resumed = handoff.read_input(encoded)
        self.assertEqual(resumed["source_base_sha"], "a" * 40)
        self.assertNotIn("transcript", resumed)

    def test_handoff_03_rejects_stale_candidate(self):
        result = {
            "task_id": "task-1", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "AGENT-01", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["tests/test_codex_agent_team.py"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        with self.assertRaisesRegex(ValueError, "candidate SHA mismatch"):
            handoff.validate_result(result, expected_candidate_sha="c" * 40)

    def test_handoff_04_rejects_private_or_authority_transfer_fields(self):
        for field in ("transcript", "tool_logs", "rubric", "held_out_fixtures", "permissions", "approval"):
            with self.subTest(field=field):
                payload = valid_input()
                payload[field] = "must not cross the handoff"
                with self.assertRaisesRegex(ValueError, "forbidden field"):
                    handoff.serialize_input(payload)

    def test_handoff_05_missing_usage_is_unknown_not_zero(self):
        result = {
            "task_id": "task-2", "role": "sf-test-executor", "status": "NOT_RUN",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [], "command_exit_codes": [], "evidence_refs": [],
            "material_findings": [], "residual_risks": ["host execution unavailable"],
            "next_action": "run in supported host",
        }
        checked = handoff.validate_result(result, expected_candidate_sha="b" * 40)
        self.assertIsNone(checked["usage"])
        self.assertEqual(checked["status"], "NOT_RUN")

    def test_handoff_06_rejects_nested_private_fields(self):
        result = {
            "task_id": "task-3", "role": "sf-test-executor", "status": "FAIL",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{
                "case_id": "AGENT-01", "status": "FAIL",
                "rubric": "private evaluator content",
            }],
            "command_exit_codes": [], "evidence_refs": [],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        with self.assertRaisesRegex(ValueError, "forbidden field: rubric"):
            handoff.validate_result(result, expected_candidate_sha="b" * 40)

    def test_handoff_07_rejects_arbitrary_nested_payload_fields(self):
        result = {
            "task_id": "task-4", "role": "sf-test-executor", "status": "FAIL",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{
                "case_id": "AGENT-01", "status": "FAIL", "prompt": "private prompt",
            }],
            "command_exit_codes": [{
                "command": "python -m unittest", "exit_code": 1,
                "output": "raw tool output",
            }],
            "evidence_refs": [], "material_findings": [], "residual_risks": [],
            "next_action": "review",
        }
        with self.assertRaisesRegex(ValueError, "unknown fields: prompt"):
            handoff.validate_result(result, expected_candidate_sha="b" * 40)

    def test_handoff_08_restricts_architecture_impact_to_native_values(self):
        payload = valid_input()
        payload["architecture_impact"] = "banana"
        with self.assertRaisesRegex(ValueError, "architecture_impact must be A0-A4 or UNKNOWN"):
            handoff.serialize_input(payload)

        payload["architecture_impact"] = "UNKNOWN"
        self.assertEqual(handoff.read_input(handoff.serialize_input(payload))["architecture_impact"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
