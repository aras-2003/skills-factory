from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/investing"))
import investment_contracts as contracts  # noqa: E402


AS_OF = "2026-11-25T12:00:00Z"


def context(*, instrument_type="EQUITY", instrument_id="NASDAQ:TEST", mode="TEST"):
    return {
        "contract_version": "1.0", "analysis_id": "analysis-001",
        "instrument": {"canonical_id": instrument_id, "type": instrument_type, "ticker": "TEST", "industry": "BANK" if instrument_id.endswith("BANK") else None},
        "as_of": AS_OF,
        "horizon": {"min_months": 36, "max_months": 60, "objective": "long-term research"},
        "requested_skills": ["security-underwriting"], "context_mode": "USER_SUPPLIED_CONTEXT",
        "evidence_snapshot_refs": ["filing-001"], "execution_mode": mode,
        "write_scope": {"mode": "NONE"},
    }


def result(*, instrument_id="NASDAQ:TEST", as_of=AS_OF):
    return {
        "contract_version": "1.0", "result_id": "result-001", "analysis_id": "analysis-001",
        "producer": {"skill_id": "security-underwriting", "version": "1.0.0", "source_sha": "a" * 40},
        "instrument_id": instrument_id, "as_of": as_of, "execution_status": "PARTIAL",
        "applicability": "APPLICABLE",
        "evidence_refs": [{"source_id": "filing-001", "source_url": "https://example.invalid/fixture", "published_at": "2026-10-01T00:00:00Z", "retrieved_at": "2026-11-25T11:00:00Z", "vendor": "synthetic", "license": "synthetic-fixture", "fiscal_basis": "FY", "source_sha256": "b" * 64, "locator": "fixture:1", "allowed_as_of": "2026-11-25T12:00:00Z"}],
        "payload_type": "SYNTHETIC_RESEARCH", "payload_schema_version": "1.0", "payload": {},
        "findings": [{"claim_id": "claim-1", "claim_kind": "INTERPRETATION", "text": "Synthetic partial finding", "scope": "issuer", "horizon": "36-60m", "evidence_ids": ["filing-001"], "counterevidence_ids": [], "evidence_status": "PROVISIONAL", "assessment": "UNRESOLVED", "confidence": "UNDETERMINED", "confidence_rationale": "synthetic", "limitations": ["not real issuer evidence"], "invalidation": {"metric": None, "operator": None, "threshold": None, "status": "NOT_SET", "window": None, "predeclared_at": None}}],
        "metrics": [], "blockers": ["incomplete synthetic snapshot"], "handoff": [], "source_result_refs": [],
    }


class InvestmentContractsTests(unittest.TestCase):
    def test_schemas_are_draft_2020_12_and_synthetic_variants_validate(self):
        for path in contracts.SCHEMAS.values():
            schema = json.loads((ROOT / path).read_text())
            Draft202012Validator.check_schema(schema)
        for case in (context(), context(instrument_type="ETF", instrument_id="NYSE:ETF"), context(instrument_id="NYSE:TEST-BANK")):
            self.assertEqual([], contracts.validate_exchange(case, [result(instrument_id=case["instrument"]["canonical_id"])], root=ROOT))

    def test_required_domain_fixtures_validate_without_ticker_aliasing(self):
        schema = json.loads((ROOT / contracts.SCHEMAS["context"]).read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        cases = json.loads((ROOT / "tests/fixtures/investing/interfaces/contexts-v1.json").read_text())
        self.assertEqual(5, len(cases))
        for case in cases:
            with self.subTest(case=case["analysis_id"]):
                self.assertEqual([], list(validator.iter_errors(case)))
        same_ticker = [case for case in cases if case["instrument"].get("ticker") == "TEST"]
        self.assertGreaterEqual(len({case["instrument"]["canonical_id"] for case in same_ticker}), 3)

    def test_checked_in_synthetic_fixture_validates_from_cli_inputs(self):
        base = ROOT / "tests/fixtures/investing/interfaces"
        self.assertEqual([], contracts.validate_files(base / "context-equity-v1.json", base / "results-equity-v1.json", root=ROOT))

    def test_duplicate_ticker_does_not_alias_distinct_canonical_ids(self):
        one, two = context(instrument_id="NASDAQ:TEST"), context(instrument_id="LSE:TEST")
        self.assertNotEqual(one["instrument"]["canonical_id"], two["instrument"]["canonical_id"])
        self.assertEqual([], contracts.validate_exchange(two, [result(instrument_id="LSE:TEST")], root=ROOT))

    def test_explicit_partial_result_is_valid_and_not_promoted_to_success(self):
        r = result()
        self.assertEqual([], contracts.validate_exchange(context(), [r], root=ROOT))
        self.assertEqual("PARTIAL", r["execution_status"])
        self.assertEqual("UNDETERMINED", r["findings"][0]["confidence"])

    def test_legacy_adapters_preserve_payload_bytes_as_opaque_values(self):
        payload = {"score": 7, "legacy": {"evidence": ["old-id"], "text": "unchanged"}}
        original_payload = copy.deepcopy(payload)
        for skill in ("security-underwriting", "technical-structure", "valuation-scenario-review"):
            c = context(); c["requested_skills"] = [skill]; c["evidence_snapshot_refs"] = []
            wrapped = contracts.wrap_legacy_result(context=c, skill_id=skill, version="0.1.0", source_sha="a" * 40, payload_schema_version="legacy-v1", payload=payload, result_id=f"result-{skill}", execution_status="BLOCKED", applicability="APPLICABLE")
            self.assertEqual(payload, wrapped["payload"])
            self.assertEqual("BLOCKED", wrapped["execution_status"])
            wrapped["payload"]["legacy"]["evidence"].append("mutated")
            self.assertEqual(["old-id"], payload["legacy"]["evidence"])
            self.assertEqual([], contracts.validate_exchange(c, [wrapped], root=ROOT))
        self.assertEqual(original_payload, payload)

    def test_unrequested_producer_is_rejected(self):
        r = result(); r["producer"]["skill_id"] = "valuation-scenario-review"
        self.assertTrue(any("producer was not requested" in e for e in contracts.validate_exchange(context(), [r], root=ROOT)))

    def test_unknown_major_and_unknown_fields_fail_closed(self):
        c = context(); c["contract_version"] = "2.0"
        self.assertTrue(contracts.validate_exchange(c, [result()], root=ROOT))
        c = context(); c["silent_fallback"] = True
        self.assertTrue(contracts.validate_exchange(c, [result()], root=ROOT))

    def test_non_utc_cutoff_and_inverted_horizon_are_rejected(self):
        c = context(); c["as_of"] = "2026-11-25T13:00:00+01:00"
        self.assertIn("context as_of must be expressed in UTC", contracts.validate_exchange(c, [result(as_of=c["as_of"])], root=ROOT))
        c = context(); c["horizon"]["min_months"] = 61
        self.assertIn("horizon min_months must not exceed max_months", contracts.validate_exchange(c, [result()], root=ROOT))

    def test_timezone_boundary_normalizes_same_instant_and_post_cutoff_is_rejected(self):
        r = result(as_of="2026-11-25T13:00:00+01:00")
        self.assertEqual([], contracts.validate_exchange(context(), [r], root=ROOT))
        r = result(); r["evidence_refs"][0]["published_at"] = "2026-11-25T12:00:01Z"
        self.assertTrue(any("published after as_of" in e for e in contracts.validate_exchange(context(mode="HISTORICAL_REPLAY"), [r], root=ROOT)))

    def test_live_context_rejects_future_metric_observation_and_period(self):
        r = result()
        r["metrics"] = [{"metric_id": "fcf", "definition": "free cash flow", "raw_value": 10, "unit": "USD", "currency": "USD", "period_start": "2026-01-01", "period_end": "2026-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "source_ids": ["filing-001"], "published_at": "2026-01-01T00:00:00Z", "observed_at": "2026-11-25T12:00:01Z", "method_id": "synthetic", "method_version": "1", "calc_receipt": "fixture", "evidence_status": "VERIFIED"}]
        errors = contracts.validate_exchange(context(mode="LIVE"), [r], root=ROOT)
        self.assertTrue(any("observed after as_of" in e for e in errors))
        self.assertTrue(any("period ends after as_of" in e for e in errors))

    def test_analysis_instrument_and_as_of_must_match_context(self):
        r = result(instrument_id="NYSE:OTHER", as_of="2026-11-24T12:00:00Z")
        errors = contracts.validate_exchange(context(), [r], root=ROOT)
        self.assertIn("results/0 instrument_id mismatch", errors)
        self.assertIn("results/0 as_of mismatch", errors)
        r = result(); r["analysis_id"] = "analysis-other"
        self.assertIn("results/0 analysis_id mismatch", contracts.validate_exchange(context(), [r], root=ROOT))

    def test_historical_replay_rejects_post_cutoff_evidence_and_metrics(self):
        r = result(); r["evidence_refs"][0]["published_at"] = "2026-11-25T12:00:01Z"
        self.assertTrue(any("published after as_of" in e for e in contracts.validate_exchange(context(mode="HISTORICAL_REPLAY"), [r], root=ROOT)))

    def test_duplicate_claim_evidence_result_ids_and_dangling_refs_fail(self):
        a, b = result(), copy.deepcopy(result()); b["result_id"] = "result-002"
        self.assertTrue(any("duplicate claim_id" in e for e in contracts.validate_exchange(context(), [a, b], root=ROOT)))
        b["findings"][0]["claim_id"] = "claim-2"; b["evidence_refs"][0]["source_id"] = "filing-001"
        a["findings"][0]["evidence_ids"] = ["missing-source"]
        self.assertTrue(any("unresolved finding evidence id" in e for e in contracts.validate_exchange(context(), [a], root=ROOT)))
        a["findings"][0]["evidence_ids"] = ["filing-001"]; a["source_result_refs"] = ["missing-result"]
        self.assertTrue(any("unresolved source_result_ref" in e for e in contracts.validate_exchange(context(), [a], root=ROOT)))

    def test_missing_context_snapshot_and_forbidden_write_escalation_fail(self):
        c = context(); c["evidence_snapshot_refs"] = ["unknown"]
        self.assertTrue(any("unresolved context evidence snapshot" in e for e in contracts.validate_exchange(c, [result()], root=ROOT)))
        c = context(); c["write_scope"] = {"mode": "EXPLICIT_OPERATION", "operation": "WRITE", "target": "thesis", "authorization_ref": "auth-1"}
        self.assertTrue(any("test and historical replay" in e for e in contracts.validate_exchange(c, [result()], root=ROOT)))

    def test_canonical_portfolio_analysis_requires_explicit_policy_and_snapshot(self):
        c = context(mode="LIVE"); c["context_mode"] = "CANONICAL"
        c["requested_skills"] = ["position-sizing-review"]
        self.assertIn("portfolio analysis requires an explicit policy_version_ref", contracts.validate_exchange(c, [result()], root=ROOT))
        self.assertIn("portfolio analysis requires an explicit portfolio_snapshot_ref", contracts.validate_exchange(c, [result()], root=ROOT))

    def test_shared_evidence_may_be_reused_only_with_identical_definition(self):
        a, b = result(), result(); b["result_id"] = "result-2"; b["findings"][0]["claim_id"] = "claim-2"
        self.assertEqual([], contracts.validate_exchange(context(), [a, b], root=ROOT))
        b["evidence_refs"][0]["source_sha256"] = "c" * 64
        self.assertTrue(any("conflicting definitions for evidence" in e for e in contracts.validate_exchange(context(), [a, b], root=ROOT)))

    def test_blocked_result_cannot_smuggle_observations(self):
        r = result(); r["execution_status"] = "BLOCKED"
        self.assertTrue(any("cannot carry findings or metrics" in e for e in contracts.validate_exchange(context(), [r], root=ROOT)))

    def test_metric_mismatches_are_preserved_but_never_compared(self):
        left = {"metric_id": "fcf", "definition": "free cash flow", "unit": "amount", "period_start": "2025-01-01", "period_end": "2025-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "currency": "USD", "raw_value": 10, "published_at": "2026-02-01T00:00:00Z", "evidence_status": "VERIFIED"}
        right = dict(left, currency="PLN", raw_value=40)
        outcome = contracts.metric_comparability(left, right, as_of=AS_OF)
        self.assertEqual("NOT_COMPARABLE", outcome["status"])
        self.assertEqual([10, 40], outcome["preserved_values"])
        self.assertIn("currency", outcome["reason_codes"])

    def test_metric_comparison_requires_value_publication_and_verified_status(self):
        base = {"metric_id": "m", "definition": "metric", "unit": "amount", "period_start": "2025-01-01", "period_end": "2025-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "currency": "USD", "raw_value": None, "published_at": None, "evidence_status": "UNKNOWN"}
        outcome = contracts.metric_comparability(base, dict(base), as_of=AS_OF)
        self.assertEqual("NOT_COMPARABLE", outcome["status"])
        self.assertIn("missing_value", outcome["reason_codes"])
        self.assertIn("missing_publication_time", outcome["reason_codes"])
        self.assertIn("left_evidence_unknown", outcome["reason_codes"])

    def test_metric_comparability_rejects_nonfinite_values(self):
        base = {"metric_id": "m", "definition": "metric", "unit": "amount", "period_start": "2025-01-01", "period_end": "2025-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "currency": "USD", "raw_value": 1.0, "published_at": "2026-02-01T00:00:00Z", "observed_at": "2026-02-02T00:00:00Z", "evidence_status": "VERIFIED"}
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                other = dict(base, raw_value=value)
                self.assertEqual("NOT_COMPARABLE", contracts.metric_comparability(base, other, as_of=AS_OF)["status"])

    def test_currency_period_basis_adjustment_action_and_missingness_each_block_comparison(self):
        base = {"metric_id": "m", "definition": "metric", "unit": "amount", "period_start": "2025-01-01", "period_end": "2025-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "currency": "USD", "raw_value": 1, "published_at": "2026-02-01T00:00:00Z", "evidence_status": "VERIFIED"}
        for field, value in (("currency", "PLN"), ("period_end", "2024-12-31"), ("accounting_basis", "IFRS"), ("adjustment_basis", "adjusted"), ("corporate_action_basis", "unadjusted"), ("currency", None)):
            with self.subTest(field=field, value=value):
                other = dict(base); other[field] = value
                self.assertEqual("NOT_COMPARABLE", contracts.metric_comparability(base, other, as_of=AS_OF)["status"])

    def test_schema_rejects_malformed_timezone_missing_currency_and_nonfinite_metric(self):
        r = result(); r["as_of"] = "2026-11-25"
        self.assertTrue(contracts.validate_exchange(context(), [r], root=ROOT))
        r = result(); r["metrics"] = [{"metric_id": "m", "definition": "x", "raw_value": 1, "unit": "amount", "currency": "US", "period_start": None, "period_end": None, "accounting_basis": None, "adjustment_basis": None, "source_ids": [], "published_at": None, "observed_at": None, "method_id": None, "method_version": None, "calc_receipt": None, "evidence_status": "UNKNOWN"}]
        self.assertTrue(contracts.validate_exchange(context(), [r], root=ROOT))

    def test_optional_missing_metric_value_is_safe_and_nonfinite_value_fails(self):
        r = result()
        metric = {"metric_id": "fcf-001", "definition": "free cash flow", "raw_value": 1.0, "unit": "amount", "currency": "USD", "period_start": "2025-01-01", "period_end": "2025-12-31", "accounting_basis": "GAAP", "adjustment_basis": "reported", "corporate_action_basis": "split-adjusted", "source_ids": ["filing-001"], "published_at": "2026-02-01T00:00:00Z", "observed_at": "2026-02-02T00:00:00Z", "method_id": "calc", "method_version": "1", "calc_receipt": "receipt-1", "evidence_status": "UNKNOWN"}
        missing = dict(metric); missing.pop("raw_value")
        r["metrics"] = [missing]
        self.assertEqual([], contracts.validate_exchange(context(), [r], root=ROOT))
        r["metrics"][0]["raw_value"] = float("nan")
        self.assertTrue(any("raw_value must be finite" in e for e in contracts.validate_exchange(context(), [r], root=ROOT)))

    def test_verified_metric_requires_trace_and_cutoff_metadata(self):
        r = result()
        r["metrics"] = [{"metric_id": "fcf", "definition": "free cash flow", "raw_value": 1.0, "unit": None, "currency": None, "period_start": None, "period_end": None, "accounting_basis": None, "adjustment_basis": None, "source_ids": [], "published_at": None, "observed_at": None, "method_id": None, "method_version": None, "calc_receipt": None, "evidence_status": "VERIFIED"}]
        self.assertTrue(contracts.validate_exchange(context(), [r], root=ROOT))


if __name__ == "__main__":
    unittest.main()
