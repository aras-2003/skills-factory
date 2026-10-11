"""OUT-02 policy tests: no model routing, file creation or runtime behavior is inferred."""
from __future__ import annotations

import unittest

from scripts.output.route import RoutingInputError, plan_outputs

SOURCE = {"result_id": "oaf:transform-01", "revision": "rev-3", "domain": "oaf"}


def request(kind="RENDER_EXISTING", outputs=None, *, source=SOURCE, **kwargs):
    return {
        "request_kind": kind,
        "semantic_resolution": "RESOLVED",
        "requested_outputs": outputs if outputs is not None else [{"kind": "report", "format": "docx"}],
        "source_result": source,
        "capabilities": {"report:docx": "AVAILABLE", "report:pdf": "AVAILABLE",
                         "presentation:canva": "AVAILABLE", "interactive_web:html": "AVAILABLE",
                         "interactive_web:hosted": "AVAILABLE", "spreadsheet:xlsx": "AVAILABLE"},
        **kwargs,
    }


class OutputRouterPolicyTests(unittest.TestCase):
    def test_analyze_only_defaults_chat_without_files(self):
        p = plan_outputs(request("ANALYZE_ONLY", [], source=None))
        self.assertEqual(["chat"], [x["kind"] for x in p["delegations"]])
        self.assertEqual(["text"], [x["format"] for x in p["delegations"]])
        self.assertEqual("READY_TO_DELEGATE", p["delegations"][0]["route_state"])
        self.assertFalse(p["executed"])

    def test_analyze_only_rejects_unrequested_file(self):
        with self.assertRaisesRegex(RoutingInputError, "must not silently generate artifacts"):
            plan_outputs(request("ANALYZE_ONLY", [{"kind": "report", "format": "pdf"}]))

    def test_existing_pack_routes_to_report_without_substantive_reanalysis(self):
        p = plan_outputs(request())
        self.assertEqual("PRESENT_EXISTING", p["mode"])
        self.assertEqual("report-production", p["delegations"][0]["owner"])
        self.assertEqual(SOURCE, p["delegations"][0]["source_result"])
        self.assertEqual("NOT_RUN", p["delegations"][0]["execution_state"])
        self.assertEqual("NOT_RUN", p["delegations"][0]["delivery_state"])

    def test_both_outputs_share_source_but_have_separate_states(self):
        x = request(outputs=[{"kind": "report", "format": "pdf"},
                             {"kind": "presentation", "format": "canva"},
                             {"kind": "interactive_web", "format": "html"}])
        p = plan_outputs(x)
        self.assertEqual("MULTI_OUTPUT", p["mode"])
        self.assertEqual(["report", "presentation", "interactive_web"],
                         [d["kind"] for d in p["delegations"]])
        self.assertTrue(all(d["source_result"] == SOURCE for d in p["delegations"]))
        self.assertTrue(all(d["route_state"] == "READY_TO_DELEGATE" for d in p["delegations"]))
        self.assertTrue(all(d["execution_state"] == "NOT_RUN" for d in p["delegations"]))

    def test_two_formats_of_same_report_are_one_content_product(self):
        p = plan_outputs(request(outputs=[{"kind": "report", "format": "docx"},
                                          {"kind": "report", "format": "pdf"}]))
        self.assertEqual("PRESENT_EXISTING", p["mode"])
        self.assertEqual(["docx", "pdf"], [d["format"] for d in p["delegations"]])

    def test_user_format_order_is_preserved_and_duplicate_deduplicated(self):
        os = [{"kind": "presentation", "format": "canva"},
              {"kind": "report", "format": "pdf"},
              {"kind": "presentation", "format": "canva"}]
        p = plan_outputs(request(outputs=os))
        self.assertEqual(2, len(p["delegations"]))
        self.assertEqual(["canva", "pdf"], [d["format"] for d in p["delegations"]])

    def test_unspecified_external_medium_requires_clarification(self):
        p = plan_outputs(request(outputs=[]))
        self.assertEqual("NEEDS_CLARIFICATION", p["routing_state"])
        self.assertEqual([], p["delegations"])

    def test_semantically_ambiguous_request_never_guesses_from_keywords(self):
        x = request()
        x["semantic_resolution"] = "AMBIGUOUS"
        p = plan_outputs(x)
        self.assertEqual("NEEDS_CLARIFICATION", p["routing_state"])
        self.assertEqual([], p["delegations"])

    def test_existing_report_without_pack_waits_for_source(self):
        p = plan_outputs(request(source=None))
        self.assertEqual("WAITING_FOR_SOURCE", p["delegations"][0]["route_state"])

    def test_analysis_requested_with_upstream_pending_waits(self):
        p = plan_outputs(request("ANALYZE_THEN_RENDER", source=None, analysis_state="NOT_STARTED"))
        self.assertEqual("WAITING_UPSTREAM", p["delegations"][0]["route_state"])
        self.assertEqual("ANALYZE_THEN_RENDER", p["mode"])

    def test_unavailable_upstream_does_not_fabricate_strategy(self):
        p = plan_outputs(request("ANALYZE_THEN_RENDER", source=None, analysis_state="UNAVAILABLE"))
        self.assertEqual("BLOCKED_UPSTREAM", p["delegations"][0]["route_state"])

    def test_missing_provider_does_not_block_independent_other_output(self):
        x = request(outputs=[{"kind": "report", "format": "pdf"},
                             {"kind": "presentation", "format": "canva"}])
        x["capabilities"]["presentation:canva"] = "UNAVAILABLE"
        p = plan_outputs(x)
        self.assertEqual(["READY_TO_DELEGATE", "BLOCKED_CAPABILITY"],
                         [d["route_state"] for d in p["delegations"]])

    def test_unobserved_capability_is_not_assumed_from_brand_connection(self):
        x = request(outputs=[{"kind": "presentation", "format": "pptx"}])
        x["capabilities"]["presentation:canva"] = "AVAILABLE"
        p = plan_outputs(x)
        self.assertEqual("UNVERIFIED_CAPABILITY", p["delegations"][0]["route_state"])
        self.assertEqual("UNKNOWN", p["delegations"][0]["capability_state"])

    def test_spreadsheet_is_deferred_even_when_generic_writer_is_available(self):
        p = plan_outputs(request(outputs=[{"kind": "spreadsheet", "format": "xlsx"}]))
        self.assertEqual("DEFERRED_PRODUCT", p["delegations"][0]["route_state"])
        self.assertEqual("spreadsheet-adapter-deferred", p["delegations"][0]["owner"])

    def test_edit_existing_requires_artifact_ref_and_never_creates(self):
        x = request("EDIT_EXISTING", [{"kind": "presentation", "format": "canva"}], source=None,
                    artifact_ref="canva:D12345")
        x["capabilities"]["edit:presentation:canva"] = "AVAILABLE"
        p = plan_outputs(x)
        self.assertEqual("EDIT_EXISTING", p["mode"])
        self.assertEqual("canva:D12345", p["delegations"][0]["artifact_ref"])
        self.assertFalse(p["executed"])

    def test_edit_cannot_be_inferred_from_generation_only(self):
        x = request("EDIT_EXISTING", [{"kind": "presentation", "format": "canva"}],
                    source=None, artifact_ref="canva:D12345")
        # A new deck can be generated, but the connector may not support editing.
        p = plan_outputs(x)
        self.assertEqual("UNVERIFIED_CAPABILITY", p["delegations"][0]["route_state"])
        self.assertEqual("UNKNOWN", p["delegations"][0]["capability_state"])

    def test_edit_existing_without_ref_errors(self):
        with self.assertRaisesRegex(RoutingInputError, "artifact_ref"):
            plan_outputs(request("EDIT_EXISTING", [{"kind": "report", "format": "docx"}]))

    def test_edit_existing_multi_output_requires_target_specific_task(self):
        with self.assertRaisesRegex(RoutingInputError, "one exact target"):
            plan_outputs(request("EDIT_EXISTING", [
                {"kind": "report", "format": "pdf"},
                {"kind": "presentation", "format": "canva"}], artifact_ref="any"))

    def test_public_deployment_requires_permission(self):
        x = request(outputs=[{"kind": "interactive_web", "format": "hosted"}])
        p = plan_outputs(x)
        self.assertEqual("BLOCKED_PUBLICATION_APPROVAL", p["delegations"][0]["route_state"])
        self.assertEqual("NOT_REQUESTED", p["publication_state"])

    def test_authorized_publish_only_authorizes_separate_step(self):
        x = request(outputs=[{"kind": "interactive_web", "format": "hosted"}],
                    publish_requested=True, publish_authorized=True)
        p = plan_outputs(x)
        self.assertEqual("AUTHORIZED_SEPARATE_STEP", p["publication_state"])
        self.assertEqual("READY_TO_DELEGATE", p["delegations"][0]["route_state"])
        self.assertEqual("NOT_RUN", p["delegations"][0]["delivery_state"])

    def test_unapproved_publish_does_not_affect_other_artifact(self):
        x = request(outputs=[{"kind": "report", "format": "pdf"}], publish_requested=True)
        p = plan_outputs(x)
        self.assertEqual("REQUIRES_EXPLICIT_APPROVAL", p["publication_state"])
        self.assertEqual("READY_TO_DELEGATE", p["delegations"][0]["route_state"])

    def test_unknown_format_is_not_coerced_into_an_alternative(self):
        with self.assertRaisesRegex(RoutingInputError, "Unsupported target/format"):
            plan_outputs(request(outputs=[{"kind": "presentation", "format": "fake-pptx"}]))

    def test_missing_source_revision_is_invalid(self):
        with self.assertRaisesRegex(RoutingInputError, "source_result.revision"):
            plan_outputs(request(source={"result_id": "a", "revision": "", "domain": "oaf"}))

    def test_invalid_capability_state_is_rejected(self):
        x = request()
        x["capabilities"]["report:docx"] = "CREATED"
        with self.assertRaisesRegex(RoutingInputError, "Invalid capability"):
            plan_outputs(x)

    def test_unresolved_semantic_classification_is_not_silently_accepted(self):
        x = request()
        del x["semantic_resolution"]
        with self.assertRaisesRegex(RoutingInputError, "semantic_resolution"):
            plan_outputs(x)

    def test_boolean_publishing_fields_do_not_accept_strings(self):
        with self.assertRaisesRegex(RoutingInputError, "booleans"):
            plan_outputs(request(publish_requested="yes"))

    def test_nested_kind_format_invalid_type_is_rejected(self):
        with self.assertRaises(RoutingInputError):
            plan_outputs(request(outputs=[{"kind": {"surprise": 1}, "format": "pdf"}]))


if __name__ == "__main__":
    unittest.main()
