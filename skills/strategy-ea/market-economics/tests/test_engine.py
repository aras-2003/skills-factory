from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "engine.py"
spec = importlib.util.spec_from_file_location("market_economics", MODULE)
model = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(model)

def ev(value, source, published="2026-01-01"):
    return {"value": str(value), "source_id": source, "published_at": published}

def fixture():
    return {"as_of":"2026-01-31", "currency":"USD", "top_down":ev(1000,"top"), "bottom_up":ev(1200,"bottom"), "currently_served":ev(20,"served"), "segments":[{"id":"smb","annual_spend":ev(100,"spend"),"serviceable_share":ev("0.5","fit"),"attainable_share":ev("0.2","capture")},{"id":"enterprise","annual_spend":ev(200,"spend2"),"serviceable_share":ev("0.25","fit2"),"attainable_share":ev("0.1","capture2")}]}

class MarketEconomicsTests(unittest.TestCase):
    def test_sizing_and_whitespace_known_answer(self):
        result=model.calculate(fixture())
        self.assertEqual("1200",result["bottom_up_tam"])
        self.assertEqual("100.00",result["segment_derived_sam"])
        self.assertEqual("80.00",result["uncovered_serviceable_value"])
        self.assertIsNone(result["validated_white_space"])
        self.assertEqual("200",result["tam_difference"])
    def test_whitespace_requires_separate_unmet_demand_evidence(self):
        data=fixture(); data["validated_unmet_demand"]=ev(30,"unmet-demand")
        result=model.calculate(data)
        self.assertEqual("30",result["validated_white_space"])
        self.assertEqual("unmet-demand",result["white_space_evidence"]["source_id"])
        data["validated_unmet_demand"]=ev(81,"unmet-demand")
        with self.assertRaises(model.InputError): model.calculate(data)
    def test_source_missing_or_future_is_rejected(self):
        data=fixture(); del data["top_down"]["source_id"]
        with self.assertRaises(model.InputError): model.calculate(data)
        data=fixture(); data["top_down"]["published_at"]="2026-02-01"
        with self.assertRaises(model.InputError): model.calculate(data)
    def test_invalid_share_or_overserved_market_is_rejected(self):
        data=fixture(); data["segments"][0]["serviceable_share"]["value"]="1.1"
        with self.assertRaises(model.InputError): model.calculate(data)
        data=fixture(); data["currently_served"]["value"]="101"
        with self.assertRaises(model.InputError): model.calculate(data)
    def test_duplicate_segment_ids_are_rejected(self):
        data=fixture(); data["segments"][1]["id"]="smb"
        with self.assertRaises(model.InputError): model.calculate(data)

if __name__ == "__main__": unittest.main()
