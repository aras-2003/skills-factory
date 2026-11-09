from __future__ import annotations

from pathlib import Path
from decimal import Decimal
import hashlib
import json
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts" / "eval") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "eval"))

from campaign import separately_validated_iteration07_investing_quality_paths

peer_script = ROOT / "skills" / "investing" / "valuation-scenario-review" / "scripts"
if str(peer_script) not in sys.path:
    sys.path.insert(0, str(peer_script))
from peer_comparison import EconomicFitEvidence, IssuerSnapshot, PeerMetric, compare_peer_set


class Iteration07InvestingQualityCoverageTests(unittest.TestCase):
    def test_candidate_hashes_and_behavior_paths_are_exactly_bound(self):
        expected = {
            "skills/investing/security-underwriting/SKILL.md",
            "skills/investing/security-underwriting/scripts/financial_quality.py",
            "skills/investing/security-underwriting/scripts/value_trap_gate.py",
            "skills/investing/valuation-scenario-review/scripts/peer_comparison.py",
            "skills/investing/valuation-scenario-review/scripts/peer_growth_plot.py",
            "skills/investing/valuation-scenario-review/SKILL.md",
            "skills/investing/valuation-scenario-review/scripts/valuation_scenarios.py",
            "skills/investing/thesis-challenge/SKILL.md",
            "workflows/investment-security-review/WORKFLOW.md",
            "workflows/runtime-registry.yaml",
            "docs/audits/investing-domain-audit-iteration-07-2026-11.md",
            "docs/governance/iterations/iteration-07-investing-quality-2026-11.md",
            "CATALOG.md",
            "docs/catalog.json",
            "scripts/eval/campaign.py",
            "adapters/skills-factory-cloud-next/src/peer-comparability.ts",
            "adapters/skills-factory-cloud-next/src/cloud-tools.ts",
            "adapters/skills-factory-cloud-next/src/mcp-handler.ts",
            "runtime/mcp/server.py",
            "runtime/mcp/cloud_server.py",
            "scripts/package/build_utils.py",
        }
        self.assertEqual(expected, separately_validated_iteration07_investing_quality_paths(ROOT))

    def test_behavior_suite_binds_runtime_evidence_and_acceptance_disposition(self):
        cfg = yaml.safe_load((ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml").read_text())
        cases = yaml.safe_load((ROOT / cfg["behavior_case_suite"]).read_text())
        self.assertEqual(set(cfg["required_case_ids"]), {item["id"] for item in cases["cases"]})
        self.assertEqual({231, 306, 307, 318}, {item["expected_issue"] for item in cases["cases"]})
        self.assertEqual("PASS", cfg["runtime_status"])
        self.assertEqual("89c28bf70353b4568c7bc031e128a5f57a0fe24d", cfg["candidate_source_revision"])
        self.assertEqual("merged_to_main", cfg["candidate_source_revision_status"])
        self.assertEqual("89c28bf70353b4568c7bc031e128a5f57a0fe24d", cfg["runtime_canonical_source_revision"])
        self.assertEqual("967ee59cfa5364be118d7521e8dfdbba4da7cfae", cfg["runtime_source_revision"])
        self.assertEqual("1.38.472+89c28bf70353", cfg["runtime_release_id"])
        self.assertEqual(125, cfg["runtime_site_version"])
        self.assertTrue((ROOT / cfg["runtime_evidence"]).is_file())
        self.assertEqual([], cfg["runtime_blockers"])
        self.assertIn("Comparator limitations are documented", cfg["status_note"])
        runtime_evidence = (ROOT / cfg["runtime_evidence"]).read_text(encoding="utf-8")
        self.assertIn("Exact Site v121 USER_SUPPLIED_CONTEXT execution", runtime_evidence)
        self.assertIn("NOT_SCORED", runtime_evidence)
        self.assertIn("client_display=NOT_OBSERVABLE", runtime_evidence)
        self.assertIs(cfg["release_approved"], False)
        self.assertIs(cfg["historical_r20_immutable"], True)

    def test_exact_runtime_receipts_document_success_and_preserve_source_limitations(self):
        evidence = (ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/runtime-evidence.md").read_text()
        self.assertIn("2026-11-09T16:37:24.680Z", evidence)
        self.assertIn("8daeb9a11e5410562a7e85dfecb62a3557b58032ffb77c35e2d8b9d5e2b1e265", evidence)
        self.assertIn("2026-11-09T16:37:34.684Z", evidence)
        self.assertIn("01f57702b5e416875ce0d7ecf3e4522a245a4fcd36da18acf1f182ce9216c231", evidence)
        self.assertIn("Neither path independently retrieves or authenticates", evidence)
        self.assertIn("forward P/E", evidence)
        self.assertIn("90-day EPS revisions", evidence)

    def test_supplemental_routing_regressions_are_registered(self):
        cfg = yaml.safe_load((ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml").read_text())
        registry = yaml.safe_load((ROOT / cfg["supplemental_routing_registry"]).read_text())
        registered = {item["id"] for item in registry["cases"]}
        required = set(cfg["supplemental_routing_case_ids"])
        self.assertTrue(required.issubset(registered))
        self.assertTrue({"investment-top-two-screen-pl", "investment-top-twenty-screen-en",
                         "investment-acronym-vat-pl", "investment-acronym-pit-pl",
                         "investment-acronym-nasa-en"}.issubset(required))
        self.assertIn("investment-security-sizing-natural-pl", required)
        base = yaml.safe_load((ROOT / cfg["routing_registry"]).read_text())
        base_ids = {item["id"] for item in base["cases"]}
        self.assertTrue(set(cfg["routing_case_ids"]).issubset(base_ids))

    def test_november_9_provider_captures_are_immutable_and_hash_bound(self):
        campaign_path = ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml"
        cfg = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
        captures = {
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-amd-compute-cohort-2026-11-09-web-capture.json",
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-msft-adjacent-2026-11-09-web-capture.json",
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-mu-memory-cohort-2026-11-09-web-capture.json",
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-peer-cohort-full-metrics-2026-11-09.json",
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-peer-cohort-valuation-fields-2026-11-09.json",
            "evals/campaigns/iteration-07-investing-quality-2026-11/sources/stockanalysis-peer-cohort-ttm-fields-2026-11-09.json",
        }
        for rel in captures:
            path = ROOT / rel
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), cfg["source_sha256"][rel], rel)
            capture = json.loads(raw)
            self.assertIn("2026-11-09", capture["snapshot_id"], rel)
            self.assertTrue(capture["source_pages"], rel)
            self.assertTrue(capture["extracted_text"].strip(), rel)
            self.assertIn("not raw HTTP", capture["archive_type"], rel)

    def test_official_sec_ytd_growth_capture_recomputes_and_preserves_incompatible_fcf_base(self):
        campaign_path = ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml"
        cfg = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
        rel = "evals/campaigns/iteration-07-investing-quality-2026-11/sources/sec-reported-ytd-growth-2026-11-09.json"
        raw = (ROOT / rel).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), cfg["source_sha256"][rel])
        capture = json.loads(raw)
        self.assertIn("not raw filing HTML", capture["archive_type"])
        self.assertEqual({"AMD", "NVDA", "INTC", "MRVL"}, {item["ticker"] for item in capture["issuers"]})
        replay_rel = "evals/campaigns/iteration-07-investing-quality-2026-11/sources/peer-comparability-amd-2026-11-09-input.json"
        replay = json.loads((ROOT / replay_rel).read_text(encoding="utf-8"))
        replay_issuers = {item["ticker"]: item for item in [replay["target"], *replay["peers"]]}
        for item in capture["issuers"]:
            self.assertTrue(item["filing_url"].startswith("https://www.sec.gov/Archives/"))
            self.assertAlmostEqual(item["revenue_current"] / item["revenue_prior"] - 1,
                                   float(item["revenue_growth_yoy"]), places=3)
            self.assertEqual(item["operating_cash_flow_current"] - item["capex_current"], item["fcf_current"])
            self.assertEqual(item["operating_cash_flow_prior"] - item["capex_prior"], item["fcf_prior"])
            if item["fcf_prior"] <= 0:
                self.assertIsNone(item["fcf_growth_yoy"])
                self.assertEqual("NOT_APPLICABLE", item["fcf_growth_status"])
            else:
                self.assertAlmostEqual(item["fcf_current"] / item["fcf_prior"] - 1,
                                       float(item["fcf_growth_yoy"]), places=3)
            issuer = replay_issuers[item["ticker"]]
            self.assertEqual(item["revenue_growth_yoy"], issuer["metrics"]["revenue_growth_ytd"]["value"])
            self.assertEqual(item["fcf_growth_yoy"], issuer["metrics"]["fcf_growth_ytd"]["value"])
            self.assertIn(str(item["period_length_months"]) + "-month fiscal YTD",
                          issuer["metrics"]["revenue_growth_ytd"]["period_alignment_group"])

    def test_exact_runtime_peer_inputs_are_replayable_and_bind_to_receipts(self):
        campaign_path = ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml"
        cfg = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
        cases = {
            "peer-comparability-amd-2026-11-09-input.json": (
                "eeb03c2cde299396bf2f11c4c61e7f9fcf2fd2b8779a01a16b97ddead26d2f19",
                "AMD",
                {"NVDA", "INTC", "MRVL"},
            ),
            "peer-comparability-mu-2026-11-09-input.json": (
                "e6e662397b4f840b8698845c299ba1f757fa7eae163432a2460bb675dabdc799",
                "MU",
                {"SKHYNIX", "NANYA", "KIOXIA"},
            ),
        }
        fit_dimensions = {"value_chain_role", "revenue_profit_mix", "customer_base", "cyclicality", "capital_intensity"}

        def canonical(value):
            if isinstance(value, list):
                return [canonical(item) for item in value]
            if isinstance(value, dict):
                return {key: canonical(value[key]) for key in sorted(value)}
            return value

        for filename, (receipt_input_sha, target_ticker, expected_direct) in cases.items():
            rel = f"evals/campaigns/iteration-07-investing-quality-2026-11/sources/{filename}"
            raw = (ROOT / rel).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), cfg["source_sha256"][rel], rel)
            request = json.loads(raw)
            request_sha = hashlib.sha256(
                json.dumps(canonical(request), separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
            self.assertEqual(receipt_input_sha, request_sha, rel)
            self.assertEqual("2026-11-09", request["as_of"])
            self.assertEqual(target_ticker, request["target"]["ticker"])
            direct = {peer["ticker"] for peer in request["peers"] if peer["peer_tier"] == "DIRECT"}
            self.assertEqual(expected_direct, direct)
            self.assertIn("MSFT", {peer["ticker"] for peer in request["peers"] if peer["peer_tier"] == "ADJACENT"})
            for issuer in [request["target"], *request["peers"]]:
                self.assertTrue(issuer["metrics"], issuer["ticker"])
                self.assertTrue(all(key == metric["name"] for key, metric in issuer["metrics"].items()))
                self.assertIsNone(issuer["metrics"]["eps_revision_90d"]["value"])
                self.assertEqual("UNVERIFIED", issuer["metrics"]["eps_revision_90d"]["status"])
            for peer in request["peers"]:
                if peer["peer_tier"] == "DIRECT":
                    self.assertEqual(fit_dimensions, set(peer["economic_fit"]))

    def test_amd_and_mu_source_snapshots_reproduce_three_peer_tables_with_distinct_model_exclusions(self):
        source_dir = ROOT / "evals/campaigns/iteration-07-investing-quality-2026-11/sources"

        def to_metric(item):
            raw_value = item.get("value")
            return PeerMetric(
                name=item["name"],
                value=Decimal(str(raw_value)) if raw_value is not None else None,
                unit=item["unit"],
                definition=item["definition"],
                period=item["period"],
                basis=item["basis"],
                published_at=item["published_at"],
                source_url=item["source_url"],
                status=item["status"],
                horizon=item.get("horizon", ""),
                currency=item.get("currency", "USD"),
                period_alignment_group=item.get("period_alignment_group", ""),
                basis_group=item.get("basis_group", ""),
                supporting_source_urls=tuple(item.get("supporting_source_urls", [])),
            )

        def to_issuer(item):
            fit = {
                key: EconomicFitEvidence(**evidence)
                for key, evidence in item.get("economic_fit", {}).items()
            }
            return IssuerSnapshot(
                ticker=item["ticker"], sector=item["sector"], industry=item["industry"],
                business_model=item["business_model"], as_of=item["as_of"],
                metrics={key: to_metric(value) for key, value in item["metrics"].items()},
                cyclical=item["cyclical"], comparison_group=item["comparison_group"],
                inclusion_rationale=item["inclusion_rationale"], peer_tier=item["peer_tier"],
                economic_fit=fit,
            )

        expected = {
            "amd": ("AMD", {"NVDA", "INTC", "MRVL"}),
            "mu": ("MU", {"SKHYNIX", "NANYA", "KIOXIA"}),
        }
        for cohort, (target_ticker, expected_direct) in expected.items():
            request = json.loads((source_dir / f"peer-comparability-{cohort}-2026-11-09-input.json").read_text())
            result = compare_peer_set(
                to_issuer(request["target"]),
                [to_issuer(peer) for peer in request["peers"]],
                request["as_of"],
            )
            self.assertEqual("COMPARABLE", result["status"], cohort)
            self.assertEqual(target_ticker, result["target"])
            self.assertEqual(3, result["direct_peer_count"])
            self.assertEqual(3, result["core_metric_peer_counts"]["ev_sales"])
            self.assertEqual(3, result["core_metric_peer_counts"]["ev_ebitda"])
            self.assertEqual(0, result["core_metric_peer_counts"]["forward_pe"])
            direct = {row["ticker"] for row in result["peers"] if row["eligibility"] == "INCLUDED"}
            self.assertEqual(expected_direct, direct, cohort)
            msft = next(row for row in result["peers"] if row["ticker"] == "MSFT")
            self.assertEqual("EXCLUDED", msft["eligibility"])
            self.assertEqual("COMPARISON_GROUP_MISMATCH", msft["reason"])
            msft_input = next(peer for peer in request["peers"] if peer["ticker"] == "MSFT")
            self.assertEqual("cloud software and hyperscale cloud services", msft_input["business_model"])
            self.assertIsNone(result["recommendation"])
            self.assertFalse(result["ranked"])


if __name__ == "__main__":
    unittest.main()
