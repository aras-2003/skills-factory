"""Contract checks for compact, source-bound SDLC child handoffs."""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


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
                        expected_test_case_ids, expected_candidate_sha="b" * 40,
                        fixture_policy_by_case=None):
        kwargs = {
            "expected_task_id": expected_task_id,
            "expected_role": expected_role,
            "expected_test_case_ids": expected_test_case_ids,
            "expected_candidate_sha": expected_candidate_sha,
        }
        kwargs["fixture_policy_by_case"] = (fixture_policy_by_case if fixture_policy_by_case is not None
                                            else {case_id: None for case_id in expected_test_case_ids})
        return handoff.validate_result(result, **kwargs)


    def _assert_rejected_by_both_inputs(self, payload):
        with self.assertRaises(ValueError):
            handoff.serialize_input(payload)
        with self.assertRaises(ValueError):
            handoff.read_input(json.dumps(payload))

    def _assert_accepted_by_both_inputs(self, payload):
        encoded = handoff.serialize_input(payload)
        self.assertEqual(payload, handoff.read_input(encoded))
        self.assertEqual(payload, handoff.read_input(json.dumps(payload)))

    def test_hbd_01_rejects_raw_wire_over_declared_budget(self):
        payload = {
            "issue_id": 748, "role": "sf-test-executor", "objective": "Run checks.",
            "acceptance_criteria": ["1. AC-D04"], "source_base_sha": "a" * 40,
            "candidate_sha": "b" * 40, "architecture_impact": "A1",
            "readonly_paths": ["AGENTS.md"], "writable_paths": [], "dependencies": [724],
            "selected_skill_refs": [], "tool_profile_ref": "#765:TOOL-01",
            "test_case_ids": ["HANDOFF-01"], "stop_conditions": ["SHA mismatch"],
            "context_budget": 600, "output_contract_version": "1",
        }
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        wire = encoded + b" " * (601 - len(encoded))
        self.assertEqual("dff39fa9d46cbcc03d23d0016040d5cfc3d88ccd0f8b8e835a766cc40c444da6",
                         hashlib.sha256(wire).hexdigest())
        for kind, data in (("bytes", wire), ("str", wire.decode("utf-8"))):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    handoff.read_input(data)

    def test_hbd_02_03_04_accept_bounded_utf8_and_formatted_input(self):
        payload = {
            "issue_id": 748, "role": "sf-test-executor", "objective": "Run checks.",
            "acceptance_criteria": ["1. AC-D04"], "source_base_sha": "a" * 40,
            "candidate_sha": "b" * 40, "architecture_impact": "A1",
            "readonly_paths": ["AGENTS.md"], "writable_paths": [], "dependencies": [724],
            "selected_skill_refs": [], "tool_profile_ref": "#765:TOOL-01",
            "test_case_ids": ["HANDOFF-01"], "stop_conditions": ["SHA mismatch"],
            "context_budget": 600, "output_contract_version": "1",
        }
        fixtures = (
            (599, "1d38ff8b9755c05d7c57999be3f73102f4e838700a776b32e74cdfe796bb3b17"),
            (600, "9271772760f6d0d3bdcd0c3329acc061f75b4512e7556cb7f5dcbd109fd6584f"),
        )
        for size, digest in fixtures:
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
            wire = raw + b" " * (size - len(raw))
            self.assertEqual(digest, hashlib.sha256(wire).hexdigest())
            for data in (wire, wire.decode("utf-8")):
                with self.subTest(case="HBD-02", size=size, kind=type(data).__name__):
                    self.assertEqual(payload, handoff.read_input(data))

        payload["objective"] = "Run café checks."
        for size, digest in (
            (600, "72694146a03891d0a3d63d472fa545a0fca9f6d176ed1608be978fe73b37816e"),
            (601, "4c29f30cc4f06bdd3bfd8f736fbf55c797aac407d187278a2ab277245595dd89"),
        ):
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
            wire = raw + b" " * (size - len(raw))
            self.assertEqual(digest, hashlib.sha256(wire).hexdigest())
            self.assertEqual(size - 1, len(wire.decode("utf-8")))
            for data in (wire, wire.decode("utf-8")):
                with self.subTest(case="HBD-03", size=size, kind=type(data).__name__):
                    if size == 600:
                        self.assertEqual(payload, handoff.read_input(data))
                    else:
                        with self.assertRaises(ValueError):
                            handoff.read_input(data)

        payload["objective"] = "Run checks."
        payload["context_budget"] = 604
        wire = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.assertEqual(604, len(wire))
        self.assertEqual("9311c6d02fa1e69a51ffd653600c5e0d97d73c1e69990ea5964b91666275d7d0",
                         hashlib.sha256(wire).hexdigest())
        for data in (wire, wire.decode("utf-8")):
            with self.subTest(case="HBD-04", kind=type(data).__name__):
                self.assertEqual(payload, handoff.read_input(data))
        self.assertEqual(payload, handoff.read_input(handoff.serialize_input(payload)))

    def test_handoff_wire_01_enforces_raw_utf8_byte_limit(self):
        payload = valid_input()
        payload["objective"] = "Run checks for café."
        payload["context_budget"] = 16_384
        formatted = json.dumps(payload, ensure_ascii=False, indent=2)
        for size in (16_384, 16_385):
            wire = formatted + " " * (size - len(formatted.encode("utf-8")))
            self.assertEqual(size, len(wire.encode("utf-8")))
            expected_digest = {
                16_384: "9ccb56b407846101e724eaeb0035ddae31aa1870b10b06576c1ba189ecb9e96e",
                16_385: "e7510f8c8576cc370b1e718f7422f780013eeab85e9f1352a3586eebfdae7002",
            }[size]
            self.assertEqual(expected_digest, hashlib.sha256(wire.encode("utf-8")).hexdigest())
            self.assertLess(len(wire), size)  # The non-ASCII character uses two bytes.
            for kind, data in (("str", wire), ("bytes", wire.encode("utf-8"))):
                with self.subTest(size=size, kind=kind):
                    if size == 16_384:
                        self.assertEqual(payload, handoff.read_input(data))
                    else:
                        with self.assertRaises(ValueError):
                            handoff.read_input(data)

    def test_handoff_wire_02_rejects_oversized_text_before_encoding(self):
        class EncodeMustNotRun(str):
            def encode(self, *args, **kwargs):
                raise AssertionError("oversized text was encoded")

        wire = EncodeMustNotRun("x" * (handoff.MAX_HANDOFF_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "byte context limit"):
            handoff.read_input(wire)

    def test_handoff_error_01_does_not_echo_unknown_input_field(self):
        sentinel = "SENTINEL_PRIVATE_7f31"
        payload = valid_input()
        payload[sentinel] = "private"
        wire = json.dumps(payload)
        for name, call in (
            ("validate_input", lambda: handoff.validate_input(payload)),
            ("read_input(str)", lambda: handoff.read_input(wire)),
            ("read_input(bytes)", lambda: handoff.read_input(wire.encode("utf-8"))),
        ):
            with self.subTest(entry_point=name):
                with self.assertRaises(ValueError) as error:
                    call()
                self.assertNotIn(sentinel, str(error.exception))

    def test_handoff_json_01_rejects_duplicate_decoded_keys(self):
        payload = valid_input()
        unique = json.dumps(payload)
        # The escaped spelling decodes to the same key as candidate_sha.
        duplicate = unique[:-1] + ', "candidate_\\u0073ha": "' + "c" * 40 + '"}'
        for kind, encode in (("str", lambda value: value),
                             ("bytes", lambda value: value.encode("utf-8"))):
            with self.subTest(kind=kind, keys="unique"):
                self.assertEqual(payload, handoff.read_input(encode(unique)))
            with self.subTest(kind=kind, keys="duplicate"):
                with self.assertRaises(ValueError):
                    handoff.read_input(encode(duplicate))

    def test_handoff_json_02_rejects_deep_wire_as_value_error(self):
        wire = '{"objective":' + "[" * 300 + "0" + "]" * 300 + "}"
        self.assertLess(len(wire.encode("utf-8")), handoff.MAX_HANDOFF_BYTES)
        original_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(250)
            for kind, data in (("str", wire), ("bytes", wire.encode("utf-8"))):
                with self.subTest(kind=kind):
                    with self.assertRaises(ValueError) as error:
                        handoff.read_input(data)
                    self.assertNotIn(wire, str(error.exception))
        finally:
            sys.setrecursionlimit(original_limit)

    def test_handoff_json_03_normalizes_decoder_recursion_error(self):
        sentinel = "SENTINEL_DECODER_RECURSION_51"
        wire = json.dumps({"objective": sentinel})
        for kind, data in (("str", wire), ("bytes", wire.encode("utf-8"))):
            with self.subTest(kind=kind):
                with patch.object(handoff.json, "loads", side_effect=RecursionError(sentinel)):
                    with self.assertRaises(ValueError) as error:
                        handoff.read_input(data)
                self.assertEqual("serialized handoff exceeds recursion limit", str(error.exception))
                self.assertNotIn(sentinel, str(error.exception))
                self.assertTrue(error.exception.__suppress_context__)

    def test_handoff_object_01_rejects_cyclic_input_as_value_error(self):
        sentinel = "SENTINEL_CYCLIC_INPUT_51"
        cyclic = [sentinel]
        cyclic.append(cyclic)
        payload = valid_input()
        payload["objective"] = cyclic
        for name, call in (("validate_input", handoff.validate_input),
                           ("serialize_input", handoff.serialize_input)):
            with self.subTest(entry_point=name):
                with self.assertRaises(ValueError) as error:
                    call(payload)
                self.assertNotIn(sentinel, str(error.exception))

    def test_handoff_object_02_rejects_cyclic_result_as_value_error(self):
        sentinel = "SENTINEL_CYCLIC_RESULT_51"
        cyclic = [sentinel]
        cyclic.append(cyclic)
        result = {
            "task_id": "task-2", "role": "sf-test-executor", "status": "NOT_RUN",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "HANDOFF-05", "status": "NOT_RUN"}],
            "command_exit_codes": [], "evidence_refs": [],
            "material_findings": cyclic, "residual_risks": ["host execution unavailable"],
            "next_action": "run in supported host",
        }
        with self.assertRaises(ValueError) as error:
            self.validate_result(result, expected_task_id="task-2", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-05"],
                                 fixture_policy_by_case={"HANDOFF-05": None})
        self.assertNotIn(sentinel, str(error.exception))

    def test_handoff_object_03_normalizes_recursive_json_serialization_error(self):
        sentinel = "SENTINEL_DEEP_SERIALIZATION_51"
        # Inject the encoder failure: some Python JSON implementations do not
        # raise RecursionError for deeply nested containers at this limit.
        with patch.object(handoff.json, "dumps", side_effect=RecursionError(sentinel)):
            with self.assertRaises(ValueError) as error:
                handoff._bounded_json({"objective": sentinel})
        self.assertNotIn(sentinel, str(error.exception))
        self.assertTrue(error.exception.__suppress_context__)

    def test_handoff_path_01_accepts_valid_and_nested_read_write_scopes(self):
        payload = valid_input()
        payload["readonly_paths"] = ["src/", "docs/guide.md"]
        payload["writable_paths"] = ["src/changed.py"]
        encoded = handoff.serialize_input(payload)
        self.assertEqual(payload, handoff.read_input(encoded))

        payload["readonly_paths"] = []
        payload["writable_paths"] = []
        self.assertEqual(payload, handoff.read_input(handoff.serialize_input(payload)))

    def test_handoff_path_02_rejects_malformed_paths_in_both_scopes(self):
        invalid = ["/tmp/x", "../x", "a/../b", "./x", "a//b", "a\\\\b", "bad\x00path"]
        for field in ("readonly_paths", "writable_paths"):
            for path in invalid:
                with self.subTest(field=field, path=path):
                    payload = valid_input()
                    payload[field] = [path]
                    self._assert_rejected_by_both_inputs(payload)

    def test_handoff_path_03_rejects_duplicate_paths_in_either_scope(self):
        for field in ("readonly_paths", "writable_paths"):
            with self.subTest(field=field):
                payload = valid_input()
                payload[field] = ["src/file.py", "src/file.py"]
                self._assert_rejected_by_both_inputs(payload)

    def test_handoff_path_04_rejects_conflicting_read_write_scopes(self):
        conflicts = [
            (["src/file.py"], ["src/file.py"]),
            (["src/"], ["src/"]),
            (["src/private.txt"], ["src/"]),
        ]
        for readonly, writable in conflicts:
            with self.subTest(readonly=readonly, writable=writable):
                payload = valid_input()
                payload["readonly_paths"] = readonly
                payload["writable_paths"] = writable
                self._assert_rejected_by_both_inputs(payload)

    def test_handoff_path_05_uses_component_boundaries_for_scopes(self):
        payload = valid_input()
        payload["readonly_paths"] = ["src/"]
        payload["writable_paths"] = ["src-old/file.py"]
        self._assert_accepted_by_both_inputs(payload)

    def test_handoff_path_06_exact_file_and_directory_scopes_are_distinct(self):
        for readonly, writable in ((["src"], ["src/"]), (["src/"], ["src"])):
            with self.subTest(readonly=readonly, writable=writable):
                payload = valid_input()
                payload["readonly_paths"] = readonly
                payload["writable_paths"] = writable
                self._assert_accepted_by_both_inputs(payload)

    def test_handoff_path_07_nested_directory_overlap_is_directional(self):
        payload = valid_input()
        payload["readonly_paths"] = ["src/a/"]
        payload["writable_paths"] = ["src/"]
        self._assert_rejected_by_both_inputs(payload)

        payload["readonly_paths"] = ["src/"]
        payload["writable_paths"] = ["src/a/"]
        self._assert_accepted_by_both_inputs(payload)

    def test_handoff_path_08_prefix_sibling_is_disjoint_from_write_directory(self):
        payload = valid_input()
        payload["readonly_paths"] = ["src-old/file.py"]
        payload["writable_paths"] = ["src/"]
        self._assert_accepted_by_both_inputs(payload)

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

    def test_handoff_03_rejects_stale_candidate_and_binds_fixture_identity(self):
        fixture_sha256 = "c" * 64
        result = {
            "task_id": "task-1", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{
                "case_id": "HANDOFF-03", "status": "PASS", "fixture_sha256": fixture_sha256,
            }],
            "command_exit_codes": [{"command": "python -m unittest", "exit_code": 0}],
            "evidence_refs": ["tests/test_codex_agent_team.py"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        expected = {"HANDOFF-03": fixture_sha256}
        with self.assertRaisesRegex(ValueError, "candidate SHA mismatch"):
            self.validate_result(result, expected_candidate_sha="c" * 40,
                                 expected_task_id="task-1", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-03"],
                                 fixture_policy_by_case=expected)

        checked = self.validate_result(result, expected_task_id="task-1", expected_role="sf-test-executor",
                                       expected_test_case_ids=["HANDOFF-03"],
                                       fixture_policy_by_case=expected)
        self.assertEqual(fixture_sha256, checked["test_case_outcomes"][0]["fixture_sha256"])

        result["test_case_outcomes"][0]["fixture_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 mismatch"):
            self.validate_result(result, expected_task_id="task-1", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-03"],
                                 fixture_policy_by_case=expected)

        del result["test_case_outcomes"][0]["fixture_sha256"]
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 is required"):
            self.validate_result(result, expected_task_id="task-1", expected_role="sf-test-executor",
                                 expected_test_case_ids=["HANDOFF-03"],
                                 fixture_policy_by_case=expected)

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
        sentinel = "SENTINEL_PRIVATE_7f31"
        result = {
            "task_id": "task-4", "role": "sf-test-executor", "status": "FAIL",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{
                "case_id": "AGENT-01", "status": "FAIL", sentinel: "private prompt",
            }],
            "command_exit_codes": [{
                "command": "python -m unittest", "exit_code": 1,
                "output": "raw tool output",
            }],
            "evidence_refs": [], "material_findings": [], "residual_risks": [],
            "next_action": "review",
        }
        with self.assertRaisesRegex(ValueError, "unknown fields") as error:
            self.validate_result(result, expected_task_id="task-4", expected_role="sf-test-executor",
                                 expected_test_case_ids=["AGENT-01"])
        self.assertNotIn(sentinel, str(error.exception))

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
        with self.assertRaisesRegex(ValueError, "requires at least one expected test case"):
            handoff.validate_result(
                result,
                expected_task_id="task-13",
                expected_role="sf-test-executor",
                expected_test_case_ids=[],
                expected_candidate_sha="b" * 40, fixture_policy_by_case={},
            )

    def test_handoff_14_binds_fixture_identity_to_trusted_dispatch(self):
        expected = {"HANDOFF-14": "c" * 64}
        result = {
            "task_id": "task-14", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "HANDOFF-14", "status": "PASS"}],
            "command_exit_codes": [{"command": "python -m unittest HANDOFF-14", "exit_code": 0}],
            "evidence_refs": ["receipt://run/14"],
            "material_findings": [], "residual_risks": [], "next_action": "review",
        }
        kwargs = dict(expected_task_id="task-14", expected_role="sf-test-executor",
                      expected_test_case_ids=["HANDOFF-14"], fixture_policy_by_case=expected)
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 is required"):
            self.validate_result(result, **kwargs)

        result["test_case_outcomes"][0]["fixture_sha256"] = "c" * 64
        checked = self.validate_result(result, **kwargs)
        self.assertEqual("c" * 64, checked["test_case_outcomes"][0]["fixture_sha256"])

        result["test_case_outcomes"][0]["fixture_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 mismatch"):
            self.validate_result(result, **kwargs)

        result["status"] = "BLOCKED"
        result["test_case_outcomes"][0] = {"case_id": "HANDOFF-14", "status": "PASS"}
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 is required"):
            self.validate_result(result, **kwargs)

        result["test_case_outcomes"][0] = {"case_id": "HANDOFF-14", "status": "NOT_RUN"}
        checked = self.validate_result(result, **kwargs)
        self.assertEqual("NOT_RUN", checked["test_case_outcomes"][0]["status"])

    def test_handoff_15_rejects_invalid_trusted_fixture_map(self):
        result = {
            "task_id": "task-15", "role": "sf-test-executor", "status": "NOT_RUN",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "HANDOFF-15", "status": "NOT_RUN"}],
            "command_exit_codes": [], "evidence_refs": [],
            "material_findings": [], "residual_risks": [], "next_action": "run",
        }
        base = dict(expected_task_id="task-15", expected_role="sf-test-executor",
                    expected_test_case_ids=["HANDOFF-15"])
        with self.assertRaisesRegex(ValueError, "exact test case IDs"):
            self.validate_result(result, **base,
                                 fixture_policy_by_case={"OTHER": "c" * 64})
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            self.validate_result(result, **base,
                                 fixture_policy_by_case={"HANDOFF-15": "C" * 64})


class FixturePolicyContractTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "task_id": "fixture-policy", "role": "sf-test-executor", "status": "PASS",
            "candidate_sha": "b" * 40, "changed_paths": [],
            "test_case_outcomes": [{"case_id": "CASE-1", "status": "PASS", "fixture_sha256": "c" * 64}],
            "command_exit_codes": [{"command": "run CASE-1", "exit_code": 0}],
            "evidence_refs": ["receipt://case-1"], "material_findings": [],
            "residual_risks": [], "next_action": "review",
        }
        self.kwargs = dict(expected_task_id="fixture-policy", expected_role="sf-test-executor",
                           expected_test_case_ids=["CASE-1"], expected_candidate_sha="b" * 40)

    def test_readonly_roles_pass_rejects_changed_paths(self):
        self.payload["changed_paths"] = ["tests/example.py"]
        for role in ("sf-test-executor", "sf-independent-reviewer"):
            with self.subTest(role=role):
                self.payload["role"] = self.kwargs["expected_role"] = role
                with self.assertRaises(ValueError):
                    handoff.validate_result(self.payload, **self.kwargs,
                                            fixture_policy_by_case={"CASE-1": "c" * 64})

    def test_readonly_roles_pass_accepts_empty_changed_paths(self):
        for role in ("sf-test-executor", "sf-independent-reviewer"):
            with self.subTest(role=role):
                self.payload["role"] = self.kwargs["expected_role"] = role
                checked = handoff.validate_result(self.payload, **self.kwargs,
                                                  fixture_policy_by_case={"CASE-1": "c" * 64})
                self.assertEqual([], checked["changed_paths"])

    def test_developer_pass_accepts_changed_paths(self):
        self.payload.update(role="sf-developer-high", changed_paths=["tests/example.py"])
        self.kwargs["expected_role"] = "sf-developer-high"
        checked = handoff.validate_result(self.payload, **self.kwargs,
                                          fixture_policy_by_case={"CASE-1": "c" * 64})
        self.assertEqual("PASS", checked["status"])
        self.assertEqual(["tests/example.py"], checked["changed_paths"])

    def test_readonly_roles_fail_accepts_changed_paths(self):
        self.payload.update(status="FAIL", changed_paths=["tests/example.py"])
        self.payload["test_case_outcomes"][0]["status"] = "FAIL"
        self.payload["command_exit_codes"][0]["exit_code"] = 1
        for role in ("sf-test-executor", "sf-independent-reviewer"):
            with self.subTest(role=role):
                self.payload["role"] = self.kwargs["expected_role"] = role
                checked = handoff.validate_result(self.payload, **self.kwargs,
                                                  fixture_policy_by_case={"CASE-1": "c" * 64})
                self.assertEqual(["tests/example.py"], checked["changed_paths"])

    def test_policy_is_required_and_covers_exact_case_set(self):
        with self.assertRaises(TypeError):
            handoff.validate_result(self.payload, **self.kwargs)
        with self.assertRaises(TypeError):
            handoff.validate_result(self.payload, **self.kwargs,
                                    expected_fixture_sha256_by_case={"CASE-1": "c" * 64})
        for policy in (None, {}, {"OTHER": "c" * 64}, {"CASE-1": "c" * 64, "OTHER": None},
                       {"CASE-1": "C" * 64}, {"CASE-1": 42}):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case=policy)

    def test_partial_multi_case_policy_rejected_for_pass_and_not_run(self):
        self.kwargs["expected_test_case_ids"] = ["CASE-1", "CASE-2"]
        self.payload["test_case_outcomes"].append({"case_id": "CASE-2", "status": "PASS"})
        for status in ("PASS", "NOT_RUN"):
            self.payload["status"] = status
            for outcome in self.payload["test_case_outcomes"]:
                outcome["status"] = status
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "exact test case IDs"):
                handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": "c" * 64})

    def test_empty_case_set_requires_explicit_empty_policy(self):
        self.payload.update(role="sf-independent-reviewer", status="NOT_RUN", test_case_outcomes=[])
        self.kwargs.update(expected_role="sf-independent-reviewer", expected_test_case_ids=[])
        self.assertEqual("NOT_RUN", handoff.validate_result(self.payload, **self.kwargs,
                                                             fixture_policy_by_case={})["status"])
        with self.assertRaises(ValueError):
            handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": None})

    def test_stale_candidate_and_changed_fixture_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "candidate SHA mismatch"):
            handoff.validate_result(self.payload, **{**self.kwargs, "expected_candidate_sha": "a" * 40},
                                    fixture_policy_by_case={"CASE-1": "c" * 64})
        with self.assertRaisesRegex(ValueError, "fixture SHA-256 mismatch"):
            handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": "d" * 64})

    def test_unbound_accepts_executed_outcomes_only_without_digest(self):
        outcome = self.payload["test_case_outcomes"][0]
        for status in ("PASS", "FAIL"):
            self.payload["status"] = status
            outcome["status"] = status
            outcome.pop("fixture_sha256", None)
            self.assertEqual(status, handoff.validate_result(
                self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": None})["status"])
            outcome["fixture_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "unbound test case"):
                handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": None})

    def test_bound_and_unbound_fixture_policy(self):
        policy = {"CASE-1": "c" * 64}
        self.assertEqual("PASS", handoff.validate_result(self.payload, **self.kwargs,
                                                          fixture_policy_by_case=policy)["status"])
        outcome = self.payload["test_case_outcomes"][0]
        for status in ("PASS", "FAIL"):
            self.payload["status"] = status
            outcome["status"] = status
            for reported in (None, "d" * 64):
                if reported is None:
                    outcome.pop("fixture_sha256", None)
                else:
                    outcome["fixture_sha256"] = reported
                with self.subTest(status=status, reported=reported), self.assertRaises(ValueError):
                    handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case=policy)
        self.payload["status"] = "FAIL"
        outcome["status"] = "FAIL"
        outcome["fixture_sha256"] = "c" * 64
        self.assertEqual("FAIL", handoff.validate_result(self.payload, **self.kwargs,
                                                          fixture_policy_by_case=policy)["status"])
        for status in ("BLOCKED", "NOT_RUN"):
            self.payload["status"] = status
            outcome["status"] = status
            outcome.pop("fixture_sha256", None)
            self.assertEqual(status, handoff.validate_result(self.payload, **self.kwargs,
                                                             fixture_policy_by_case=policy)["status"])
            outcome["fixture_sha256"] = "c" * 64
            self.assertEqual(status, handoff.validate_result(self.payload, **self.kwargs,
                                                             fixture_policy_by_case=policy)["status"])
            outcome["fixture_sha256"] = "d" * 64
            with self.assertRaises(ValueError):
                handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case=policy)
        outcome["fixture_sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            handoff.validate_result(self.payload, **self.kwargs, fixture_policy_by_case={"CASE-1": None})
        outcome.pop("fixture_sha256")
        self.assertEqual("NOT_RUN", handoff.validate_result(self.payload, **self.kwargs,
                                                             fixture_policy_by_case={"CASE-1": None})["status"])


if __name__ == "__main__":
    unittest.main()
