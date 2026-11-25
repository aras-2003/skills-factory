"""Deterministic, read-only synthesis tests for INV-ARCH-02."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.investing import investment_decisions as decisions

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/investing/interfaces"
AS_OF = "2026-11-25T12:00:00Z"
PRODUCERS = {
    "quality": "security-underwriting",
    "eligibility": "investment-policy-design",
    "thesis": "thesis-challenge",
    "valuation": "valuation-scenario-review",
    "portfolio": "portfolio-state-review",
    "timing": "technical-structure",
}
PRODUCER_VERSIONS = {"security-underwriting":"0.6.0", "investment-policy-design":"0.1.0", "thesis-challenge":"0.1.2", "valuation-scenario-review":"0.4.0", "portfolio-state-review":"0.7.2", "technical-structure":"0.1.1"}


def decision_input(*, position="NOT_HELD", thesis="SURVIVES", valuation="ATTRACTIVE", eligibility="ELIGIBLE", quality="PASS", portfolio="IN_POLICY", timing=None):
    context = json.loads((FIXTURES / "context-equity-v1.json").read_text())
    context["requested_skills"] = list(PRODUCERS.values())
    context["policy_version_ref"] = "policy:synthetic:v1"
    context["portfolio_snapshot_ref"] = "portfolio:synthetic:2026-11-25"
    results = []
    signals = {}
    states = {"quality": quality, "eligibility": eligibility, "thesis": thesis, "valuation": "UNRESOLVED" if valuation == "UNRESOLVED" else "READY", "portfolio": portfolio}
    if timing is not None:
        states["timing"] = timing
    for index, key in enumerate(PRODUCERS):
        if key not in states:
            continue
        result = json.loads((FIXTURES / "results-equity-v1.json").read_text())[0]
        result["result_id"] = f"result-{key}"
        result["producer"]["skill_id"] = PRODUCERS[key]
        result["producer"]["version"] = PRODUCER_VERSIONS[PRODUCERS[key]]
        result["execution_status"] = "SUCCESS"
        result["findings"][0]["claim_id"] = f"claim-{key}"
        result["findings"][0]["evidence_status"] = "VERIFIED"
        result["evidence_refs"][0].update({"source_sha256": "b" * 64, "archive_snapshot_ref": "archive:synthetic-001"})
        results.append(result)
        signals[key] = {
            "state": states[key],
            "producer_skill_id": PRODUCERS[key],
            "result_id": result["result_id"],
            "claim_ids": [f"claim-{key}"],
            "evidence_ids": ["fixture-filing-001"],
        }
        if key == "valuation":
            signals[key]["security_attractiveness"] = valuation
            signals[key]["asset_path"] = "ETF" if context["instrument"]["type"] == "ETF" else ("BANK" if "bank" in (context["instrument"].get("industry") or "").lower() else "EQUITY")
        if key == "quality" and states[key] == "CONFLICTED":
            signals[key]["conflict_ids"] = ["conflict:fcf:synthetic-1"]
        if key == "portfolio":
            signals[key]["position_state"] = position
            signals[key]["position_snapshot_complete"] = position != "UNKNOWN"
        if key in {"eligibility", "portfolio"}:
            signals[key]["policy_rule_ref"] = "policy-rule:synthetic:1"
        result["payload_type"] = "INVESTMENT_DECISION_SIGNAL"
        result["payload_schema_version"] = "1.0"
        signal_payload = {"signal_type": key, "state": states[key], "claim_ids": [f"claim-{key}"], "evidence_ids": ["fixture-filing-001"]}
        if key == "valuation":
            signal_payload["security_attractiveness"] = valuation
            signal_payload["asset_path"] = signals[key]["asset_path"]
        if key == "quality" and states[key] == "CONFLICTED": signal_payload["conflict_ids"] = signals[key]["conflict_ids"]
        if key == "portfolio":
            signal_payload["position_state"] = position
            signal_payload["position_snapshot_complete"] = position != "UNKNOWN"
        if key in {"eligibility", "portfolio"}:
            signal_payload["policy_rule_ref"] = signals[key]["policy_rule_ref"]
        if key == "portfolio" and "continuation_rule_ref" in signals[key]:
            signal_payload["continuation_rule_ref"] = signals[key]["continuation_rule_ref"]
        result["payload"] = {"decision_signal_v1": signal_payload}
    if position == "HELD" and portfolio == "IN_POLICY":
        signals["portfolio"]["continuation_rule_ref"] = "policy-rule:continue:synthetic"
        portfolio_result = next(result for result in results if result["result_id"] == "result-portfolio")
        portfolio_result["payload"]["decision_signal_v1"]["continuation_rule_ref"] = signals["portfolio"]["continuation_rule_ref"]
    return {"schema_version": "1.0", "context": context, "results": results, "position_state": position, "signals": signals}


class InvestmentDecisionTests(unittest.TestCase):
    def test_output_schema_is_draft_2020_12_and_positive_wait_is_advisory_only(self):
        value = decision_input(valuation="UNFAVORABLE")
        result = decisions.synthesize_decision(value, root=ROOT)
        schema = json.loads((ROOT / "schemas/investing/investment-decision-v1.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(result)
        self.assertEqual("WAIT", result["advisory_recommendation"])
        self.assertTrue(result["owner_approval_required"])
        self.assertFalse(result["execution_authorized"])

    def test_full_36_cell_matrix_preserves_gates_and_never_executes(self):
        for position in ("NOT_HELD", "HELD"):
            for thesis in ("SURVIVES", "WEAKENED", "INVALIDATED"):
                for valuation in ("ATTRACTIVE", "FAIR", "UNFAVORABLE"):
                    for portfolio in ("IN_POLICY", "REVIEW_THRESHOLD"):
                        with self.subTest(position=position, thesis=thesis, valuation=valuation, portfolio=portfolio):
                            value = decision_input(position=position, thesis=thesis, valuation=valuation, portfolio=portfolio)
                            before = copy.deepcopy(value)
                            output = decisions.synthesize_decision(value, root=ROOT)
                            self.assertEqual([f"G{i}" for i in range(7)], [gate["gate_id"] for gate in output["gate_results"]])
                            self.assertFalse(output["execution_authorized"])
                            self.assertTrue(output["owner_approval_required"])
                            self.assertEqual(before, value)

    def test_positive_wait_requires_new_position_and_verified_unfavorable_valuation(self):
        self.assertEqual("WAIT", decisions.synthesize_decision(decision_input(valuation="UNFAVORABLE"), root=ROOT)["advisory_recommendation"])
        held = decisions.synthesize_decision(decision_input(position="HELD", valuation="UNFAVORABLE"), root=ROOT)
        self.assertNotEqual("WAIT", held["advisory_recommendation"])

    def test_held_continue_requires_explicit_rule(self):
        value = decision_input(position="HELD")
        self.assertEqual("HOLD", decisions.synthesize_decision(value, root=ROOT)["advisory_recommendation"])
        value["signals"]["portfolio"].pop("continuation_rule_ref")
        portfolio_result = next(result for result in value["results"] if result["result_id"] == "result-portfolio")
        portfolio_result["payload"]["decision_signal_v1"].pop("continuation_rule_ref")
        self.assertIsNone(decisions.synthesize_decision(value, root=ROOT)["advisory_recommendation"])

    def test_review_threshold_is_not_a_trim_or_hard_cap(self):
        output = decisions.synthesize_decision(decision_input(position="HELD", portfolio="REVIEW_THRESHOLD"), root=ROOT)
        self.assertEqual("TRIM_REVIEW", output["advisory_recommendation"])
        self.assertNotEqual("TRIM", output["advisory_recommendation"])
        self.assertIn("POLICY_REVIEW_THRESHOLD", output["reason_codes"])

    def test_hard_cap_breach_requires_reduction_review_not_trade(self):
        output = decisions.synthesize_decision(decision_input(position="HELD", portfolio="HARD_CAP_BREACH"), root=ROOT)
        self.assertIsNone(output["advisory_recommendation"])
        self.assertIn("POLICY_BREACH_REDUCTION_REVIEW", output["reason_codes"])
        self.assertFalse(output["execution_authorized"])

    def test_invalid_thesis_cheap_valuation_does_not_become_wait(self):
        output = decisions.synthesize_decision(decision_input(thesis="INVALIDATED", valuation="UNFAVORABLE"), root=ROOT)
        self.assertEqual("AVOID", output["advisory_recommendation"])
        self.assertNotEqual("WAIT", output["advisory_recommendation"])

    def test_held_invalid_thesis_is_sell_review_only(self):
        output = decisions.synthesize_decision(decision_input(position="HELD", thesis="INVALIDATED"), root=ROOT)
        self.assertEqual("SELL_REVIEW", output["advisory_recommendation"])
        self.assertEqual("SELL_REVIEW", output["portfolio_action"])
        self.assertFalse(output["execution_authorized"])

    def test_missing_conflicting_or_late_evidence_abstains_and_blocks_sizing(self):
        for state in ("VERIFY", "CONFLICTED", "UNRESOLVED"):
            with self.subTest(state=state):
                output = decisions.synthesize_decision(decision_input(quality=state), root=ROOT)
                self.assertIsNone(output["advisory_recommendation"])
                self.assertTrue(output["numeric_sizing_blocked"])

    def test_verified_pass_signal_rejects_provisional_claim_evidence(self):
        value = decision_input()
        quality_id = value["signals"]["quality"]["result_id"]
        result = next(item for item in value["results"] if item["result_id"] == quality_id)
        result["findings"][0]["evidence_status"] = "PROVISIONAL"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])
        self.assertIsNone(output["advisory_recommendation"])

    def test_quality_block_and_timing_cannot_override_each_other(self):
        output = decisions.synthesize_decision(decision_input(quality="BLOCK", timing="SUPPORTIVE"), root=ROOT)
        self.assertTrue(output["numeric_sizing_blocked"])
        self.assertIsNone(output["advisory_recommendation"])
        self.assertEqual("BLOCK", output["gate_results"][1]["status"])

    def test_conflicted_finding_is_preserved_as_unresolved_not_averaged(self):
        value = decision_input(quality="CONFLICTED")
        quality_id = value["signals"]["quality"]["result_id"]
        result = next(item for item in value["results"] if item["result_id"] == quality_id)
        result["findings"][0]["evidence_status"] = "CONFLICTED"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("UNRESOLVED", output["gate_results"][1]["status"])
        self.assertEqual("UNRESOLVED", output["gate_results"][4]["status"])
        self.assertEqual(["conflict:fcf:synthetic-1"], output["gate_results"][1]["conflict_ids"])
        self.assertIsNone(output["advisory_recommendation"])

    def test_omitted_timing_is_na_but_unusable_requested_timing_is_unresolved(self):
        omitted = decisions.synthesize_decision(decision_input(), root=ROOT)
        unresolved = decisions.synthesize_decision(decision_input(timing="UNRESOLVED"), root=ROOT)
        self.assertEqual("N/A", omitted["gate_results"][6]["status"])
        self.assertEqual("UNRESOLVED", unresolved["gate_results"][6]["status"])

    def test_unknown_context_version_and_dangling_signal_reference_fail_closed(self):
        bad = decision_input(); bad["context"]["contract_version"] = "2.0"
        output = decisions.synthesize_decision(bad, root=ROOT)
        self.assertIsNone(output["advisory_recommendation"])
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])
        dangling = decision_input(); dangling["signals"]["valuation"]["result_id"] = "missing-result"
        output = decisions.synthesize_decision(dangling, root=ROOT)
        self.assertIsNone(output["advisory_recommendation"])
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])

    def test_position_unknown_stops_g5_without_misclassifying_g0(self):
        output = decisions.synthesize_decision(decision_input(position="UNKNOWN"), root=ROOT)
        self.assertEqual("PASS", output["gate_results"][0]["status"])
        self.assertEqual("UNRESOLVED", output["gate_results"][5]["status"])
        self.assertIsNone(output["advisory_recommendation"])

    def test_g1_block_or_conflict_blocks_downstream_valuation_gate(self):
        for state in ("BLOCK", "CONFLICTED"):
            with self.subTest(state=state):
                output = decisions.synthesize_decision(decision_input(quality=state), root=ROOT)
                self.assertEqual("UNRESOLVED", output["gate_results"][4]["status"])
                self.assertTrue(output["numeric_sizing_blocked"])

    def test_generic_or_mismatched_payload_cannot_claim_decision_signal(self):
        value = decision_input()
        value["results"][0]["payload_type"] = "LEGACY_OPAQUE"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])
        value = decision_input()
        value["results"][0]["payload"]["decision_signal_v1"]["state"] = "BLOCK"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])

    def test_unsupported_producer_version_blocks_synthesis(self):
        value = decision_input()
        value["results"][0]["producer"]["version"] = "99.0.0"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])

    def test_late_publication_blocks_entire_synthesis_before_valuation(self):
        value = decision_input()
        value["results"][0]["evidence_refs"][0]["published_at"] = "2026-11-25T12:00:01Z"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])
        self.assertIsNone(output["advisory_recommendation"])

    def test_portfolio_projection_cannot_invent_policy_or_continuation_rule(self):
        value = decision_input(position="HELD")
        value["signals"]["portfolio"]["continuation_rule_ref"] = "policy-rule:invented"
        result = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", result["gate_results"][0]["status"])
        self.assertIsNone(result["advisory_recommendation"])

    def test_held_position_with_incomplete_snapshot_cannot_receive_hold(self):
        value = decision_input(position="HELD")
        value["signals"]["portfolio"]["position_snapshot_complete"] = False
        portfolio_result = next(result for result in value["results"] if result["result_id"] == "result-portfolio")
        portfolio_result["payload"]["decision_signal_v1"]["position_snapshot_complete"] = False
        result = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("UNRESOLVED", result["gate_results"][5]["status"])
        self.assertIsNone(result["advisory_recommendation"])

    def test_incomplete_position_snapshot_blocks_sell_and_reduction_reviews(self):
        for overrides in ({"thesis": "INVALIDATED"}, {"portfolio": "HARD_CAP_BREACH"}):
            value = decision_input(position="HELD", **overrides)
            value["signals"]["portfolio"]["position_snapshot_complete"] = False
            portfolio_result = next(result for result in value["results"] if result["result_id"] == "result-portfolio")
            portfolio_result["payload"]["decision_signal_v1"]["position_snapshot_complete"] = False
            result = decisions.synthesize_decision(value, root=ROOT)
            self.assertEqual("UNRESOLVED", result["gate_results"][5]["status"])
            self.assertIsNone(result["advisory_recommendation"])
            self.assertEqual("UNRESOLVED", result["portfolio_action"])

    def test_signal_evidence_must_be_linked_to_each_referenced_claim(self):
        value = decision_input()
        thesis_result = next(result for result in value["results"] if result["result_id"] == "result-thesis")
        second_source = dict(thesis_result["evidence_refs"][0], source_id="source-two")
        thesis_result["evidence_refs"].append(second_source)
        second_claim = dict(thesis_result["findings"][0], claim_id="claim-thesis-two", evidence_ids=["source-two"])
        thesis_result["findings"].append(second_claim)
        value["signals"]["thesis"]["claim_ids"].append("claim-thesis-two")
        thesis_result["payload"]["decision_signal_v1"]["claim_ids"].append("claim-thesis-two")
        result = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", result["gate_results"][0]["status"])
        self.assertIsNone(result["advisory_recommendation"])

    def test_malformed_root_and_unhashable_position_fail_closed(self):
        for value in (None, [], {"context": {}, "results": [], "position_state": []}):
            with self.subTest(value=value):
                output = decisions.synthesize_decision(value, root=ROOT)
                self.assertEqual("BLOCK", output["gate_results"][0]["status"])
                self.assertFalse(output["execution_authorized"])

    def test_etf_uses_etf_specific_path_and_wrong_path_abstains(self):
        value = decision_input()
        value["context"]["instrument"]["type"] = "ETF"
        value["signals"]["valuation"]["asset_path"] = "ETF"
        result = next(item for item in value["results"] if item["result_id"] == value["signals"]["valuation"]["result_id"])
        result["payload"]["decision_signal_v1"]["asset_path"] = "ETF"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("PASS", output["gate_results"][0]["status"])
        value["signals"]["valuation"]["asset_path"] = "EQUITY"
        value["results"][-2]["payload"]["decision_signal_v1"]["asset_path"] = "EQUITY"
        output = decisions.synthesize_decision(value, root=ROOT)
        self.assertEqual("BLOCK", output["gate_results"][0]["status"])

    def test_buy_accumulate_direct_trim_sell_are_not_inferred_without_approved_mappings(self):
        for state in ("ATTRACTIVE",):
            output = decisions.synthesize_decision(decision_input(valuation=state), root=ROOT)
            self.assertNotIn(output["advisory_recommendation"], {"BUY", "ACCUMULATE", "TRIM", "SELL"})
            self.assertIn("BUY_ACCUMULATE_MAPPING_NOT_APPROVED", output["reason_codes"])


if __name__ == "__main__":
    unittest.main()
