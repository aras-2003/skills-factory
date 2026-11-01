import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.engine import StructureInputError, analyze_structure


def bars(values):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [{"timestamp": (start + timedelta(days=i)).isoformat(),
             "published_at": (start + timedelta(days=i)).isoformat(),
            "open": close, "high": high, "low": low, "close": close, "volume": 100,
             "source_id": f"synthetic-{i}"}
            for i, (high, low, close) in enumerate(values)]


class TechnicalStructureTests(unittest.TestCase):
    def test_future_right_bars_are_required_to_confirm_pivot(self):
        data = bars([(10, 8, 9), (11, 8, 10), (14, 9, 11), (12, 9, 11), (11, 8, 10), (13, 9, 12), (11, 9, 10), (10, 8, 9)])
        result = analyze_structure(data, as_of=data[3]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD", left=1, right=2)
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual("FUTURE_DATED_BAR", result["reason"])

    def test_higher_highs_and_lows_produce_auditable_state_and_levels(self):
        data = bars([(10, 8, 9), (12, 9, 11), (11, 8.5, 10), (14, 10, 12), (12, 9, 11), (16, 11, 14), (14, 10, 12), (13, 11, 12)])
        result = analyze_structure(data, as_of=data[-1]["timestamp"], source_id="synthetic-series", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD", left=1, right=1)
        self.assertEqual("UPTREND", result["trend"])
        self.assertEqual(100, result["score"])
        self.assertFalse(result["score_is_probability"])
        self.assertEqual("16", result["ops"]["price"])
        self.assertEqual("10", result["opd"]["price"])

    def test_direction_score_is_symmetric_and_explainable(self):
        rising = [(10, 8, 9), (12, 9, 11), (11, 8.5, 10), (14, 10, 12), (12, 9, 11), (16, 11, 14), (14, 10, 12), (13, 11, 12)]
        bullish = analyze_structure(bars(rising), as_of="2026-01-08T00:00:00+00:00", source_id="synthetic-series", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD", left=1, right=1)
        self.assertEqual("UPTREND", bullish["trend"])
        self.assertEqual(100, bullish["score"])
        self.assertEqual({"higher_high": True, "higher_low": True, "lower_high": False, "lower_low": False}, bullish["score_components"])

        falling = [(30 - low, 30 - high, 30 - close) for high, low, close in rising]
        bearish = analyze_structure(bars(falling), as_of="2026-01-08T00:00:00+00:00", source_id="synthetic-series", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD", left=1, right=1)
        self.assertEqual("DOWNTREND", bearish["trend"])
        self.assertEqual(0, bearish["score"])
        self.assertEqual({"higher_high": False, "higher_low": False, "lower_high": True, "lower_low": True}, bearish["score_components"])

        mixed_values = [(10, 8, 9), (12, 9, 11), (11, 8.5, 10), (14, 10, 12), (12, 9, 11), (16, 11, 14), (14, 8, 12), (13, 11, 12)]
        mixed = analyze_structure(bars(mixed_values), as_of="2026-01-08T00:00:00+00:00", source_id="synthetic-series", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD", left=1, right=1)
        self.assertEqual("RANGE_OR_MIXED", mixed["trend"])
        self.assertEqual(50, mixed["score"])
        self.assertEqual({"higher_high": True, "higher_low": False, "lower_high": False, "lower_low": True}, mixed["score_components"])

    def test_synthetic_known_answer_confirms_pivots_only_after_right_bars(self):
        values = [(10, 8, 9), (12, 9, 11), (14, 10, 12), (12, 9, 10), (11, 8, 9),
                  (14, 10, 13), (16, 11, 15), (14, 10, 12), (13, 9, 11), (12, 10, 11), (12, 10, 11)]
        data = bars(values)
        for index, bar in enumerate(data):
            bar["source_id"] = f"SYNTHETIC-XYZ-{index}"

        result = analyze_structure(
            data,
            as_of="2026-01-11T00:00:00+00:00",
            source_id="SYNTHETIC-XYZ-DAILY-v1",
            adjusted=True,
            adjustment_id="synthetic-adjustment-v1", currency="USD",
        )

        self.assertEqual("OBSERVED", result["status"])
        self.assertEqual("USD", result["currency"])
        self.assertEqual("UPTREND", result["trend"])
        self.assertEqual(100, result["score"])
        self.assertFalse(result["score_is_probability"])
        self.assertEqual("16", result["ops"]["price"])
        self.assertEqual("2026-01-09T00:00:00+00:00", result["ops"]["confirmed_at"])
        self.assertEqual("SYNTHETIC-XYZ-6", result["ops"]["source_id"])
        self.assertEqual("45.45", result["ops"]["distance_pct"])
        self.assertEqual("9", result["opd"]["price"])
        self.assertEqual("2026-01-11T00:00:00+00:00", result["opd"]["confirmed_at"])
        self.assertEqual("SYNTHETIC-XYZ-8", result["opd"]["source_id"])
        self.assertEqual("-18.18", result["opd"]["distance_pct"])

    def test_requires_adjusted_prices_and_provenance(self):
        data = bars([(10, 8, 9)] * 8)
        self.assertEqual("UNKNOWN", analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=False, adjustment_id="none", currency="USD")["status"])

    def test_missing_currency_is_unknown(self):
        data = bars([(10, 8, 9)] * 8)
        result = analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1")
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual("MISSING_CURRENCY", result["reason"])

    def test_marks_future_publication_unknown(self):
        data = bars([(10, 8, 9)] * 8)
        data[2]["published_at"] = (datetime.fromisoformat(data[-1]["timestamp"]) + timedelta(days=1)).isoformat()
        result = analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD")
        self.assertEqual("FUTURE_DATED_BAR", result["reason"])

    def test_rejects_duplicate_timestamp_and_invalid_ohlc(self):
        data = bars([(10, 8, 9)] * 8)
        data[1]["timestamp"] = data[0]["timestamp"]
        with self.assertRaises(StructureInputError):
            analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD")
        data = bars([(10, 8, 9)] * 8)
        data[0]["high"] = 7
        with self.assertRaises(StructureInputError):
            analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD")

    def test_long_gaps_are_unknown_not_interpolated(self):
        data = bars([(10, 8, 9)] * 8)
        data[4]["timestamp"] = (datetime.fromisoformat(data[3]["timestamp"]) + timedelta(days=10)).isoformat()
        result = analyze_structure(data, as_of="2026-02-01T00:00:00+00:00", source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", currency="USD")
        self.assertEqual("DATA_GAP_EXCEEDS_LIMIT", result["reason"])


if __name__ == "__main__":
    unittest.main()
