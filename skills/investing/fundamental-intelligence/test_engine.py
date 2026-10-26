import unittest
from decimal import Decimal as D
from engine import Metric,Quality,compare,percentile,economic_spread
class Tests(unittest.TestCase):
    def setUp(self):
        self.a=Metric("pe","ttm",D(12),"multiple","2026-02-01","SEC",Quality.VERIFIED)
        self.b=Metric("pe","ttm",D(15),"multiple","2026-01-01","NYU",Quality.VERIFIED)
    def test_valid(self): self.assertEqual(compare(self.a,self.b,"2026-10-22")["delta"],"-3")
    def test_lookahead(self): self.assertEqual(compare(self.a,self.b,"2026-01-02")["reason"],"LOOKAHEAD")
    def test_mismatch(self):
        b=Metric("pe","forward",D(15),"multiple","2026-01-01","NYU",Quality.VERIFIED)
        self.assertEqual(compare(self.a,b,"2026-10-22")["status"],"BLOCKED")
    def test_missing(self):
        a=Metric("pe","ttm",None,"multiple","2026-02-01","SEC",Quality.VERIFIED)
        self.assertEqual(compare(a,self.b,"2026-10-22")["status"],"BLOCKED")
    def test_percentile(self):
        self.assertIsNone(percentile(D(1),[D(1)]))
        self.assertEqual(percentile(D(3),[D(i) for i in range(5)]),D("0.7"))
    def test_spread(self):
        a=Metric("roic","roic",D("0.2"),"fraction","2026-01-01","SEC",Quality.VERIFIED)
        b=Metric("wacc","wacc",D("0.1"),"fraction","2026-01-01","NYU",Quality.VERIFIED)
        self.assertEqual(economic_spread(a,b,"2026-10-22")["value"],"0.1")
    def test_invalid_dates_and_quality_fail_closed(self):
        from dataclasses import replace
        for metric in [replace(self.a,published_at="yesterday"), replace(self.a,published_at="2026-2-1"), replace(self.a,quality="UNKNOWN")]:
            self.assertEqual(compare(metric,self.b,"2026-10-22")["status"],"BLOCKED")
        self.assertEqual(compare(self.a,self.b,"tomorrow")["status"],"BLOCKED")

    def test_spread_cannot_subtract_unrelated_metrics(self):
        from dataclasses import replace
        a=replace(self.a,unit="fraction")
        b=replace(self.b,unit="fraction")
        self.assertEqual(economic_spread(a,b,"2026-10-22")["status"],"BLOCKED")
if __name__=="__main__": unittest.main()
