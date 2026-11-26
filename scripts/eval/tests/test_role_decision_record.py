from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import role_decision_record as records


def record(impact: str = "A1", invoke: bool = False) -> dict:
    claim = {"value": "UNKNOWN", "provenance": "test", "reason": "not exposed"}
    return {
        "schema_version": "1.0", "task_reference": "test task",
        "source_revision": "test revision", "policy_revision": "test policy", "role": "Architect",
        "decision": {"value": "INVOKE" if invoke else "SKIP", "reason": "test decision",
                     "timestamp": "2026-01-01T10:00:00Z"},
        "impact": impact,
        "requested": {key: copy.deepcopy(claim) for key in ("model", "effort", "profile")},
        "host_observed": {key: copy.deepcopy(claim) for key in ("model", "effort", "profile")},
        "dispatch": {"status": "ACCEPTED" if invoke else "NOT_ATTEMPTED",
                     "timestamp": "2026-01-01T10:01:00Z" if invoke else None, "reason": None},
        "execution": {"state": "NOT_STARTED", "started_at": None, "ended_at": None, "reason": None},
        "result": {"reference": None, "sha256": None, "reference_kind": None},
        "coordinator_disposition": {"value": "PENDING", "timestamp": "2026-01-01T10:00:00Z", "reason": None},
        "timing_assessment": {"value": "UNKNOWN", "assessor": "reviewer", "provenance": "test",
                              "assessed_at": "2026-01-01T10:04:00Z",
                              "first_dependent_action_at": None, "first_dependent_action_reference": None,
                              "no_qualifying_action_confirmed": None, "reason": "not yet reviewed"},
        "decision_id": "decision-1", "attempt_id": "attempt-1" if invoke else None,
        "retry_of": None, "trigger_source": "NATURAL",
        "signal_evidence": [{"reference": "test evidence", "captured_at": "2026-01-01T09:59:00Z"}],
        "supersedes_decision_id": None, "parent_decision_id": None, "retry_resolution_reason": None,
    }


class RoleDecisionRecordTests(unittest.TestCase):
    def assertError(self, data: dict, message: str) -> None:
        self.assertTrue(any(message in error for error in records.validate_record(data)), records.validate_record(data))

    def test_valid_routing_classes(self) -> None:
        for impact in ("A0", "A1"):
            with self.subTest(impact=impact):
                self.assertEqual([], records.validate_record(record(impact)))
        for impact in ("A2", "A3", "A4"):
            with self.subTest(impact=impact):
                self.assertEqual([], records.validate_record(record(impact, invoke=True)))

    def test_unknown_requires_reason(self) -> None:
        for group, field in (("requested", "model"), ("host_observed", "effort")):
            data = record()
            data[group][field]["reason"] = "  "
            with self.subTest(group=group, field=field):
                self.assertError(data, f"{group}.{field}=UNKNOWN requires a reason")
        data = record()
        data["timing_assessment"]["reason"] = None
        self.assertError(data, "timing_assessment.value=UNKNOWN requires a reason")

    def test_chronology_and_dispatch_order(self) -> None:
        cases = (
            (lambda d: d["signal_evidence"][0].update(captured_at="2026-01-01T10:01:00Z"), "captured after the decision"),
            (lambda d: d["dispatch"].update(timestamp="2026-01-01T10:00:00Z"), "decision must precede dispatch"),
            (lambda d: d["execution"].update(state="RUNNING", started_at="2026-01-01T10:00:30Z"), "execution cannot start before dispatch"),
            (lambda d: d["execution"].update(state="FAILED", started_at="2026-01-01T10:03:00Z", ended_at="2026-01-01T10:02:00Z"), "execution cannot end before it starts"),
            (lambda d: d["dispatch"].update(timestamp=None), "dispatch attempt requires a timestamp"),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                data = record("A2", invoke=True)
                mutate(data)
                self.assertError(data, message)
        data = record()
        data["dispatch"].update(status="ACCEPTED", timestamp="2026-01-01T10:01:00Z")
        data["attempt_id"] = "attempt-1"
        self.assertError(data, "SKIP cannot have a dispatch attempt")

    def test_timing_labels_and_contradictions(self) -> None:
        for label in ("EARLY", "ON_TIME", "LATE", "MISSED", "CORRECT_SKIP", "UNNECESSARY"):
            with self.subTest(label=label):
                invoke = label not in {"MISSED", "CORRECT_SKIP"}
                data = record("A1" if label in {"CORRECT_SKIP", "UNNECESSARY"} else "A2", invoke)
                timing = data["timing_assessment"]
                timing.update(value=label, reason="reviewer rationale")
                if label in {"EARLY", "ON_TIME", "LATE", "MISSED"}:
                    timing.update(first_dependent_action_at="2026-01-01T10:00:30Z" if label == "LATE" else "2026-01-01T10:02:00Z",
                                  first_dependent_action_reference="test action")
                if label == "CORRECT_SKIP":
                    timing["no_qualifying_action_confirmed"] = True
                self.assertEqual([], records.validate_record(data))
        data = record("A2", invoke=True)
        data["timing_assessment"].update(value="ON_TIME", reason=None)
        self.assertError(data, "ON_TIME timing requires a first dependent action")
        data = record("A2")
        data["timing_assessment"].update(value="CORRECT_SKIP", reason="reviewed", no_qualifying_action_confirmed=True)
        self.assertError(data, "CORRECT_SKIP is inconsistent with impact A2-A4")
        data = record("A1", invoke=True)
        data["timing_assessment"].update(value="UNNECESSARY", reason=None)
        self.assertError(data, "NATURAL A0/A1 INVOKE requires")

    def test_repo_file_digest_and_unsafe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.object(records, "ROOT", Path(directory)):
            content = b"synthetic result\n"
            (Path(directory) / "result.txt").write_bytes(content)
            data = record("A2", invoke=True)
            data["execution"].update(state="COMPLETED", started_at="2026-01-01T10:02:00Z", ended_at="2026-01-01T10:03:00Z")
            data["result"] = {"reference": "result.txt", "reference_kind": "REPO_FILE", "sha256": hashlib.sha256(content).hexdigest()}
            self.assertEqual([], records.validate_record(data))
            data["result"]["sha256"] = "0" * 64
            self.assertError(data, "REPO_FILE result sha256 mismatch")
            for path in ("../outside.txt", str(Path(directory) / "result.txt")):
                with self.subTest(path=path):
                    data["result"]["reference"] = path
                    self.assertError(data, "safe repository-relative path")

    def test_timestamps_require_timezone_and_valid_format(self) -> None:
        for timestamp in ("2026-01-01T10:00:00", "2026-01-01 10:00:00Z", "2026-13-01T10:00:00Z"):
            with self.subTest(timestamp=timestamp):
                data = record()
                data["decision"]["timestamp"] = timestamp
                self.assertTrue(records.validate_record(data))
        data = record()
        data["decision"]["timestamp"] = "2026-01-01T11:00:00+01:00"
        self.assertEqual([], records.validate_record(data))

    def run_chain(self, *items: dict) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, item in enumerate(items):
                path = Path(directory) / f"{index}.json"
                path.write_text(json.dumps(item), encoding="utf-8")
                paths.append(str(path))
            output = io.StringIO()
            with patch.object(sys, "argv", ["role_decision_record.py", "validate", *paths]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                result = records.main()
            return result, output.getvalue()

    def test_retry_chains_and_contradictions(self) -> None:
        original = record("A2", invoke=True)
        retry = copy.deepcopy(original)
        retry.update(attempt_id="attempt-2", retry_of="attempt-1")
        retry["dispatch"]["timestamp"] = "2026-01-01T10:02:00Z"
        self.assertEqual(0, self.run_chain(original, retry)[0])
        cases = (
            (lambda d: d.update(attempt_id="attempt-1", retry_of=None), "duplicate or conflicting attempt_id"),
            (lambda d: d.update(impact="A3"), "differs"),
            (lambda d: d["dispatch"].update(timestamp="2026-01-01T10:01:00Z"), "retry target dispatch must be earlier"),
            (lambda d: d.update(retry_of=None), "attempt chain requires exactly one root"),
            (lambda d: d.update(retry_of="missing"), "partial scans require a reason"),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                invalid = copy.deepcopy(retry)
                mutate(invalid)
                status, output = self.run_chain(original, invalid)
                self.assertEqual(1, status, output)
                self.assertIn(message, output)
        partial = copy.deepcopy(retry)
        partial["retry_resolution_reason"] = "target omitted from partial scan"
        self.assertEqual(0, self.run_chain(partial)[0])
        retry["retry_of"] = retry["attempt_id"]
        self.assertError(retry, "retry_of cannot refer to the same attempt_id")

    def v11(self, invoke: bool = True) -> dict:
        data = record("A2" if invoke else "A1", invoke)
        data["schema_version"] = "1.1"
        data["dispatch"].update(coordinator_bounds=None, time_unknown_reason=None)
        data["execution"].update(started_coordinator_bounds=None, started_time_unknown_reason=None,
                                 ended_coordinator_bounds=None, ended_time_unknown_reason=None)
        data["timing_assessment"].update(first_dependent_action_coordinator_bounds=None,
                                         first_dependent_action_time_unknown_reason=None)
        return data

    def v12(self, impact: str, invoke: bool, trigger: str) -> dict:
        data = self.v11(invoke)
        data["schema_version"] = "1.2"
        data["architect_trigger"] = {
            "class": trigger,
            "reason": "reviewed trigger classification",
            "evidence_reference": "test evidence",
        }
        if trigger != "UNKNOWN":
            data["architect_trigger"]["evidence_reference"] = "test evidence"
        data["impact"] = impact
        return data

    def test_v12_structured_architecture_trigger_separates_routing_from_timing(self) -> None:
        # ROUTE-TRIGGER-01: qualifying A1 invocation can be chronologically ON_TIME.
        invoke = self.v12("A1", True, "A1_SHARED_PUBLIC_CONTRACT")
        invoke["timing_assessment"].update(value="ON_TIME", reason="reviewed",
            first_dependent_action_at="2026-01-01T10:02:00Z", first_dependent_action_reference="action")
        self.assertEqual([], records.validate_record(invoke))

        # ROUTE-TRIGGER-02: impact A2 with explicit NONE may correctly skip.
        skip = self.v12("A2", False, "NONE")
        skip["timing_assessment"].update(value="CORRECT_SKIP", reason="no qualifying trigger",
            no_qualifying_action_confirmed=True)
        self.assertEqual([], records.validate_record(skip))

        # A material A2 trigger still requires invocation.
        material = self.v12("A2", True, "A2_MATERIAL_DEPENDENCY")
        self.assertEqual([], records.validate_record(material))

    def test_v12_trigger_missing_invalid_and_contradictory_fail_closed(self) -> None:
        # ROUTE-TRIGGER-03/05: missing or contradictory trigger evidence must fail closed.
        data = self.v12("A2", True, "A2_SHARED_CONTRACT")
        del data["architect_trigger"]
        self.assertTrue(records.validate_record(data))
        data = self.v12("A2", True, "A2_SHARED_CONTRACT")
        data["architect_trigger"]["class"] = "MADE_UP"
        self.assertTrue(records.validate_record(data))
        data = self.v12("A3", False, "NONE")
        data["timing_assessment"].update(value="CORRECT_SKIP", reason="reviewed",
            no_qualifying_action_confirmed=True)
        self.assertError(data, "CORRECT_SKIP is inconsistent with impact A2-A4")
        data = self.v12("A2", False, "NONE")
        data["timing_assessment"].update(value="MISSED", reason="reviewed",
            first_dependent_action_at="2026-01-01T10:02:00Z", first_dependent_action_reference="action")
        self.assertError(data, "MISSED conflicts with an explicit NONE Architect trigger")

    def test_v12_unknown_trigger_cannot_confirm_correct_skip(self) -> None:
        # Independent review P1: UNKNOWN trigger must not establish a correct skip.
        data = self.v12("A1", False, "UNKNOWN")
        data["timing_assessment"].update(value="CORRECT_SKIP", reason="no trigger seen",
            no_qualifying_action_confirmed=True)
        self.assertError(data, "CORRECT_SKIP requires an explicit NONE Architect trigger")

    def test_v12_none_trigger_cannot_be_assessed_missed_across_natural_skip_impacts(self) -> None:
        # Independent review P2: NONE at the recorded decision conflicts with MISSED for any natural skip impact.
        for impact in ("A0", "A1"):
            with self.subTest(impact=impact):
                data = self.v12(impact, False, "NONE")
                data["timing_assessment"].update(value="MISSED", reason="later action",
                    first_dependent_action_at="2026-01-01T10:02:00Z", first_dependent_action_reference="action")
                self.assertError(data, "MISSED conflicts with an explicit NONE Architect trigger")

    def test_v12_qualifying_natural_invoke_cannot_be_assessed_unnecessary(self) -> None:
        # An UNNECESSARY verdict contradicts the qualifying trigger even when chronology is separate.
        for impact, trigger in (
            ("A1", "A1_SHARED_PUBLIC_CONTRACT"),
            ("A2", "A2_SHARED_CONTRACT"),
            ("A3", "A3_MULTICOMPONENT_OR_MIGRATION_OR_SECURITY_OR_OPERATIONS"),
            ("A4", "A4_BROAD_IMPACT_OR_HARD_ROLLBACK"),
        ):
            with self.subTest(impact=impact, trigger=trigger):
                data = self.v12(impact, True, trigger)
                data["timing_assessment"].update(value="UNNECESSARY", reason="reviewer found invocation unnecessary")
                self.assertError(data, "UNNECESSARY conflicts with a qualifying Architect trigger")

    def test_v12_concrete_trigger_class_must_match_impact(self) -> None:
        # Independent review P2: no concrete trigger class may contradict the impact class.
        for impact, trigger in (("A1", "A2_SHARED_CONTRACT"), ("A0", "A4_BROAD_IMPACT_OR_HARD_ROLLBACK")):
            with self.subTest(impact=impact, trigger=trigger):
                data = self.v12(impact, False, trigger)
                data["timing_assessment"].update(value="CORRECT_SKIP", reason="no qualifying action",
                    no_qualifying_action_confirmed=True)
                self.assertError(data, f"trigger class {trigger} is incompatible with impact {impact}")

    def test_v12_natural_a0_a1_invoke_without_trigger_is_unnecessary_or_unknown(self) -> None:
        # ROUTE-TRIGGER-04: no trigger needs UNKNOWN or reviewer-confirmed UNNECESSARY.
        data = self.v12("A1", True, "NONE")
        data["timing_assessment"].update(value="ON_TIME", reason="chronology was timely",
            first_dependent_action_at="2026-01-01T10:02:00Z", first_dependent_action_reference="action")
        self.assertError(data, "requires UNKNOWN or UNNECESSARY")
        data["timing_assessment"].update(value="UNNECESSARY", reason="independent reviewer found no trigger",
            first_dependent_action_at=None, first_dependent_action_reference=None)
        self.assertEqual([], records.validate_record(data))

    def test_v12_retry_cannot_change_architecture_trigger(self) -> None:
        # ROUTE-TRIGGER-07: retry preserves the structural decision and its trigger.
        original = self.v12("A2", True, "A2_SHARED_CONTRACT")
        retry = copy.deepcopy(original)
        retry.update(attempt_id="attempt-2", retry_of="attempt-1")
        retry["dispatch"]["timestamp"] = "2026-01-01T10:02:00Z"
        retry["architect_trigger"] = {
            "class": "A2_MATERIAL_DEPENDENCY",
            "reason": "changed after retry",
            "evidence_reference": "other evidence",
        }
        status, output = self.run_chain(original, retry)
        self.assertEqual(1, status, output)
        self.assertIn("architect_trigger", output)

    def test_v12_timing_bounds_preserve_unknown_when_order_overlaps(self) -> None:
        # ROUTE-TRIGGER-06: preserving chronology constraints is separate from routing correctness.
        data = self.v12("A1", True, "A1_SHARED_PUBLIC_CONTRACT")
        data["dispatch"].update(timestamp=None, time_unknown_reason="host omitted time",
            coordinator_bounds=self.bounds("2026-01-01T10:00:30Z", "2026-01-01T10:01:30Z"))
        data["timing_assessment"].update(value="ON_TIME", reason="reviewed",
            first_dependent_action_at=None, first_dependent_action_reference="action",
            first_dependent_action_time_unknown_reason="host omitted time",
            first_dependent_action_coordinator_bounds=self.bounds("2026-01-01T10:01:00Z", "2026-01-01T10:02:00Z"))
        self.assertError(data, "requires accepted dispatch before")
        data["timing_assessment"].update(value="UNKNOWN", reason="coordinator bounds overlap")
        self.assertEqual([], records.validate_record(data))

    def test_v10_v11_reject_v12_trigger_field(self) -> None:
        # ROUTE-TRIGGER-08: legacy acceptance stays unchanged; v1.2 does not use v1.0 logic.
        for version in ("1.0", "1.1"):
            data = self.v11(invoke=True) if version == "1.1" else record("A1", invoke=True)
            data["architect_trigger"] = {
                "class": "A1_TRUST_BOUNDARY",
                "reason": "test trigger",
                "evidence_reference": "test evidence",
            }
            self.assertTrue(records.validate_record(data), version)

    def test_default_cli_validates_historical_sidecars(self) -> None:
        # ROUTE-TRIGGER-09: all stored historical sidecars are checked as a repository scan.
        output = io.StringIO()
        with patch.object(sys, "argv", ["role_decision_record.py", "validate"]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = records.main()
        self.assertEqual(0, status, output.getvalue())

    def test_v12_unknown_trigger_can_omit_evidence_but_specific_trigger_cannot(self) -> None:
        # ROUTE-TRIGGER-05: UNKNOWN is explicitly unknown, but concrete classes need evidence.
        unknown = self.v12("A2", True, "UNKNOWN")
        unknown["architect_trigger"]["evidence_reference"] = None
        self.assertEqual([], records.validate_record(unknown))
        specific = self.v12("A2", True, "A2_SHARED_CONTRACT")
        specific["architect_trigger"]["evidence_reference"] = None
        self.assertTrue(records.validate_record(specific))
        specific["architect_trigger"]["evidence_reference"] = "   "
        self.assertTrue(records.validate_record(specific))

    @staticmethod
    def bounds(earliest: str, latest: str) -> dict:
        return {"earliest": earliest, "latest": latest, "evidence": "coordinator receipt"}

    def test_v11_nullable_host_times_and_bounds(self) -> None:
        data = self.v11()
        data["dispatch"].update(timestamp=None, time_unknown_reason="host omitted time",
            coordinator_bounds=self.bounds("2026-01-01T10:00:10Z", "2026-01-01T10:01:00Z"))
        data["execution"].update(state="COMPLETED", started_time_unknown_reason="host omitted start",
                                 ended_time_unknown_reason="host omitted end")
        data["result"].update(reference="private result", sha256="a" * 64, reference_kind="PRIVATE")
        data["timing_assessment"].update(value="ON_TIME", first_dependent_action_reference="action",
            first_dependent_action_time_unknown_reason="host omitted time",
            first_dependent_action_coordinator_bounds=self.bounds("2026-01-01T10:02:00Z", "2026-01-01T10:03:00Z"))
        self.assertEqual([], records.validate_record(data))
        for first in ("2026-01-01T10:01:00Z", "2026-01-01T10:00:30Z"):
            data["timing_assessment"]["first_dependent_action_coordinator_bounds"]["earliest"] = first
            self.assertError(data, "requires accepted dispatch before")
        data["timing_assessment"].update(value="UNKNOWN", reason="bounds overlap")
        self.assertEqual([], records.validate_record(data))

    def test_v11_late_and_skip_evidence(self) -> None:
        data = self.v11()
        data["dispatch"].update(timestamp=None, time_unknown_reason="not reported",
            coordinator_bounds=self.bounds("2026-01-01T10:00:10Z", "2026-01-01T10:03:00Z"))
        data["timing_assessment"].update(value="LATE", first_dependent_action_reference="action",
                                        first_dependent_action_at="2026-01-01T10:02:00Z")
        self.assertError(data, "LATE requires action proven before")
        data["timing_assessment"]["first_dependent_action_at"] = "2026-01-01T09:59:30Z"
        self.assertEqual([], records.validate_record(data))
        skip = self.v11(False)
        skip["timing_assessment"].update(value="CORRECT_SKIP", reason="reviewed", no_qualifying_action_confirmed=True,
                                         first_dependent_action_reference="action")
        self.assertError(skip, "CORRECT_SKIP forbids action occurrence evidence")
        skip["timing_assessment"].update(value="MISSED", first_dependent_action_at="2026-01-01T09:59:30Z")
        self.assertError(skip, "MISSED requires a qualifying action after SKIP")

    def test_all_timestamp_fields_reject_invalid_calendar_without_format_checker(self) -> None:
        data = self.v11()
        data["dispatch"].update(coordinator_bounds=self.bounds("2026-01-01T10:00:30Z", "2026-01-01T10:02:00Z"))
        data["execution"].update(started_coordinator_bounds=self.bounds("2026-01-01T10:02:00Z", "2026-01-01T10:03:00Z"),
            ended_coordinator_bounds=self.bounds("2026-01-01T10:03:00Z", "2026-01-01T10:04:00Z"))
        data["timing_assessment"].update(first_dependent_action_at="2026-01-01T10:03:00Z",
            first_dependent_action_reference="action", first_dependent_action_coordinator_bounds=self.bounds("2026-01-01T10:02:00Z", "2026-01-01T10:04:00Z"))
        data["execution"].update(started_at="2026-01-01T10:02:00Z", ended_at="2026-01-01T10:03:00Z")
        def mutate_dates(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"timestamp", "started_at", "ended_at", "assessed_at", "first_dependent_action_at", "captured_at", "earliest", "latest"} and child:
                        yield path + (key,)
                    else:
                        yield from mutate_dates(child, path + (key,))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    yield from mutate_dates(child, path + (i,))
        for path in mutate_dates(data):
            item = copy.deepcopy(data)
            parent = item
            for key in path[:-1]: parent = parent[key]
            parent[path[-1]] = "2026-02-30T10:00:00Z"
            with self.subTest(path=path), patch.object(records, "FormatChecker", return_value=None):
                self.assertTrue(records.validate_record(item))

    def test_v11_retry_topology_and_immutable_values(self) -> None:
        first = self.v11()
        first["dispatch"].update(timestamp=None, time_unknown_reason="not exposed")
        second = copy.deepcopy(first)
        second.update(attempt_id="attempt-2", retry_of="attempt-1")
        status, output = self.run_chain(second, first)
        self.assertEqual(0, status, output)
        self.assertIn("chronology UNKNOWN", output)
        changed = copy.deepcopy(second)
        changed["decision"]["reason"] = "changed"
        self.assertIn("differs", self.run_chain(first, changed)[1])
        cycle = copy.deepcopy(first)
        cycle["retry_of"] = "attempt-2"
        self.assertIn("cycle", self.run_chain(second, cycle)[1])
        cross = copy.deepcopy(second)
        cross["decision_id"] = "another-decision"
        self.assertIn("differs", self.run_chain(first, cross)[1])

    def test_repo_root_alias_and_escaping_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            alias = Path(directory) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            (root / "result").write_text("content")
            (root / "escape").symlink_to(Path(directory) / "outside")
            data = self.v11()
            data["execution"].update(state="COMPLETED", started_time_unknown_reason="unknown", ended_time_unknown_reason="unknown")
            data["result"].update(reference="result", reference_kind="REPO_FILE", sha256=hashlib.sha256(b"content").hexdigest())
            with patch.object(records, "ROOT", alias):
                self.assertEqual([], records.validate_record(data))
                data["result"]["reference"] = "escape"
                self.assertError(data, "safe repository-relative path")

    def test_external_content_is_not_verified(self) -> None:
        for kind in ("EXTERNAL", "PRIVATE"):
            data = self.v11()
            data["execution"].update(state="COMPLETED", started_time_unknown_reason="unknown", ended_time_unknown_reason="unknown")
            data["result"].update(reference="result", reference_kind=kind, sha256="a" * 64)
            status, output = self.run_chain(data)
            self.assertEqual(0, status, output)
            self.assertIn("content NOT VERIFIED", output)


if __name__ == "__main__":
    unittest.main()
