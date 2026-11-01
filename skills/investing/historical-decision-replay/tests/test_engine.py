import unittest
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.engine import ReplayInputError, evaluate_replay, net_return, summarize_returns, validate_information_set


def synthetic_snapshots(decision_at):
    """Clearly synthetic, hash-shaped references for arithmetic contract tests."""
    return {
        domain: {
            "snapshot_id": f"synthetic-{domain}-snapshot",
            "source_id": f"synthetic-{domain}-source",
            "content_sha256": str(index) * 64,
            "published_at": decision_at,
            "observed_at": decision_at,
        }
        for index, domain in enumerate(("decision", "thesis", "policy", "portfolio", "market"), 1)
    }


class ReplayEngineTests(unittest.TestCase):
    def test_accepts_only_timezone_aware_predecision_evidence(self):
        rows = [{"source_id": "fixture-1", "published_at": "2020-01-01T09:00:00Z", "observed_at": "2020-01-01T09:00:00Z"}]
        self.assertEqual(rows, validate_information_set("2020-01-01T10:00:00Z", rows))

    def test_rejects_future_publication_and_observation(self):
        for field in ("published_at", "observed_at"):
            row = {"source_id": "fixture-1", "published_at": "2020-01-01T09:00:00Z", "observed_at": "2020-01-01T09:00:00Z"}
            row[field] = "2020-01-01T11:00:00Z"
            with self.subTest(field=field), self.assertRaises(ReplayInputError):
                validate_information_set("2020-01-01T10:00:00Z", [row])

    def test_rejects_timezone_free_timestamps(self):
        with self.assertRaises(ReplayInputError):
            validate_information_set("2020-01-01T10:00:00", [])

    def test_known_answer_net_return_includes_entry_and_exit_costs(self):
        self.assertEqual("0.089054726368159203980099502", str(net_return("100", "110", 0, 50)))

    def test_rejects_invalid_prices_and_costs(self):
        for args in ((0, 100, 0, 0), (100, 110, -1, 0), (100, 110, 10000, 0)):
            with self.subTest(args=args), self.assertRaises(ReplayInputError):
                net_return(*args)

    def test_summary_exposes_denominator_and_no_significance_claim(self):
        result = summarize_returns([
            {"strategy_net_return": "0.1", "baseline_net_return": "0.05"},
            {"strategy_net_return": "0.0", "baseline_net_return": "0.02"},
        ])
        self.assertEqual(2, result["denominator"])
        self.assertEqual("0.5", result["paired_outperformance_rate"])
        self.assertFalse(result["statistical_significance_claimed"])

    def test_empty_sample_blocks_instead_of_emitting_zero(self):
        self.assertEqual({"status": "BLOCKED_NO_OBSERVATIONS", "n": 0}, summarize_returns([]))

    def test_costed_replay_reports_baselines_turnover_drawdown_and_oos(self):
        rows = []
        for index, (asset, benchmark, trend, exposure, trend_exposure) in enumerate((
            ("0.10", "0.05", "0.08", "1", "1"),
            ("-0.10", "-0.03", "-0.04", "1", "0"),
            ("0.02", "0.01", "0.01", "0", "1"),
        )):
            day = 2 + index * 2
            decision = f"2020-01-{day:02d}T09:00:00Z"
            outcome = f"2020-01-{day + 1:02d}T09:00:00Z"
            rows.append({
                "decision_at": decision,
                "outcome_at": outcome,
                "source_id": f"asset-{index}",
                "benchmark_source_id": f"index-{index}",
                "trend_source_id": f"trend-{index}",
                "snapshots": synthetic_snapshots(decision),
                "information_inputs": [{"source_id": f"filing-{index}", "published_at": decision, "observed_at": decision}],
                "asset_return": asset,
                "benchmark_return": benchmark,
                "trend_return": trend,
                "strategy_exposure": exposure,
                "trend_exposure": trend_exposure,
                "event_type": "earnings",
                "alert_triggered": index != 1,
                "event_occurred": index == 0,
            })
        result = evaluate_replay(
            rows, rule_id="frozen-rule", rule_revision="a" * 40,
            rule_frozen_at="2020-01-01T00:00:00Z", fee_bps=10, slippage_bps=20,
            sample_metadata={"universe": "fixture securities", "selection_method": "predeclared fixture", "exclusions": "none", "survivorship_status": "ASSESSED"},
            split_at="2020-01-05T00:00:00Z",
        )
        self.assertEqual("DESCRIPTIVE_ONLY", result["status"])
        self.assertEqual(3, result["strategy"]["denominator"])
        self.assertLess(Decimal(result["strategy"]["max_drawdown"]), 0)
        self.assertGreater(Decimal(result["turnover"]["strategy_one_way_notional"]), 0)
        oos = result["out_of_sample"]
        self.assertEqual(1, oos["n"])
        self.assertEqual(Decimal("0.0"), Decimal(oos["strategy"]["cumulative_return"]))
        self.assertEqual(Decimal("0.01388"), Decimal(oos["buy_and_hold"]["cumulative_return"]))
        self.assertEqual(Decimal("0.00394"), Decimal(oos["benchmark"]["cumulative_return"]))
        self.assertEqual(Decimal("0.00394"), Decimal(oos["trend_following_baseline"]["cumulative_return"]))
        self.assertEqual("NOT_MODELED", result["costs"]["taxes"])
        self.assertEqual(1, result["alert_precision_recall"]["true_positives"])
        self.assertFalse(result["economic_edge_claimed"])

    def test_single_period_known_answer_applies_entry_and_exit_costs(self):
        row = {
            "decision_at": "2020-01-02T00:00:00Z", "outcome_at": "2020-01-03T00:00:00Z",
            "source_id": "asset", "benchmark_source_id": "index", "trend_source_id": "trend",
            "snapshots": synthetic_snapshots("2020-01-02T00:00:00Z"),
            "information_inputs": [{"source_id": "record", "published_at": "2020-01-02T00:00:00Z", "observed_at": "2020-01-02T00:00:00Z"}],
            "asset_return": "0.10", "benchmark_return": "0.05", "trend_return": "0.08",
            "strategy_exposure": "1", "trend_exposure": "1",
        }
        result = evaluate_replay(
            [row], rule_id="rule", rule_revision="b" * 40,
            rule_frozen_at="2020-01-01T00:00:00Z", fee_bps=25, slippage_bps=25,
            sample_metadata={"universe": "fixture", "selection_method": "fixed", "exclusions": "none", "survivorship_status": "ASSESSED"},
        )
        self.assertEqual(Decimal("0.089"), Decimal(result["strategy"]["cumulative_return"]))
        # Independent one-period arithmetic: 50 bps per-side cost is charged
        # on entry and exit, so each fully invested baseline retains 99% of
        # its gross ending value.
        self.assertEqual(Decimal("0.089"), Decimal(result["buy_and_hold"]["cumulative_return"]))
        self.assertEqual(Decimal("0.0395"), Decimal(result["benchmark"]["cumulative_return"]))
        self.assertEqual(Decimal("0.0692"), Decimal(result["trend_following_baseline"]["cumulative_return"]))
        self.assertFalse(result["economic_edge_claimed"])
        self.assertEqual({"status": "BLOCKED_MISSING_SPLIT", "n": 0}, result["out_of_sample"])

    def test_replay_blocks_missing_costs_future_information_overlap_and_bad_split(self):
        row = {
            "decision_at": "2020-01-02T00:00:00Z", "outcome_at": "2020-01-03T00:00:00Z",
            "source_id": "asset", "benchmark_source_id": "index", "trend_source_id": "trend",
            "snapshots": synthetic_snapshots("2020-01-02T00:00:00Z"),
            "information_inputs": [{"source_id": "record", "published_at": "2020-01-02T00:00:00Z", "observed_at": "2020-01-02T00:00:00Z"}],
            "asset_return": "0.1", "benchmark_return": "0.05", "trend_return": "0.08",
            "strategy_exposure": "1", "trend_exposure": "1",
        }
        kwargs = {"rule_id": "rule", "rule_revision": "b" * 40, "rule_frozen_at": "2020-01-01T00:00:00Z",
                  "fee_bps": 0, "slippage_bps": 0,
                  "sample_metadata": {"universe": "fixture", "selection_method": "fixed", "exclusions": "none", "survivorship_status": "ASSESSED"}}
        self.assertEqual("BLOCKED_MISSING_COSTS", evaluate_replay([row], **{**kwargs, "fee_bps": None})["status"])
        future = {**row, "information_inputs": [{"source_id": "future", "published_at": "2020-01-04T00:00:00Z", "observed_at": "2020-01-04T00:00:00Z"}]}
        with self.assertRaises(ReplayInputError):
            evaluate_replay([future], **kwargs)
        with self.assertRaises(ReplayInputError):
            evaluate_replay([row], **{**kwargs, "split_at": "2019-12-31T00:00:00Z"})
        overlapping = {**row, "decision_at": "2020-01-02T12:00:00Z", "outcome_at": "2020-01-04T00:00:00Z"}
        with self.assertRaisesRegex(ReplayInputError, "overlap"):
            evaluate_replay([row, overlapping], **kwargs)
        partial_event = {**row, "alert_triggered": True}
        with self.assertRaisesRegex(ReplayInputError, "supplied together"):
            evaluate_replay([partial_event], **kwargs)

    def test_sample_selection_and_rule_revision_are_explicit(self):
        row = {
            "decision_at": "2020-01-02T00:00:00Z", "outcome_at": "2020-01-03T00:00:00Z",
            "source_id": "asset", "benchmark_source_id": "index", "trend_source_id": "trend",
            "snapshots": synthetic_snapshots("2020-01-02T00:00:00Z"),
            "information_inputs": [], "asset_return": "0", "benchmark_return": "0", "trend_return": "0",
            "strategy_exposure": "0", "trend_exposure": "0",
        }
        kwargs = {"rule_id": "rule", "rule_revision": "mutable", "rule_frozen_at": "2020-01-01T00:00:00Z",
                  "fee_bps": 0, "slippage_bps": 0,
                  "sample_metadata": {"universe": "fixture", "selection_method": "fixed", "exclusions": "none", "survivorship_status": "ASSESSED"}}
        with self.assertRaises(ReplayInputError):
            evaluate_replay([row], **kwargs)
        with self.assertRaises(ReplayInputError):
            evaluate_replay([row], **{**kwargs, "rule_revision": "a" * 40,
                                      "sample_metadata": {**kwargs["sample_metadata"], "survivorship_status": "UNKNOWN"}})

    def test_missing_snapshot_blocks_entire_sample_without_metrics(self):
        row = {
            "decision_at": "2020-01-02T00:00:00Z", "outcome_at": "2020-01-03T00:00:00Z",
            "source_id": "asset", "benchmark_source_id": "index", "trend_source_id": "trend",
            "information_inputs": [], "asset_return": "0.10", "benchmark_return": "0.02", "trend_return": "0.03",
            "strategy_exposure": "1", "trend_exposure": "1",
        }
        kwargs = {"rule_id": "rule", "rule_revision": "b" * 40, "rule_frozen_at": "2020-01-01T00:00:00Z",
                  "fee_bps": 0, "slippage_bps": 0,
                  "sample_metadata": {"universe": "synthetic fixture", "selection_method": "fixed", "exclusions": "none", "survivorship_status": "KNOWN_LIMITATION"}}
        result = evaluate_replay([row], **kwargs)
        self.assertEqual({"status": "BLOCKED_MISSING_SNAPSHOT", "n": 1}, result)

    def test_future_dated_snapshot_is_rejected(self):
        row = {
            "decision_at": "2020-01-02T00:00:00Z", "outcome_at": "2020-01-03T00:00:00Z",
            "source_id": "asset", "benchmark_source_id": "index", "trend_source_id": "trend",
            "snapshots": synthetic_snapshots("2020-01-02T00:00:00Z"),
            "information_inputs": [], "asset_return": "0.10", "benchmark_return": "0.02", "trend_return": "0.03",
            "strategy_exposure": "1", "trend_exposure": "1",
        }
        row["snapshots"]["market"]["observed_at"] = "2020-01-04T00:00:00Z"
        kwargs = {"rule_id": "rule", "rule_revision": "b" * 40, "rule_frozen_at": "2020-01-01T00:00:00Z",
                  "fee_bps": 0, "slippage_bps": 0,
                  "sample_metadata": {"universe": "synthetic fixture", "selection_method": "fixed", "exclusions": "none", "survivorship_status": "KNOWN_LIMITATION"}}
        with self.assertRaisesRegex(ReplayInputError, "future-observed market snapshot"):
            evaluate_replay([row], **kwargs)


if __name__ == "__main__":
    unittest.main()
