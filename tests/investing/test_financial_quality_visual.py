import importlib.util
import sys
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "scripts/investing/financial_quality_visual.py"
spec = importlib.util.spec_from_file_location("financial_quality_visual", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FinancialVisualTests(unittest.TestCase):
    def test_renders_verified_trends(self):
        obs = [{"period": str(y), "metrics": {"gross_margin": 0.4+i*.02, "fcf_margin": None}}
               for i,y in enumerate((2023,2024,2025))]
        result = mod.render_quality_trends_svg(obs, company="<Test>")
        self.assertIn("&lt;Test&gt;", result)
        self.assertIn("Gross margin", result)
        self.assertIn("no data", result)
        self.assertNotIn("<Test>", result)

    def test_rejects_short_history(self):
        with self.assertRaises(ValueError):
            mod.render_quality_trends_svg([{"period":"2025", "metrics":{}}])

    def test_missing_period_not_connected(self):
        data = [{"period":str(y),"metrics":{"gross_margin":m}} for y,m in [(2023,.3),(2024,None),(2025,.5)]]
        svg = mod.render_quality_trends_svg(data)
        self.assertNotIn("<polyline",svg)


if __name__ == "__main__":
    unittest.main()
