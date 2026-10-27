from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "engine.py"
spec = importlib.util.spec_from_file_location("strategy_value_realization", MODULE)
ledger = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ledger)


def ev(value, source_id, published_at="2026-01-01"):
    return {"value": str(value), "source_id": source_id, "published_at": published_at}


def base():
    return {
        "as_of": "2026-01-31",
        "initiatives": [{
            "initiative_id": "initiative-1",
            "owner": "owner-1",
            "currency": "USD",
            "funded_amount": ev("100000", "approved-funding"),
            "review_cadence_days": ev("30", "approved-cadence"),
            "last_review_at": "2025-12-01",
            "benefits": [{
                "kpi_id": "savings-run-rate",
                "kind": "lagging",
                "unit": "USD/month",
                "baseline": ev("0", "baseline"),
                "target": ev("1000", "target"),
                "forecast": [{"period": "2026-01", **ev("1000", "forecast-jan")}],
                "actual": [{"period": "2026-01", **ev("800", "actual-jan", "2026-01-31")}],
                "decision_critical": True,
            }],
            "decision_rules": {
                "stop_if_variance_pct_at_or_below": ev("-0.50", "stop-policy"),
                "correct_if_variance_pct_at_or_below": ev("-0.10", "correct-policy"),
            },
        }],
    }


class ValueRealizationTests(unittest.TestCase):
    def test_known_answer_variance_and_review_action(self):
        result = ledger.evaluate_ledger(base())
        initiative = result["initiatives"][0]
        kpi = initiative["benefits"][0]
        self.assertEqual("REVIEWABLE", result["status"])
        self.assertEqual("DUE", initiative["review_state"])
        self.assertEqual("2025-12-31", initiative["next_review_at"])
        self.assertEqual("-200.00", kpi["periods"][0]["variance"])
        self.assertEqual("-0.2", kpi["periods"][0]["variance_pct"])
        self.assertEqual("CORRECT_REVIEW", initiative["decision"]["action"])
        self.assertTrue(initiative["decision"]["human_decision_required"])
        self.assertFalse(result["writes_performed"])

    def test_source_provenance_is_preserved(self):
        result = ledger.evaluate_ledger(base())
        period = result["initiatives"][0]["benefits"][0]["periods"][0]
        self.assertEqual("forecast-jan", period["forecast_source_id"])
        self.assertEqual("2026-01-31", period["actual_published_at"])

    def test_unmatched_periods_are_reported_without_zero_fill(self):
        data = base()
        benefit = data["initiatives"][0]["benefits"][0]
        benefit["actual"] = []
        result = ledger.evaluate_ledger(data)["initiatives"][0]["benefits"][0]
        self.assertEqual("BLOCKED_NO_ALIGNED_ACTUAL", result["status"])
        self.assertEqual(["2026-01"], result["unmatched_forecast_periods"])
        self.assertEqual([], result["periods"])

    def test_missing_review_and_decision_policies_stay_unconfigured(self):
        data = base()
        item = data["initiatives"][0]
        item["last_review_at"] = None
        item.pop("decision_rules")
        result = ledger.evaluate_ledger(data)["initiatives"][0]
        self.assertEqual("NOT_CONFIGURED", result["review_state"])
        self.assertEqual("NOT_CONFIGURED", result["decision"]["status"])

    def test_funded_amount_requires_currency(self):
        data = base()
        data["initiatives"][0].pop("currency")
        with self.assertRaisesRegex(ledger.LedgerInputError, "currency is required"):
            ledger.evaluate_ledger(data)

    def test_future_dated_actual_is_rejected(self):
        data = base()
        data["initiatives"][0]["benefits"][0]["actual"][0]["published_at"] = "2026-02-01"
        with self.assertRaisesRegex(ledger.LedgerInputError, "future-dated"):
            ledger.evaluate_ledger(data)

    def test_thresholds_need_provenance_and_correct_order(self):
        data = base()
        data["initiatives"][0]["decision_rules"]["stop_if_variance_pct_at_or_below"] = {"value": "-0.5"}
        with self.assertRaisesRegex(ledger.LedgerInputError, "source_id"):
            ledger.evaluate_ledger(data)
        data = base()
        data["initiatives"][0]["decision_rules"]["stop_if_variance_pct_at_or_below"] = ev("-0.1", "stop")
        data["initiatives"][0]["decision_rules"]["correct_if_variance_pct_at_or_below"] = ev("-0.2", "correct")
        with self.assertRaisesRegex(ledger.LedgerInputError, "stop threshold must be <="):
            ledger.evaluate_ledger(data)

    def test_duplicate_ids_and_ambiguous_critical_kpis_are_rejected(self):
        data = base()
        data["initiatives"].append(dict(data["initiatives"][0]))
        with self.assertRaisesRegex(ledger.LedgerInputError, "unique"):
            ledger.evaluate_ledger(data)
        data = base()
        second = dict(data["initiatives"][0]["benefits"][0])
        second["kpi_id"] = "second-critical-kpi"
        data["initiatives"][0]["benefits"].append(second)
        with self.assertRaisesRegex(ledger.LedgerInputError, "exactly one"):
            ledger.evaluate_ledger(data)

    def test_cli_is_machine_readable_and_read_only(self):
        result = subprocess.run([sys.executable, str(MODULE)], input=json.dumps(base()), text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["writes_performed"])


if __name__ == "__main__":
    unittest.main()
