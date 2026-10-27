import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.engine import ReplayInputError, net_return, summarize_returns, validate_information_set


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


if __name__ == "__main__":
    unittest.main()
