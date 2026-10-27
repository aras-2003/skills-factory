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
        result = analyze_structure(data, as_of=data[3]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1", left=1, right=2)
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual("FUTURE_DATED_BAR", result["reason"])

    def test_higher_highs_and_lows_produce_auditable_state_and_levels(self):
        data = bars([(10, 8, 9), (12, 9, 11), (11, 8.5, 10), (14, 10, 12), (12, 9, 11), (16, 11, 14), (14, 10, 12), (13, 11, 12)])
        result = analyze_structure(data, as_of=data[-1]["timestamp"], source_id="synthetic-series", adjusted=True, adjustment_id="synthetic-adjustment-v1", left=1, right=1)
        self.assertEqual("UPTREND", result["trend"])
        self.assertEqual(100, result["score"])
        self.assertFalse(result["score_is_probability"])
        self.assertEqual("16", result["ops"]["price"])
        self.assertEqual("10", result["opd"]["price"])

    def test_requires_adjusted_prices_and_provenance(self):
        data = bars([(10, 8, 9)] * 8)
        self.assertEqual("UNKNOWN", analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=False, adjustment_id="none")["status"])

    def test_marks_future_publication_unknown(self):
        data = bars([(10, 8, 9)] * 8)
        data[2]["published_at"] = (datetime.fromisoformat(data[-1]["timestamp"]) + timedelta(days=1)).isoformat()
        result = analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1")
        self.assertEqual("FUTURE_DATED_BAR", result["reason"])

    def test_rejects_duplicate_timestamp_and_invalid_ohlc(self):
        data = bars([(10, 8, 9)] * 8)
        data[1]["timestamp"] = data[0]["timestamp"]
        with self.assertRaises(StructureInputError):
            analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1")
        data = bars([(10, 8, 9)] * 8)
        data[0]["high"] = 7
        with self.assertRaises(StructureInputError):
            analyze_structure(data, as_of=data[-1]["timestamp"], source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1")

    def test_long_gaps_are_unknown_not_interpolated(self):
        data = bars([(10, 8, 9)] * 8)
        data[4]["timestamp"] = (datetime.fromisoformat(data[3]["timestamp"]) + timedelta(days=10)).isoformat()
        result = analyze_structure(data, as_of="2026-02-01T00:00:00+00:00", source_id="fixture", adjusted=True, adjustment_id="synthetic-adjustment-v1")
        self.assertEqual("DATA_GAP_EXCEEDS_LIMIT", result["reason"])


if __name__ == "__main__":
    unittest.main()
