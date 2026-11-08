"""Synthetic regression fixtures for comparable peer and PEG semantics."""
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from peer_comparison import EconomicFitEvidence, EvidenceState, IssuerSnapshot, PeerMetric, compare_peer_set
from peer_growth_plot import render_peer_growth_plot
from tempfile import TemporaryDirectory
from pathlib import Path


AS_OF = "2026-08-01"
FIT_DIMENSIONS = ("value_chain_role", "revenue_profit_mix", "customer_base", "cyclicality", "capital_intensity")


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
    fit = {
        dimension: EconomicFitEvidence(
            alignment="MATCH", target_summary="synthetic target profile", peer_summary="synthetic peer profile",
            rationale="Synthetic reviewer note for deterministic helper behavior coverage.",
            target_published_at=as_of, target_source_url=f"https://issuer.example/TARGET/fit/{dimension}",
            published_at=as_of, source_url=f"https://issuer.example/{ticker}/fit/{dimension}",
        )
        for dimension in FIT_DIMENSIONS
    }
    return IssuerSnapshot(ticker=ticker, sector="Technology", industry="Semiconductors",
                          business_model=model, as_of=as_of, metrics=metrics,
                          comparison_group=f"Technology/Semiconductors/{model}",
                          inclusion_rationale="Synthetic fixture included by reviewed compute-product fit.",
                          peer_tier="DIRECT", economic_fit=fit)


class PeerComparisonTests(unittest.TestCase):
    def test_real_amd_ttm_snapshot_admits_three_economically_reviewed_direct_peers(self):
        """Dated reported TTM revenue and whole-company fit support a small AMD cohort.

        EV is the Nov 5, 2026 QDD snapshot. Revenue is GAAP reported TTM, rebuilt
        from company filings available by that date; periods end in Jul–Sep 2026
        and are explicitly aligned as the latest reported TTM. The result is a
        screen only, not a recommendation or rank.
        """
        as_of = "2026-11-05"
        target_url = "https://www.sec.gov/Archives/edgar/data/2488/000000248826000191/amd-20260926.htm"
        qdd = {
            "AMD": "https://www.qddresearch.com/us/amd/",
            "NVDA": "https://www.qddresearch.com/us/nvda/",
            "INTC": "https://www.qddresearch.com/us/intc/",
            "MRVL": "https://www.qddresearch.com/us/mrvl/",
        }
        filings = {
            "AMD": ("2026-11-04", target_url),
            "NVDA": ("2026-08-26", "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm"),
            "INTC": ("2026-10-30", "https://www.sec.gov/Archives/edgar/data/50863/000005086326000191/intc-20260926.htm"),
            "MRVL": ("2026-08-28", "https://www.sec.gov/Archives/edgar/data/1835632/000183563226000025/mrvl-20260801.htm"),
        }
        # Latest reported TTM revenue (USD millions): annual FY2025 + current
        # reported quarters − matching prior-year quarters, using issuer filings.
        ttm_components = {
            "AMD": (D("34639"), (D("10253"), D("11536"), D("13377")), (D("7438"), D("7685"), D("9246"))),
            "NVDA": (D("215938"), (D("81615"), D("96221")), (D("44062"), D("46743"))),
            "INTC": (D("52853"), (D("13577"), D("16128"), D("16500")), (D("12667"), D("12859"), D("13653"))),
            "MRVL": (D("8195"), (D("2418"), D("2739")), (D("1895"), D("2006"))),
        }
        ttm_sales = {
            ticker: annual + sum(current) - sum(prior)
            for ticker, (annual, current, prior) in ttm_components.items()
        }
        self.assertEqual(
            {"AMD": D("45436"), "NVDA": D("302969"), "INTC": D("59879"), "MRVL": D("9451")},
            ttm_sales,
        )
        enterprise_value = {"AMD": D("651500"), "NVDA": D("4310000"), "INTC": D("290500"), "MRVL": D("118300")}
        revenue_source_urls = {
            "AMD": (target_url, qdd["AMD"]),
            "NVDA": (filings["NVDA"][1], qdd["NVDA"]),
            "INTC": (filings["INTC"][1], "https://www.sec.gov/Archives/edgar/data/50863/000005086326000188/q326earningsrelease.htm", qdd["INTC"]),
            "MRVL": (filings["MRVL"][1], "https://investor.marvell.com/sec-filings/all-sec-filings/content/0001835632-26-000022/q227_8kx812026ex-991.htm", qdd["MRVL"]),
        }
        target_periods = {
            "AMD": "TTM through 2026-09-26",
            "NVDA": "TTM through 2026-07-26",
            "INTC": "TTM through 2026-09-26",
            "MRVL": "TTM through 2026-08-01",
        }

        def real_issuer(ticker, model, tier, rationale):
            metric = PeerMetric(
                name="ev_sales", value=enterprise_value[ticker] / ttm_sales[ticker], unit="multiple",
                definition="Enterprise value as of 2026-11-05 / latest reported GAAP TTM revenue",
                period=target_periods[ticker], basis="GAAP; USD millions; QDD enterprise value snapshot",
                published_at=as_of, source_url=qdd[ticker], currency="USD",
                period_alignment_group="latest reported TTM as of 2026-11-05",
                basis_group="GAAP reported revenue and same-date enterprise value",
                supporting_source_urls=revenue_source_urls[ticker],
            )
            fit = {}
            if ticker != "AMD":
                peer_date, peer_url = filings[ticker]
                for dimension in FIT_DIMENSIONS:
                    partial = dimension in {"revenue_profit_mix", "customer_base", "capital_intensity"}
                    fit[dimension] = EconomicFitEvidence(
                        alignment="PARTIAL" if partial else "MATCH",
                        target_summary="AMD combines data-center CPUs/GPUs with client/gaming and embedded processors.",
                        peer_summary={
                            "NVDA": "Accelerated compute, networking, gaming GPUs and software platform.",
                            "INTC": "Client and data-center CPU products plus integrated manufacturing and foundry.",
                            "MRVL": "Data-infrastructure semiconductors, custom ASICs, interconnect and storage controllers.",
                        }[ticker],
                        rationale=rationale,
                        target_published_at="2026-11-04", target_source_url=target_url,
                        published_at=peer_date, source_url=peer_url,
                    )
            return IssuerSnapshot(
                ticker=ticker, sector="Technology", industry="Semiconductors",
                business_model=model, as_of=as_of, metrics={"ev_sales": metric}, cyclical=True,
                comparison_group="Technology/Semiconductors/compute-and-data-infrastructure",
                inclusion_rationale=rationale, peer_tier=tier, economic_fit=fit,
            )

        target = real_issuer(
            "AMD", "fabless compute and AI semiconductors", "DIRECT",
            "Target issuer for a dated same-industry compute and data-infrastructure screen.",
        )
        peers = [
            real_issuer("NVDA", "accelerated compute platform", "DIRECT",
                        "Direct product-market overlap in data-center accelerated compute and GPUs; platform, software, and profitability mix are material caveats."),
            real_issuer("INTC", "integrated processor designer and manufacturer", "DIRECT",
                        "Direct CPU competition across client and data-center markets; foundry ownership and capital intensity differ materially."),
            real_issuer("MRVL", "data-infrastructure semiconductor designer", "DIRECT",
                        "Custom silicon and data-center connectivity overlap with AMD infrastructure markets; whole-company product and customer mix differ."),
        ]
        result = compare_peer_set(target, peers, as_of)
        self.assertEqual("COMPARABLE", result["status"])
        self.assertEqual(3, result["direct_peer_count"])
        self.assertEqual(3, result["core_metric_peer_counts"]["ev_sales"])
        self.assertIsNone(result["recommendation"])
        self.assertFalse(result["ranked"])
        self.assertTrue(result["cycle_normalization_required"])
        self.assertEqual(
            str(D("651500") / D("45436")),
            next(row for row in result["peers"] if row["ticker"] == "NVDA")["metrics"]["ev_sales"]["target_value"],
        )
        nvda_row = next(row for row in result["peers"] if row["ticker"] == "NVDA")
        self.assertEqual([target_url, qdd["AMD"]], nvda_row["metrics"]["ev_sales"]["target_supporting_source_urls"])
        self.assertEqual([filings["NVDA"][1], qdd["NVDA"]], nvda_row["metrics"]["ev_sales"]["supporting_source_urls"])

    def test_invalid_supporting_metric_source_is_not_meaningful(self):
        target = issuer("AMD")
        peers = [issuer("P1"), issuer("P2"), issuer("P3")]
        invalid_metric = replace(peers[0].metrics["ev_sales"], supporting_source_urls=("http://not-secure.example/source",))
        peers[0] = replace(peers[0], metrics={**peers[0].metrics, "ev_sales": invalid_metric})
        result = compare_peer_set(target, peers, AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("INVALID_SUPPORTING_SOURCE_URL", row["metrics"]["ev_sales"]["reason"])

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
            return IssuerSnapshot(
                ticker, sector, industry, model, as_of, {"ev_sales": sales_multiple},
                comparison_group="Technology/Semiconductors/compute-processors",
                inclusion_rationale="Diagnostic source candidate; review tier is explicit and period/model caveats remain visible.",
                peer_tier="DIRECT" if ticker == "NVDA" else "ADJACENT",
                economic_fit={
                    dimension: EconomicFitEvidence(
                        alignment="PARTIAL" if dimension in {"revenue_profit_mix", "customer_base"} else "MATCH",
                        target_summary="AMD fabless processor design and sales",
                        peer_summary="NVIDIA accelerated-compute platform, including data-center systems",
                        rationale="The filings support value-chain overlap; the broader NVIDIA platform and customer/profit mix remain explicit caveats.",
                        target_published_at="2026-11-03",
                        target_source_url="https://www.sec.gov/Archives/edgar/data/2488/000000248826000191/amd-20260926.htm",
                        published_at="2026-08-27",
                        source_url="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm",
                    ) for dimension in FIT_DIMENSIONS
                } if ticker == "NVDA" else {},
            )

        target = replace(snapshot("AMD"), comparison_group="Technology/Semiconductors/compute-processors")
        result = compare_peer_set(target, [snapshot(ticker) for ticker in ("MU", "MSFT", "NVDA", "AVGO", "MRVL")], as_of)
        by_ticker = {row["ticker"]: row for row in result["peers"]}
        self.assertEqual(D("8.2"), snapshot("AVGO").metrics["ev_sales"].value)
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertEqual(4, result["included_peer_count"])
        self.assertEqual(1, result["direct_peer_count"])
        self.assertEqual("SECTOR_OR_INDUSTRY_MISMATCH", by_ticker["MSFT"]["reason"])
        self.assertEqual("ADJACENT", by_ticker["MU"]["comparability_tier"])
        self.assertEqual("DIRECT", by_ticker["NVDA"]["comparability_tier"])
        self.assertEqual("ADJACENT", by_ticker["AVGO"]["comparability_tier"])
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertNotIn("AVGO", [point["ticker"] for point in result["plot"]["points"]])
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
        self.assertEqual("COMPARISON_GROUP_MISMATCH", row["reason"])
        self.assertTrue(row["ticker"].startswith("MU"))
        self.assertEqual(3, result["included_peer_count"])

    def test_reviewed_adjacent_business_model_can_join_table_without_peg_or_percentile(self):
        target = issuer("AMD", model="fabless compute")
        adjacent = replace(
            issuer("ACCELERATOR", model="AI accelerator designer"),
            comparison_group=target.comparison_group,
            peer_tier="ADJACENT",
            inclusion_rationale="Issuer filing confirms a fabless AI accelerator portfolio sold into the same data-center compute market; retain as adjacent segment reference, not a direct valuation peer.",
        )
        result = compare_peer_set(target, [issuer("P1"), issuer("P2"), adjacent], AS_OF)
        row = next(x for x in result["peers"] if x["ticker"] == "ACCELERATOR")
        self.assertEqual("INCLUDED", row["eligibility"])
        self.assertEqual("ADJACENT", row["comparability_tier"])
        self.assertIn("segment reference", row["inclusion_rationale"])
        self.assertEqual("N/M", row["metrics"]["peg"]["value"])
        self.assertEqual("BUSINESS_MODEL_MISMATCH", row["metrics"]["peg"]["reason"])
        self.assertEqual("N/M", row["metrics"]["ps_growth_heuristic"]["value"])
        # Adjacent observations remain visible in rows but never enter the
        # direct-peer summary statistics.
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertEqual(2, result["direct_peer_count"])
        self.assertEqual(2, result["metric_summaries"]["ev_sales"]["valid_peer_count"])
        self.assertFalse(result["ranked"])

    def test_missing_rationale_fails_closed_for_direct_or_adjacent_peers(self):
        target = issuer("AMD")
        peer = replace(issuer("P1"), inclusion_rationale="")
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(x for x in result["peers"] if x["ticker"] == "P1")
        self.assertEqual("EXCLUDED", row["eligibility"])
        self.assertEqual("MISSING_INCLUSION_RATIONALE", row["reason"])
        self.assertIsNotNone(row["exclusion_rationale"])

    def test_direct_peer_requires_source_backed_fit_across_all_five_dimensions(self):
        target = issuer("AMD")
        peer = replace(issuer("P1"), economic_fit={})
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("EXCLUDED", row["eligibility"])
        self.assertEqual("INCOMPLETE_DIRECT_FIT_EVIDENCE", row["reason"])
        self.assertEqual(2, result["direct_peer_count"])

    def test_direct_peer_with_unknown_or_mismatched_dimension_cannot_be_admitted(self):
        target = issuer("AMD")
        peer = issuer("P1")
        evidence = dict(peer.economic_fit)
        evidence["customer_base"] = replace(evidence["customer_base"], alignment="UNKNOWN")
        peer = replace(peer, economic_fit=evidence)
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("DIRECT_FIT_NOT_ESTABLISHED", row["reason"])
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])

    def test_partial_direct_fit_is_explicit_and_bound_into_snapshot(self):
        target = issuer("AMD")
        peer = issuer("P1")
        evidence = dict(peer.economic_fit)
        evidence["revenue_profit_mix"] = replace(
            evidence["revenue_profit_mix"], alignment="PARTIAL",
            rationale="The processor overlap is meaningful; data-center weighting differs and remains a valuation caveat.",
        )
        peer = replace(peer, economic_fit=evidence)
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("COMPARABLE", result["status"])
        self.assertEqual("PARTIAL", row["economic_fit"]["revenue_profit_mix"]["alignment"])
        self.assertNotEqual(result["plot"]["snapshot_id"], compare_peer_set(target, [issuer("P1"), issuer("P2"), issuer("P3")], AS_OF)["plot"]["snapshot_id"])

    def test_direct_fit_rejects_future_or_invalid_source(self):
        target = issuer("AMD")
        peer = issuer("P1")
        evidence = dict(peer.economic_fit)
        evidence["cyclicality"] = replace(evidence["cyclicality"], published_at="2026-08-02")
        peer = replace(peer, economic_fit=evidence)
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("INVALID_OR_LOOKAHEAD_DIRECT_FIT_SOURCE_DATE", row["reason"])

    def test_direct_fit_rejects_stale_source(self):
        target = issuer("AMD")
        peer = issuer("P1")
        evidence = dict(peer.economic_fit)
        evidence["cyclicality"] = replace(
            evidence["cyclicality"], target_published_at="2025-06-01", published_at="2025-06-01",
        )
        peer = replace(peer, economic_fit=evidence)
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("STALE_DIRECT_FIT_EVIDENCE", row["reason"])

    def test_explicit_reviewed_direct_peer_can_have_a_distinct_business_model_label(self):
        target = issuer("AMD", model="fabless compute")
        nvda = replace(issuer("NVDA", model="accelerated-compute platform"),
            comparison_group=target.comparison_group, peer_tier="DIRECT",
            inclusion_rationale="Issuer reports competing data-center accelerated-compute platforms; broader networking/software mix is disclosed as a valuation caveat.")
        peers = [nvda, replace(issuer("INTC"), comparison_group=target.comparison_group),
                 replace(issuer("QCOM"), comparison_group=target.comparison_group)]
        result = compare_peer_set(target, peers, AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "NVDA")
        self.assertEqual("INCLUDED", row["eligibility"])
        self.assertEqual("DIRECT", row["comparability_tier"])
        self.assertEqual("COMPARABLE", result["status"])

    def test_missing_or_invalid_reviewer_tier_fails_closed(self):
        target = issuer("AMD")
        peer = replace(issuer("P1"), peer_tier="")
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        row = next(item for item in result["peers"] if item["ticker"] == "P1")
        self.assertEqual("EXCLUDED", row["eligibility"])
        self.assertEqual("INVALID_COMPARABILITY_TIER", row["reason"])

    def test_reviewer_tier_is_bound_into_the_snapshot_identity(self):
        target = issuer("AMD")
        direct = issuer("PEER")
        adjacent = replace(direct, peer_tier="ADJACENT")
        direct_result = compare_peer_set(target, [direct, issuer("P2"), issuer("P3")], AS_OF)
        adjacent_result = compare_peer_set(target, [adjacent, issuer("P2"), issuer("P3")], AS_OF)
        self.assertNotEqual(direct_result["plot"]["snapshot_id"], adjacent_result["plot"]["snapshot_id"])
        direct_peer = next(row for row in direct_result["peers"] if row["ticker"] == "PEER")
        adjacent_peer = next(row for row in adjacent_result["peers"] if row["ticker"] == "PEER")
        self.assertNotEqual(direct_peer["comparability_tier"], adjacent_peer["comparability_tier"])

    def test_peer_count_alone_does_not_make_a_comparable_table(self):
        target = issuer("AMD")
        peers = []
        for ticker in ("P1", "P2", "P3"):
            peer = issuer(ticker)
            metrics = {name: replace(value, period="FY2024") for name, value in peer.metrics.items()}
            peers.append(replace(peer, metrics=metrics))
        result = compare_peer_set(target, peers, AS_OF)
        self.assertEqual(3, result["direct_peer_count"])
        self.assertEqual("INSUFFICIENT_COMPARABLE_PEERS", result["status"])
        self.assertEqual("NO_CORE_METRIC_HAS_THREE_COMPATIBLE_DIRECT_PEERS", result["comparability_reason"])

    def test_reviewed_alignment_group_allows_nearby_reporting_dates_and_local_currency_ratios(self):
        target = issuer("AMD", values={"revenue_growth": "0.443"})
        target_metrics = dict(target.metrics)
        target_metrics["revenue_growth"] = replace(
            target_metrics["revenue_growth"], period="9M ended 2026-09-26", basis="US GAAP",
            currency="USD", period_alignment_group="calendar-2026-9m",
            basis_group="reported-consolidated-GAAP-growth",
        )
        target = replace(target, metrics=target_metrics)
        peer = issuer("P1", values={"revenue_growth": "0.576"})
        peer_metrics = dict(peer.metrics)
        peer_metrics["revenue_growth"] = replace(
            peer_metrics["revenue_growth"], period="9M ended 2026-09-30", basis="China GAAP",
            currency="CNY", period_alignment_group="calendar-2026-9m",
            basis_group="reported-consolidated-GAAP-growth",
        )
        peer = replace(peer, metrics=peer_metrics)
        result = compare_peer_set(target, [peer, issuer("P2"), issuer("P3")], AS_OF)
        value = next(x for x in result["peers"] if x["ticker"] == "P1")["metrics"]["revenue_growth"]
        self.assertEqual("VERIFIED", value["status"])
        self.assertEqual("9M ended 2026-09-30", value["period"])
        self.assertEqual("9M ended 2026-09-26", value["target_period"])
        self.assertEqual("CNY", value["peer_currency"])
        self.assertEqual("USD", value["target_currency"])

    def test_reporting_period_and_basis_mismatches_without_reviewed_groups_are_nm(self):
        target = issuer("AMD", values={"revenue_growth": "0.443"})
        target_metrics = dict(target.metrics)
        target_metrics["revenue_growth"] = replace(
            target_metrics["revenue_growth"], period="9M ended 2026-09-26", basis="US GAAP", currency="USD"
        )
        target = replace(target, metrics=target_metrics)
        peer = issuer("P1", values={"revenue_growth": "0.576"})
        peer_metrics = dict(peer.metrics)
        peer_metrics["revenue_growth"] = replace(
            peer_metrics["revenue_growth"], period="9M ended 2026-09-30", basis="China GAAP", currency="CNY"
        )
        result = compare_peer_set(target, [replace(peer, metrics=peer_metrics), issuer("P2"), issuer("P3")], AS_OF)
        value = next(x for x in result["peers"] if x["ticker"] == "P1")["metrics"]["revenue_growth"]
        self.assertEqual("N/M", value["value"])
        self.assertEqual("INCOMPATIBLE_DEFINITION_PERIOD_BASIS_OR_HORIZON", value["reason"])

    def test_compatible_synthetic_amd_mu_peers_and_distinct_model_flag(self):
        target = issuer("AMD", model="fabless compute")
        peers = [issuer("P1"), issuer("P2"), issuer("P3"),
                 replace(issuer("MU", model="memory producer"), cyclical=True)]
        result = compare_peer_set(target, peers, AS_OF)
        mu = next(row for row in result["peers"] if row["ticker"] == "MU")
        self.assertEqual("EXCLUDED", mu["eligibility"])
        self.assertEqual("COMPARISON_GROUP_MISMATCH", mu["reason"])
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
        target_metrics = dict(target.metrics)
        target_metrics["forward_pe"] = replace(
            target_metrics["forward_pe"], supporting_source_urls=("https://issuer.example/target/price",)
        )
        target = replace(target, metrics=target_metrics)
        peer = issuer("P1")
        peer_metrics = dict(peer.metrics)
        peer_metrics["forward_pe"] = replace(
            peer_metrics["forward_pe"], supporting_source_urls=("https://issuer.example/p1/shares",)
        )
        result = compare_peer_set(target, [replace(peer, metrics=peer_metrics), issuer("P2"), issuer("P3")], AS_OF)
        self.assertTrue(result["cycle_normalization_required"])
        self.assertTrue(next(p for p in result["plot"]["points"] if p["ticker"] == "TARGET")["cycle_normalization_required"])
        with TemporaryDirectory() as tmp:
            rendered = render_peer_growth_plot(result, Path(tmp) / "peer.png")
            self.assertIn(rendered["status"], {"RENDERED_STATIC", "BLOCKED_RENDERER_UNAVAILABLE"})
            if rendered["status"] == "RENDERED_STATIC":
                self.assertTrue(Path(rendered["path"]).is_file())
                self.assertEqual(result["plot"]["snapshot_id"], rendered["snapshot_id"])
                self.assertIn("https://issuer.example/target/price", rendered["source_urls"])
                self.assertIn("https://issuer.example/p1/shares", rendered["source_urls"])

    def test_plot_blocks_when_table_has_no_compatible_peer_points(self):
        target = issuer("TARGET")
        result = compare_peer_set(target, [replace(issuer("P1"), industry="Different"), issuer("P2")], AS_OF)
        with TemporaryDirectory() as tmp:
            rendered = render_peer_growth_plot(result, Path(tmp) / "peer.png")
        self.assertEqual("BLOCKED_NO_COMPATIBLE_POINTS", rendered["status"])


if __name__ == "__main__":
    unittest.main()
