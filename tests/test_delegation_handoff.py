"""Contract checks for compact, source-bound SDLC child handoffs."""

import importlib.util
import json
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
    def validate_result(self, result, *, expected_task_id, expected_role,
                        expected_test_case_ids, expected_candidate_sha="b" * 40):
        return handoff.validate_result(
            result,
            expected_task_id=expected_task_id,
            expected_role=expected_role,
            expected_test_case_ids=expected_test_case_ids,
            expected_candidate_sha=expected_candidate_sha,
        )

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
            self.validate_result(result, expected_candidate_sha="c" * 40,
                                 expected_task_id="task-1", expected_role="sf-test-executor",
                                 expected_test_case_ids=["AGENT-01"])

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
            "test_case_outcomes": [{"case_id": "HANDOFF-05", "status": "NOT_RUN"}],
            "command_exit_codes": [], "evidence_refs": [],
            "material_findings": [], "residual_risks": ["host execution unavailable"],
            "next_action": "run in supported host",
        }
        checked = self.validate_result(result, expected_task_id="task-2", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-05"])
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
            self.validate_result(result, expected_task_id="task-3", expected_role="sf-test-executor",
                                 expected_test_case_ids=["AGENT-01"])

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
            self.validate_result(result, expected_task_id="task-4", expected_role="sf-test-executor",
                                 expected_test_case_ids=["AGENT-01"])

    def test_handoff_08_restricts_architecture_impact_to_native_values(self):
        payload = valid_input()
        payload["architecture_impact"] = "banana"
        with self.assertRaisesRegex(ValueError, "architecture_impact must be A0-A4 or UNKNOWN"):
            handoff.serialize_input(payload)

        payload["architecture_impact"] = "UNKNOWN"
        self.assertEqual(handoff.read_input(handoff.serialize_input(payload))["architecture_impact"], "UNKNOWN")

    def test_handoff_09_rejects_duplicate_requested_case_ids(self):
        payload = valid_input()
        payload["test_case_ids"] = ["HANDOFF-09", "HANDOFF-09"]
        with self.assertRaisesRegex(ValueError, "test_case_ids must contain unique case IDs"):
            handoff.serialize_input(payload)
        with self.assertRaisesRegex(ValueError, "test_case_ids must contain unique case IDs"):
            handoff.read_input(json.dumps(payload))

        payload["test_case_ids"] = ["HANDOFF-09", "HANDOFF-10"]
        decoded = handoff.read_input(handoff.serialize_input(payload))
        self.assertEqual(decoded["test_case_ids"], payload["test_case_ids"])
        payload["test_case_ids"] = []
        with self.assertRaisesRegex(ValueError, "requires at least one test_case_id"):
            handoff.serialize_input(payload)

    def test_handoff_10_rejects_duplicate_result_case_ids(self):
        for statuses in (("PASS", "PASS"), ("PASS", "FAIL")):
            with self.subTest(statuses=statuses):
                result = {
                    "task_id": "task-10", "role": "sf-test-executor", "status": "FAIL",
                    "candidate_sha": "b" * 40, "changed_paths": [],
                    "test_case_outcomes": [
                        {"case_id": "HANDOFF-10", "status": statuses[0]},
                        {"case_id": "HANDOFF-10", "status": statuses[1]},
                    ],
                    "command_exit_codes": [], "evidence_refs": [],
                    "material_findings": [], "residual_risks": [], "next_action": "review",
                }
                with self.assertRaisesRegex(ValueError, "test_case_outcomes must contain unique case IDs"):
                    self.validate_result(result, expected_task_id="task-10", expected_role="sf-test-executor",
                                         expected_test_case_ids=["HANDOFF-10"])

        unique_result = {
            "task_id": "task-10", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "HANDOFF-10", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["receipt://run/10"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        checked = self.validate_result(unique_result, expected_task_id="task-10", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-10"])
        self.assertEqual([row["case_id"] for row in checked["test_case_outcomes"]], ["HANDOFF-10"])

    def test_handoff_11_binds_result_to_delegated_task_role_and_case_set(self):
        result = {
            "task_id": "task-11", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [
                {"case_id": "HANDOFF-11A", "status": "PASS"},
                {"case_id": "HANDOFF-11B", "status": "PASS"},
            ],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["receipt://run/11"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        checked = self.validate_result(result, expected_task_id="task-11", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-11A", "HANDOFF-11B"])
        self.assertEqual(checked["status"], "PASS")
        reordered = self.validate_result(result, expected_task_id="task-11", expected_role="sf-test-executor",
                                         expected_test_case_ids=["HANDOFF-11B", "HANDOFF-11A"])
        self.assertEqual(reordered["status"], "PASS")
        with self.assertRaisesRegex(ValueError, "task ID mismatch"):
            self.validate_result(result, expected_task_id="task-other", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-11A", "HANDOFF-11B"])
        with self.assertRaisesRegex(ValueError, "role mismatch"):
            self.validate_result(result, expected_task_id="task-11", expected_role="sf-independent-reviewer",
                                 expected_test_case_ids=["HANDOFF-11A", "HANDOFF-11B"])
        with self.assertRaisesRegex(ValueError, "test case IDs do not match"):
            self.validate_result(result, expected_task_id="task-11", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-11A"])
        with self.assertRaisesRegex(ValueError, "unique case IDs"):
            self.validate_result(result, expected_task_id="task-11", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-11A", "HANDOFF-11A"])

    def test_handoff_12_rejects_unsupported_pass_claims(self):
        result = {
            "task_id": "task-12", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "HANDOFF-12", "status": "FAIL"}],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 1}],
            "evidence_refs": [], "material_findings": [], "residual_risks": [],
            "next_action": "fix",
        }
        with self.assertRaisesRegex(ValueError, "PASS requires at least one evidence"):
            self.validate_result(result, expected_task_id="task-12", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-12"])
        result["evidence_refs"] = ["receipt://run/12"]
        with self.assertRaisesRegex(ValueError, "non-PASS test case"):
            self.validate_result(result, expected_task_id="task-12", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-12"])
        result["test_case_outcomes"][0]["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "nonzero command exit"):
            self.validate_result(result, expected_task_id="task-12", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-12"])

    def test_handoff_13_requires_executor_command_for_case_pass_and_maps_blocked_cases(self):
        result = {
            "task_id": "task-13", "role": "sf-test-executor", "status": "BLOCKED",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [
                {"case_id": "HANDOFF-13A", "status": "PASS"},
                {"case_id": "HANDOFF-13B", "status": "BLOCKED"},
            ],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 2}],
            "evidence_refs": ["receipt://run/13"], "material_findings": [],
            "residual_risks": ["one required case was blocked"], "next_action": "retry blocked case",
        }
        checked = self.validate_result(result, expected_task_id="task-13", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-13A", "HANDOFF-13B"])
        self.assertEqual(checked["status"], "BLOCKED")
        result["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "non-PASS test case"):
            self.validate_result(result, expected_task_id="task-13", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-13A", "HANDOFF-13B"])
        result["status"] = "NOT_RUN"
        result["test_case_outcomes"] = [
            {"case_id": "HANDOFF-13A", "status": "NOT_RUN"},
            {"case_id": "HANDOFF-13B", "status": "NOT_RUN"},
        ]
        checked = self.validate_result(result, expected_task_id="task-13", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-13A", "HANDOFF-13B"])
        self.assertEqual(checked["status"], "NOT_RUN")
        result["status"] = "PASS"
        result["command_exit_codes"] = []
        result["test_case_outcomes"] = [
            {"case_id": "HANDOFF-13A", "status": "PASS"},
            {"case_id": "HANDOFF-13B", "status": "PASS"},
        ]
        with self.assertRaisesRegex(ValueError, "requires at least one command exit record"):
            self.validate_result(result, expected_task_id="task-13", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-13A", "HANDOFF-13B"])


if __name__ == "__main__":
    unittest.main()
