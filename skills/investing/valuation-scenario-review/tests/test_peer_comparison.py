"""Synthetic regression fixtures for comparable peer and PEG semantics."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from peer_comparison import EvidenceState, IssuerSnapshot, PeerMetric, compare_peer_set
from peer_growth_plot import render_peer_growth_plot
from tempfile import TemporaryDirectory
from pathlib import Path


AS_OF = "2026-08-01"


def metric(name, value, *, published="2026-07-01", definition=None, period=None,
           basis="GAAP", horizon="", unit=None, status=EvidenceState.VERIFIED):
    defaults = {
        "ev_sales": ("EV / trailing twelve-month revenue", "TTM FY2025", "multiple", ""),
        "ev_ebitda": ("EV / EBITDA reconciled to GAAP", "FY2025", "multiple", ""),
        "forward_pe": ("Price / next-twelve-month diluted GAAP EPS", "NTM FY2026", "multiple", "12M"),
        "eps_cagr": ("Diluted GAAP EPS CAGR", "FY2026–FY2030", "fraction", "5Y"),
        "revenue_growth": ("Revenue CAGR", "FY2022–FY2025", "fraction", "3Y"),
        "fcf_yield": ("FCF / market capitalization", "TTM FY2025", "fraction", ""),
        "roic": ("NOPAT / average invested capital", "FY2025", "fraction", ""),
        "price_sales": ("Price / trailing twelve-month revenue", "TTM FY2025", "multiple", ""),
        "eps_revision_90d": ("Consensus diluted EPS estimate revision over prior 90 days", "90D", "fraction", "90D"),
    }
    default_definition, default_period, default_unit, default_horizon = defaults[name]
    return PeerMetric(
        name=name, value=D(str(value)) if value is not None else None,
        unit=unit or default_unit, definition=definition or default_definition,
        period=period or default_period, basis=basis, published_at=published,
        source_url=f"https://issuer.example/filings/{name}", status=status,
        horizon=horizon or default_horizon, currency="USD",
    )


def issuer(ticker, *, model="fabless compute", as_of=AS_OF, values=None):
    values = values or {"ev_sales": "5", "ev_ebitda": "20", "forward_pe": "20", "eps_cagr": "0.20", "revenue_growth": "0.15", "fcf_yield": "0.02", "roic": "0.18"}
    metrics = {name: metric(name, value) for name, value in values.items()}
    return IssuerSnapshot(ticker=ticker, sector="Technology", industry="Semiconductors",
                          business_model=model, as_of=as_of, metrics=metrics)


class PeerComparisonTests(unittest.TestCase):
    def test_real_qdd_fy2027_snapshot_keeps_adjacent_models_out_of_amd_cohort(self):
        """Public consensus observations are not peer evidence without model and period fit."""
        as_of = "2026-11-05"
        source_urls = {
            "AMD": "https://www.qddresearch.com/us/amd/",
            "MU": "https://www.qddresearch.com/us/mu/",
            "MSFT": "https://www.qddresearch.com/us/msft/",
            "NVDA": "https://www.qddresearch.com/us/nvda/",
            "AVGO": "https://www.qddresearch.com/us/avgo/",
            "MRVL": "https://www.qddresearch.com/us/mrvl/",
        }
        observations = {
            "AMD": ("fabless high-performance compute", "Technology", "Semiconductors", "6.8", "FY2027 ending 2027-12-31"),
            "MU": ("integrated memory", "Technology", "Semiconductors", "2.6", "FY2027 ending 2027-08-31"),
            "MSFT": ("cloud software services", "Technology", "Software", "10.2", "FY2027 ending 2027-06-30"),
            "NVDA": ("accelerated compute platform", "Technology", "Semiconductors", "10.5", "FY2027 ending 2027-01-31"),
            "AVGO": ("custom silicon and infrastructure software", "Technology", "Semiconductors", "8.2", "FY2027 ending 2027-10-31"),
            "MRVL": ("data infrastructure semiconductors", "Technology", "Semiconductors", "9.8", "FY2027 ending 2027-01-31"),
        }

        def snapshot(ticker):
            model, sector, industry, value, period = observations[ticker]
            sales_multiple = PeerMetric(
                name="ev_sales", value=D(value), unit="multiple",
                definition="Enterprise value / QDD consensus mean estimated FY2027 sales",
                period=period, basis="QDD consensus estimate; vendor-reported EV/Sales",
                published_at=as_of, source_url=source_urls[ticker], currency="USD",
            )
            return IssuerSnapshot(ticker, sector, industry, model, as_of, {"ev_sales": sales_multiple})

        result = compare_peer_set(snapshot("AMD"), [snapshot(ticker) for ticker in ("MU", "MSFT", "NVDA", "AVGO", "MRVL")], as_of)
        by_ticker = {row["ticker"]: row for row in result["peers"]}
        self.assertEqual(D("8.2"), snapshot("AVGO").metrics["ev_sales"].value)
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertEqual(0, result["included_peer_count"])
        self.assertEqual("SECTOR_OR_INDUSTRY_MISMATCH", by_ticker["MSFT"]["reason"])
        for ticker in ("MU", "NVDA", "AVGO", "MRVL"):
            self.assertEqual("BUSINESS_MODEL_MISMATCH", by_ticker[ticker]["reason"])
        self.assertEqual({}, by_ticker["AVGO"]["metrics"])
        self.assertEqual([], result["plot"]["points"])
        self.assertFalse(result["ranked"])
        self.assertIsNone(result["recommendation"])

    def test_three_comparable_peers_make_a_table_but_no_small_sample_percentile(self):
        target = issuer("AMD-LIKE")
        peers = [issuer("PEER-A", values={"ev_sales": "4", "ev_ebitda": "18", "forward_pe": "18", "eps_cagr": "0.18"}),
                 issuer("PEER-B", values={"ev_sales": "6", "ev_ebitda": "22", "forward_pe": "24", "eps_cagr": "0.24"}),
                 issuer("PEER-C", values={"ev_sales": "5", "ev_ebitda": "20", "forward_pe": "20", "eps_cagr": "0.20"})]
        result = compare_peer_set(target, peers, AS_OF)
        repeated = compare_peer_set(target, peers, AS_OF)
        self.assertEqual("COMPARABLE", result["status"])
        self.assertEqual(3, result["included_peer_count"])
        self.assertNotIn("target_percentile", result["metric_summaries"]["ev_sales"])
        self.assertIn("at least five", result["metric_summaries"]["ev_sales"]["percentile_status"])
        self.assertIsNone(result["recommendation"])
        self.assertFalse(result["ranked"])

    def test_different_business_model_is_visible_but_excluded(self):
        target = issuer("AMD-LIKE", model="fabless compute")
        peers = [issuer("A1"), issuer("A2"), issuer("A3"), replace(issuer("MU-LIKE", model="integrated memory"), cyclical=True)]
        result = compare_peer_set(target, peers, AS_OF)
        row = next(x for x in result["peers"] if x["ticker"] == "MU-LIKE")
        self.assertEqual("EXCLUDED", row["eligibility"])
        self.assertEqual("BUSINESS_MODEL_MISMATCH", row["reason"])
        self.assertTrue(row["ticker"].startswith("MU"))
        self.assertEqual(3, result["included_peer_count"])

    def test_compatible_synthetic_amd_mu_peers_and_distinct_model_flag(self):
        target = issuer("AMD", model="fabless compute")
        peers = [issuer("P1"), issuer("P2"), issuer("P3"),
                 replace(issuer("MU", model="memory producer"), cyclical=True)]
        result = compare_peer_set(target, peers, AS_OF)
        mu = next(row for row in result["peers"] if row["ticker"] == "MU")
        self.assertEqual("EXCLUDED", mu["eligibility"])
        self.assertEqual("BUSINESS_MODEL_MISMATCH", mu["reason"])
        self.assertTrue(result["plot"]["points"])

    def test_industry_mismatch_and_different_as_of_are_explicit(self):
        target = issuer("TARGET")
        peers = [issuer("A1"), issuer("A2"), issuer("A3"),
                 replace(issuer("SAAS"), industry="Application Software"),
                 replace(issuer("OLD"), as_of="2026-07-31")]
        result = compare_peer_set(target, peers, AS_OF)
        by_ticker = {x["ticker"]: x for x in result["peers"]}
        self.assertEqual("SECTOR_OR_INDUSTRY_MISMATCH", by_ticker["SAAS"]["reason"])
        self.assertEqual("AS_OF_MISMATCH", by_ticker["OLD"]["reason"])

    def test_forward_pe_and_eps_growth_produce_peg_one_with_same_source_snapshot(self):
        target = issuer("TARGET")
        peers = [issuer("P1", values={"forward_pe": "20", "eps_cagr": "0.20"}), issuer("P2"), issuer("P3")]
        result = compare_peer_set(target, peers, AS_OF)
        repeated = compare_peer_set(target, peers, AS_OF)
        p1 = next(x for x in result["peers"] if x["ticker"] == "P1")
        self.assertEqual("1", p1["metrics"]["peg"]["value"])
        self.assertEqual("1", result["peg_reference"]["value"])
        self.assertTrue(result["plot"]["same_input_as_table"])
        self.assertEqual(result["plot"]["snapshot_id"], repeated["plot"]["snapshot_id"])
        point = next(p for p in result["plot"]["points"] if p["ticker"] == "P1")
        self.assertEqual("20.00", point["eps_growth_pct"])
        self.assertEqual("20", point["forward_pe"])
        self.assertEqual("1", point["peg"])

    def test_missing_stale_future_or_negative_eps_never_becomes_cheap_peg(self):
        target = issuer("TARGET")
        good = issuer("GOOD")
        negative = issuer("NEGATIVE", values={"forward_pe": "20", "eps_cagr": "-0.1"})
        stale = issuer("STALE")
        stale_metrics = dict(stale.metrics)
        stale_metrics["eps_cagr"] = replace(stale_metrics["eps_cagr"], published_at="2026-01-01")
        stale = replace(stale, metrics=stale_metrics)
        future = issuer("FUTURE")
        future_metrics = dict(future.metrics)
        future_metrics["forward_pe"] = replace(future_metrics["forward_pe"], published_at="2026-08-02")
        future = replace(future, metrics=future_metrics)
        result = compare_peer_set(target, [good, issuer("P2"), issuer("P3"), negative, stale, future], AS_OF)
        by_ticker = {x["ticker"]: x for x in result["peers"]}
        self.assertEqual("N/M", by_ticker["NEGATIVE"]["metrics"]["peg"]["value"])
        self.assertEqual("NONPOSITIVE_EPS_GROWTH", by_ticker["NEGATIVE"]["metrics"]["peg"]["reason"])
        self.assertEqual("STALE_FORWARD_OR_REVISION_DATA", by_ticker["STALE"]["metrics"]["eps_cagr"]["reason"])
        self.assertEqual("LOOKAHEAD", by_ticker["FUTURE"]["metrics"]["forward_pe"]["reason"])
        self.assertNotIn("STALE", [p["ticker"] for p in result["plot"]["points"]])
        self.assertNotIn("FUTURE", [p["ticker"] for p in result["plot"]["points"]])

    def test_metric_definition_period_basis_or_horizon_mismatch_is_nm(self):
        target = issuer("TARGET")
        incompatible = issuer("BAD")
        metrics = dict(incompatible.metrics)
        metrics["ev_ebitda"] = replace(metrics["ev_ebitda"], definition="EV / adjusted EBITDA", basis="Adjusted, SBC excluded")
        metrics["forward_pe"] = replace(metrics["forward_pe"], horizon="6M")
        incompatible = replace(incompatible, metrics=metrics)
        result = compare_peer_set(target, [issuer("P1"), issuer("P2"), incompatible], AS_OF)
        row = next(x for x in result["peers"] if x["ticker"] == "BAD")
        self.assertEqual("N/M", row["metrics"]["ev_ebitda"]["value"])
        self.assertEqual("INCOMPATIBLE_DEFINITION_PERIOD_BASIS_OR_HORIZON", row["metrics"]["ev_ebitda"]["reason"])
        self.assertEqual("Adjusted, SBC excluded", row["metrics"]["ev_ebitda"]["peer_basis"])
        self.assertEqual("INCOMPATIBLE_FORWARD_PE_HORIZON", row["metrics"]["forward_pe"]["reason"])

    def test_five_valid_peer_observations_allow_descriptive_percentile_and_keep_outlier(self):
        target = issuer("TARGET")
        peers = [issuer(f"P{i}", values={"ev_sales": "1000" if i == 5 else str(i + 2)}) for i in range(1, 6)]
        result = compare_peer_set(target, peers, AS_OF)
        summary = result["metric_summaries"]["ev_sales"]
        self.assertEqual(5, summary["valid_peer_count"])
        self.assertEqual("1000", next(p for p in result["peers"] if p["ticker"] == "P5")["metrics"]["ev_sales"]["value"])
        self.assertEqual("0.5", summary["target_percentile"])
        self.assertFalse(result["cross_sector_ranking"])

    def test_peg_percentile_uses_target_and_peer_calculation_from_same_definitions(self):
        target = issuer("TARGET")
        peers = [issuer(f"P{i}") for i in range(1, 6)]
        result = compare_peer_set(target, peers, AS_OF)
        repeated = compare_peer_set(target, peers, AS_OF)
        self.assertEqual("0.5", result["metric_summaries"]["peg"]["target_percentile"])
        self.assertEqual(result["plot"]["snapshot_id"], repeated["plot"]["snapshot_id"])

    def test_ps_growth_is_optional_descriptive_only_and_requires_positive_growth(self):
        values = {"price_sales": "4", "revenue_growth": "0.20"}
        target = issuer("TARGET", values=values)
        peer = issuer("P1", values=values)
        result = compare_peer_set(target, [peer, issuer("P2", values=values), issuer("P3", values=values)], AS_OF)
        p1 = next(row for row in result["peers"] if row["ticker"] == "P1")
        heuristic = p1["metrics"]["ps_growth_heuristic"]
        self.assertEqual("0.2", heuristic["value"])
        self.assertFalse(heuristic["primary_rank"])
        self.assertIsNone(heuristic["recommendation"])
        self.assertNotIn("ps_growth_heuristic", result["metric_summaries"])

        negative = issuer("NEG", values={"price_sales": "4", "revenue_growth": "-0.1"})
        result = compare_peer_set(target, [peer, issuer("P2", values=values), negative], AS_OF)
        neg = next(row for row in result["peers"] if row["ticker"] == "NEG")
        self.assertEqual("N/M", neg["metrics"]["ps_growth_heuristic"]["value"])
        self.assertEqual("NONPOSITIVE_REVENUE_GROWTH", neg["metrics"]["ps_growth_heuristic"]["reason"])

    def test_stale_estimate_revision_is_nm(self):
        target = issuer("TARGET", values={"eps_revision_90d": "0.10"})
        peer = issuer("P1", values={"eps_revision_90d": "0.15"})
        old_metrics = dict(peer.metrics)
        old_metrics["eps_revision_90d"] = replace(old_metrics["eps_revision_90d"], published_at="2026-01-01")
        peer = replace(peer, metrics=old_metrics)
        result = compare_peer_set(target, [peer, issuer("P2", values={"eps_revision_90d": "0.12"}), issuer("P3", values={"eps_revision_90d": "0.08"})], AS_OF)
        p1 = next(row for row in result["peers"] if row["ticker"] == "P1")
        self.assertEqual("N/M", p1["metrics"]["eps_revision_90d"]["value"])
        self.assertEqual("STALE_FORWARD_OR_REVISION_DATA", p1["metrics"]["eps_revision_90d"]["reason"])

    def test_duplicate_issuer_or_invalid_target_snapshot_is_rejected(self):
        target = issuer("TARGET")
        duplicate = compare_peer_set(target, [issuer("P1"), issuer("P1")], AS_OF)
        self.assertEqual("DUPLICATE_OR_TARGET_PEER", duplicate["reason"])
        bad_date = compare_peer_set(replace(target, as_of="2026-07-31"), [issuer("P1")], AS_OF)
        self.assertEqual("INVALID_TARGET_SNAPSHOT_OR_PEER_COUNT", bad_date["reason"])

    def test_cycle_flag_survives_into_snapshot_and_plot_uses_same_data(self):
        target = replace(issuer("TARGET"), cyclical=True)
        result = compare_peer_set(target, [issuer("P1"), issuer("P2"), issuer("P3")], AS_OF)
        self.assertTrue(result["cycle_normalization_required"])
        self.assertTrue(next(p for p in result["plot"]["points"] if p["ticker"] == "TARGET")["cycle_normalization_required"])
        with TemporaryDirectory() as tmp:
            rendered = render_peer_growth_plot(result, Path(tmp) / "peer.png")
            self.assertIn(rendered["status"], {"RENDERED_STATIC", "BLOCKED_RENDERER_UNAVAILABLE"})
            if rendered["status"] == "RENDERED_STATIC":
                self.assertTrue(Path(rendered["path"]).is_file())
                self.assertEqual(result["plot"]["snapshot_id"], rendered["snapshot_id"])

    def test_plot_blocks_when_table_has_no_compatible_peer_points(self):
        target = issuer("TARGET")
        result = compare_peer_set(target, [replace(issuer("P1"), industry="Different"), issuer("P2")], AS_OF)
        with TemporaryDirectory() as tmp:
            rendered = render_peer_growth_plot(result, Path(tmp) / "peer.png")
        self.assertEqual("BLOCKED_NO_COMPATIBLE_POINTS", rendered["status"])


if __name__ == "__main__":
    unittest.main()
