from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "failure_injection.py"
spec = importlib.util.spec_from_file_location("failure_injection", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class InjectedFailureTests(unittest.TestCase):
    def test_all_failures_are_simulated_and_not_runtime_success(self):
        for scenario in module.FAILURES:
            with self.subTest(scenario=scenario):
                result = module.failure_probe(scenario)
                self.assertFalse(result["provider_calls_executed"])
                self.assertIsNone(result["tool_receipt"])
                self.assertIsNone(result["real_outcome"])
                self.assertEqual("NOT_RUN", result["real_execution_state"])
                self.assertEqual("not_observed", result["client_display_state"])

    def test_missing_tool_denied_timeout_are_blocked_not_fail(self):
        for case in ("timeout", "permission_denied", "tool_unavailable", "renderer_unavailable"):
            self.assertEqual("BLOCKED", module.failure_probe(case)["simulated_expected_status"])

    def test_observed_denial_with_no_steps_is_not_fail(self):
        observed = {"execution_state": "blocked", "actual_exception": "permission denied"}
        self.assertEqual("NOT_RUN", module.evaluate_observed_failure("permission_denied", observed)["status"])

    def test_runtime_trace_is_required_for_review(self):
        observed = {"execution_state": "executed", "actual_exception": "ValueError"}
        self.assertEqual("REVIEW_REQUIRED", module.evaluate_observed_failure("incompatible_schema", observed)["status"])

    def test_never_calls_arbitrary_actions(self):
        called = []
        with self.assertRaises(ValueError):
            module.failure_probe("timeout", lambda: called.append("network"))
        self.assertEqual([], called)

    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError):
            module.failure_probe("force_prod_write")


if __name__ == "__main__":
    unittest.main()
