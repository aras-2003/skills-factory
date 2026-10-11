from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import assertions
import receipt
import validate_isolation
import validate_routing


class EvalProtocolTests(unittest.TestCase):
    def test_registry_inputs_are_isolated(self) -> None:
        errors = validate_isolation.validate_registry(HERE.parents[3])
        self.assertEqual([], errors)

    def test_executor_input_rejects_evaluator_only_heading_variants(self) -> None:
        headings = (
            "## Expected route",
            "## Evaluator-only rubric",
            "## Evaluator instructions",
            "## Scoring rubric",
        )
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIsNotNone(
                    validate_isolation.FORBIDDEN_INPUT_HEADINGS.search(heading + "\\nsecret verdict")
                )

    def test_assisted_pass_is_rejected(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="PASS",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version="1.0.0",
            component_digest="1" * 64,
            provider="test",
            model_id="test",
            reasoning="none",
            catalog=[],
            prompt="test",
            output=__file__,
            tool_trace=None,
            reviewer="unit-test",
            assisted=True,
            note=None,
        )
        with self.assertRaisesRegex(ValueError, "assisted runs cannot be recorded as PASS"):
            receipt.create_receipt(args)

    def test_not_run_does_not_need_output(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="NOT_RUN",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version="1.0.0",
            component_digest=None,
            provider=None,
            model_id=None,
            reasoning=None,
            catalog=[],
            prompt=None,
            output=None,
            tool_trace=None,
            reviewer=None,
            assisted=False,
            note="runtime unavailable",
        )
        record = receipt.create_receipt(args)
        self.assertEqual("NOT_RUN", record["evaluation"]["status"])
        self.assertIsNone(record["outcome"])
        self.assertEqual("not_executed", record["execution_state"])
        self.assertIsNone(record["execution"]["actual_output_path"])

    def test_non_execution_states_have_no_test_outcome(self) -> None:
        for state in ("blocked", "awaiting_runner", "no_steps", "not_executed"):
            args = argparse.Namespace(
                case_id="case-001-premium-vs-generic",
                status="NOT_RUN",
                execution_state=state,
                execution_state_reason="controlled test condition",
                source_revision="abcdef1234567",
                component="commerce-product-deep-dive",
                component_version=None,
                component_digest=None,
                provider=None,
                model_id=None,
                reasoning=None,
                catalog=[],
                prompt=None,
                output=None,
                tool_trace=None,
                reviewer=None,
                assisted=False,
                note="runtime did not produce a test result",
            )
            record = receipt.create_receipt(args)
            self.assertIsNone(record["outcome"])
            self.assertEqual(state, record["execution_state"])
            self.assertEqual([], receipt.validate_receipt_data(record, root=HERE.parents[3]))

    def test_executed_verdict_maps_to_separate_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "output.txt"
            output.write_text("Decision: INVESTIGATE\n", encoding="utf-8")
            for status, outcome in (("PASS", "passed"), ("FAIL", "failed"), ("REVIEW_REQUIRED", None)):
                with self.subTest(status=status):
                    args = self._runtime_args(output)
                    args.status = status
                    record = receipt.create_receipt(args)
                    self.assertEqual(status, record["evaluation"]["status"])
                    self.assertEqual(outcome, record["outcome"])
                    self.assertEqual("executed", record["execution_state"])

    def test_legacy_receipt_without_execution_state_remains_readable(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="NOT_RUN",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version=None,
            component_digest=None,
            provider=None,
            model_id=None,
            reasoning=None,
            catalog=[],
            prompt=None,
            output=None,
            tool_trace=None,
            reviewer=None,
            assisted=False,
            note="runtime unavailable",
        )
        record = receipt.create_receipt(args)
        record.pop("outcome")
        record.pop("execution_state")
        record.pop("execution_state_reason")
        self.assertEqual([], receipt.validate_receipt_data(record, root=HERE.parents[3]))

    def test_not_run_cannot_claim_execution_or_outcome(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="NOT_RUN",
            execution_state="executed",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version=None,
            component_digest=None,
            provider=None,
            model_id=None,
            reasoning=None,
            catalog=[],
            prompt=None,
            output=None,
            tool_trace=None,
            reviewer=None,
            assisted=False,
            note="invalid state",
        )
        with self.assertRaisesRegex(ValueError, "NOT_RUN cannot have execution_state=executed"):
            receipt.create_receipt(args)

    def test_stale_input_digest_is_detected(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="NOT_RUN",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version="1.0.0",
            component_digest=None,
            provider=None,
            model_id=None,
            reasoning=None,
            catalog=[],
            prompt=None,
            output=None,
            tool_trace=None,
            reviewer=None,
            assisted=False,
            note="test record for stale input digest validation",
        )
        record = receipt.create_receipt(args)
        record["case"]["input_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "receipt.json"
            p.write_text(json.dumps(record), encoding="utf-8")
            errors = receipt.validate_receipt(p)
        self.assertTrue(any("input digest mismatch" in e for e in errors))

    def _runtime_args(self, output: Path, *, evidence_scope: str = "current-version") -> argparse.Namespace:
        version, digest = receipt.current_component_identity(HERE.parents[3], "commerce-product-deep-dive")
        return argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="PASS",
            evidence_scope=evidence_scope,
            source_revision=receipt.current_source_revision(HERE.parents[3]),
            component="commerce-product-deep-dive",
            component_version=version,
            component_digest=digest,
            provider="test-provider",
            model_id="test-model",
            reasoning="none",
            catalog=["commerce-product-deep-dive"],
            prompt="test",
            output=str(output),
            tool_trace=None,
            reviewer="unit-test",
            assisted=False,
            note=None,
        )

    def test_imported_not_run_cannot_be_relabelled_pass_without_runtime_evidence(self) -> None:
        args = argparse.Namespace(
            case_id="case-001-premium-vs-generic",
            status="NOT_RUN",
            evidence_scope="current-version",
            source_revision="abcdef1234567",
            component="commerce-product-deep-dive",
            component_version=None,
            component_digest=None,
            provider=None,
            model_id=None,
            reasoning=None,
            catalog=[],
            prompt=None,
            output=None,
            tool_trace=None,
            reviewer=None,
            assisted=False,
            note="runtime unavailable",
        )
        record = receipt.create_receipt(args)
        record["evaluation"]["status"] = "PASS"
        errors = receipt.validate_receipt_data(record, root=HERE.parents[3], current_revision=record["source_revision"])
        self.assertTrue(any("requires runtime/component/output identity" in e or "schema:" in e for e in errors))

    def test_current_version_receipt_rejects_stale_component_and_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "output.txt"
            output.write_text("Decision: TEST\n", encoding="utf-8")
            args = self._runtime_args(output)
            record = receipt.create_receipt(args)
            record["component"]["version"] = "0.0.0"
            record["component"]["content_sha256"] = "0" * 64
            record["source_revision"] = "deadbeef"
            errors = receipt.validate_receipt_data(
                record,
                root=HERE.parents[3],
                current_revision=receipt.current_source_revision(HERE.parents[3]),
            )
        self.assertTrue(any("component version mismatch" in e for e in errors))
        self.assertTrue(any("component content digest mismatch" in e for e in errors))
        self.assertTrue(any("source revision mismatch" in e for e in errors))

    def test_runtime_output_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "output.txt"
            output.write_text("Decision: TEST\n", encoding="utf-8")
            args = self._runtime_args(output)
            record = receipt.create_receipt(args)
            output.write_text("tampered\n", encoding="utf-8")
            errors = receipt.validate_receipt_data(
                record,
                root=HERE.parents[3],
                current_revision=record["source_revision"],
            )
        self.assertTrue(any("output digest mismatch" in e for e in errors))

    def test_historical_receipt_is_not_misrepresented_as_current_version_proof(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "output.txt"
            output.write_text("historical output\n", encoding="utf-8")
            args = self._runtime_args(output, evidence_scope="historical")
            args.source_revision = "abcdef1234567"
            args.component_version = "0.9.0"
            args.component_digest = "2" * 64
            record = receipt.create_receipt(args)
            errors = receipt.validate_receipt_data(
                record,
                root=HERE.parents[3],
                current_revision=receipt.current_source_revision(HERE.parents[3]),
            )
        self.assertEqual("historical", record["evidence_scope"])
        self.assertFalse(any("component version mismatch" in e for e in errors))
        self.assertFalse(any("component content digest mismatch" in e for e in errors))
        self.assertFalse(any("source revision mismatch" in e for e in errors))

    def test_deterministic_assertions_distinguish_good_and_bad_output(self) -> None:
        rubric = {
            "assertions": {
                "deterministic": [
                    {"contains": "UNKNOWN"},
                    {"not_contains": "guaranteed"},
                    {"regex": r"Decision:\s+INVESTIGATE"},
                ]
            }
        }
        good = "Decision: INVESTIGATE\nCandidate Fit: UNKNOWN\n"
        bad = "Decision: PURSUE\nCandidate Fit: 100/100 guaranteed\n"
        good_ok, good_failures = assertions.evaluate(good, rubric)
        bad_ok, bad_failures = assertions.evaluate(bad, rubric)
        self.assertTrue(good_ok, good_failures)
        self.assertFalse(bad_ok)
        self.assertGreaterEqual(len(bad_failures), 1)

    def test_natural_routing_bad_control_leaks_target_and_fails(self) -> None:
        leaked = validate_routing.leaked_capabilities(
            "Please use unit-economics-review for this request.",
            {"unit-economics-review", "supplier-viability-review"},
        )
        self.assertEqual(["unit-economics-review"], leaked)

    def test_natural_routing_plain_language_does_not_leak_target(self) -> None:
        leaked = validate_routing.leaked_capabilities(
            "Policz economics i break-even CAC dla tego produktu.",
            {"unit-economics-review", "supplier-viability-review"},
        )
        self.assertEqual([], leaked)


if __name__ == "__main__":
    unittest.main()
