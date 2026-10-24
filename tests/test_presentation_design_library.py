import importlib.util
import json
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]/"assets"/"design-library"
spec=importlib.util.spec_from_file_location("selector",BASE/"select_design.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class SelectionTests(unittest.TestCase):
    def test_board_prefers_executive(self):
        r=module.select({"audience":"board","purpose":"decision strategy","density":"high","medium":"pptx"})
        self.assertEqual(r["recommendations"][0]["style_id"],"executive-classic")
    def test_finance_prefers_analytical(self):
        r=module.select({"audience":"executive","purpose":"investment finance data","density":"high","medium":"pptx"})
        self.assertEqual(r["recommendations"][0]["style_id"],"analytical-modern")
    def test_learning_prefers_learning(self):
        r=module.select({"audience":"training","purpose":"learning workshop","density":"low","medium":"web"})
        self.assertEqual(r["recommendations"][0]["style_id"],"learning-clear")
    def test_explicit_brand(self):
        r=module.select({"audience":"board","purpose":"decision","density":"high","medium":"pptx","brand_style_id":"editorial-perspective"})
        self.assertEqual(len(r["recommendations"]),1)
    def test_unknown_brand_rejected(self):
        with self.assertRaises(ValueError):
            module.select({"medium":"pptx","brand_style_id":"missing"})
    def test_library_has_unique_ids_and_safe_rights(self):
        d=json.loads((BASE/"templates.json").read_text())
        self.assertEqual(len({s["id"] for s in d["styles"]}),len(d["styles"]))
        source=json.loads((BASE/"sources.json").read_text())
        self.assertTrue(all(s["rights_status"]!="cleared" for s in source["sources"]))
    def test_deterministic(self):
        b={"audience":"board","purpose":"decision","density":"medium","medium":"pdf"}
        self.assertEqual(module.select(b),module.select(b))

if __name__=="__main__": unittest.main()
