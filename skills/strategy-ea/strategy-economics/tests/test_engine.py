from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

MODULE=Path(__file__).resolve().parents[1]/"engine.py"
spec=importlib.util.spec_from_file_location("strategy_economics",MODULE); model=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(model)

def ev(value,source): return {"value":str(value),"source_id":source,"published_at":"2026-01-01"}

def fixture():
    return {"as_of":"2026-01-31","currency":"USD","profit_pools":[{"entity":"A","revenue":ev(100,"ra"),"operating_profit":ev(20,"pa")},{"entity":"B","revenue":ev(200,"rb"),"operating_profit":ev(30,"pb")}],"pvm":[{"id":"a","prior_price":ev(10,"p0a"),"current_price":ev(11,"p1a"),"prior_volume":ev(10,"v0a"),"current_volume":ev(12,"v1a")},{"id":"b","prior_price":ev(20,"p0b"),"current_price":ev(22,"p1b"),"prior_volume":ev(10,"v0b"),"current_volume":ev(8,"v1b")}],"driver_tree":{"reported_value":ev(30,"parent"),"operation":"sum","children":[{"reported_value":ev(10,"child1")},{"reported_value":ev(20,"child2")}]},"cost_bridge":[{"id":"labor","baseline":ev(40,"cb"),"actual":ev(45,"ca")} ]}

class StrategyEconomicsTests(unittest.TestCase):
    def test_profit_pool_and_pvm_reconcile(self):
        out=model.calculate(fixture()); self.assertEqual("300",out["profit_pool"]["total_revenue"]); self.assertEqual("50",out["profit_pool"]["total_operating_profit"]); self.assertEqual("8",out["pvm"]["change"]); self.assertEqual("-20.0",out["pvm"]["mix_effect"]); self.assertEqual("28",out["pvm"]["price_effect"]); self.assertTrue(out["pvm"]["reconciles"])
    def test_driver_tree_must_reconcile(self):
        data=fixture(); data["driver_tree"]["children"][0]["reported_value"]["value"]="11"
        with self.assertRaises(model.InputError): model.calculate(data)
    def test_future_evidence_and_missing_source_are_rejected(self):
        data=fixture(); data["profit_pools"][0]["revenue"]["published_at"]="2026-02-01"
        with self.assertRaises(model.InputError): model.calculate(data)
        data=fixture(); del data["pvm"][0]["current_price"]["source_id"]
        with self.assertRaises(model.InputError): model.calculate(data)
    def test_zero_base_or_current_volume_is_rejected(self):
        data=fixture(); data["pvm"][0]["prior_volume"]["value"]="0"; data["pvm"][1]["prior_volume"]["value"]="0"
        with self.assertRaises(model.InputError): model.calculate(data)

if __name__=="__main__": unittest.main()
