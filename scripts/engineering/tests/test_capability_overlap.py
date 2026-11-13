from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.engineering import capability_overlap as matcher


def fact_items(values):
    return [{"value": value, "evidence": [{"source_path": "fixture/SKILL.md", "source_sha256": "a" * 64, "line_start": 1, "line_end": 2}]} for value in (values or [])]


def capability(identity: str, *, triggers=None, outputs=None, domains=None, tools=None, dependencies=None, permissions=None, conflicts=None):
    return {
        "identity": identity,
        "facets": {
            "triggers": fact_items(triggers),
            "outputs": fact_items(outputs),
            "domain_semantics": fact_items(domains),
            "tools": fact_items(tools),
            "dependencies": fact_items(dependencies),
            "permissions": fact_items(permissions),
            "conflicts": fact_items(conflicts),
        },
    }


class CapabilityOverlapTests(unittest.TestCase):
    def run_match(self, candidate, existing, complete=True):
        return matcher.compare_capabilities(candidate, {"schema_version": 1, "complete": complete, "capabilities": existing})

    def test_same_function_duplicate_reuses_and_rejects_reimport(self):
        candidate = capability("external.demo", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"], tools=["filesystem"])
        existing = capability("skills/meta/skill-authoring", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"], tools=["filesystem"])
        report = self.run_match(candidate, [existing])
        self.assertEqual("REUSE_EXISTING", report["decision"])
        self.assertIn("DUPLICATE_REIMPORT_REJECTED", report["reason_codes"])
        self.assertEqual([existing["identity"]], report["matched_capabilities"])
        self.assertFalse(report["human_review_required"])

    def test_complementary_extension_is_preserved(self):
        candidate = capability("external.demo", triggers=["adapt external skill"], outputs=["portable skill package", "lineage proposal"], domains=["skill authoring", "source lineage"], tools=["filesystem"])
        existing = capability("skills/meta/skill-authoring", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"], tools=["filesystem"])
        report = self.run_match(candidate, [existing])
        self.assertEqual("EXTEND", report["decision"])
        self.assertTrue(report["human_review_required"])
        output_evidence = report["comparisons"][0]["evidence"]["outputs"]
        self.assertEqual(["lineage proposal"], output_evidence["candidate_only"])
        self.assertEqual("fixture/SKILL.md", output_evidence["candidate_only_evidence"]["lineage proposal"][0]["source_path"])

    def test_explicit_conflict_fails_closed_and_escalates(self):
        candidate = capability("external.demo", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"], conflicts=["skills/meta/skill-authoring"])
        existing = capability("skills/meta/skill-authoring", triggers=["adapt external skill"], outputs=["different output"], domains=["skill authoring"])
        report = self.run_match(candidate, [existing])
        self.assertEqual("REJECT", report["decision"])
        self.assertTrue(report["escalation_required"])
        self.assertEqual([existing["identity"]], report["conflicts"])

    def test_same_trigger_and_domain_with_disjoint_outputs_escalates(self):
        candidate = capability("external.demo", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"])
        existing = capability("skills/meta/skill-authoring", triggers=["adapt external skill"], outputs=["evaluate an existing skill"], domains=["skill authoring"])
        report = self.run_match(candidate, [existing])
        self.assertEqual("REJECT", report["decision"])
        self.assertEqual("SAME_TRIGGER_DOMAIN_DISJOINT_OUTPUTS", report["comparisons"][0]["conflict_basis"])

    def test_composes_multiple_compatible_capabilities(self):
        candidate = capability("external.demo", triggers=["adapt external skill", "review imported skill"], outputs=["portable skill package", "lineage proposal"], domains=["skill authoring", "source lineage"])
        existing = [
            capability("skills/meta/skill-authoring", triggers=["adapt external skill"], outputs=["portable skill package"], domains=["skill authoring"]),
            capability("skills/meta/skill-specification", triggers=["review imported skill"], outputs=["lineage proposal"], domains=["source lineage"]),
        ]
        report = self.run_match(candidate, existing)
        self.assertEqual("COMPOSE", report["decision"])
        self.assertEqual(2, len(report["matched_capabilities"]))

    def test_unknown_core_evidence_and_incomplete_inventory_fail_closed(self):
        candidate = capability("external.demo", triggers=["package"], outputs=["package"], domains=["authoring"])
        candidate["facets"]["triggers"] = None
        existing = capability("skills/x", triggers=["x"], outputs=["y"], domains=["z"])
        self.assertEqual("REJECT", self.run_match(candidate, [existing])["decision"])
        candidate = capability("external.demo", triggers=["new trigger"], outputs=["new output"], domains=["new domain"])
        report = self.run_match(candidate, [], complete=False)
        self.assertIn("INVENTORY_INCOMPLETE", report["reason_codes"])
        self.assertEqual("REJECT", report["decision"])


    def test_unknown_permissions_or_dependencies_fail_closed(self):
        candidate = capability("external.demo", triggers=["new trigger"], outputs=["new output"], domains=["new domain"])
        candidate["facets"]["permissions"] = None
        report = self.run_match(candidate, [])
        self.assertEqual("REJECT", report["decision"])
        self.assertIn("UNKNOWN_CAPABILITY_EVIDENCE", report["reason_codes"])

    def test_all_facets_are_present_even_if_explicitly_unknown(self):
        candidate = capability("external.demo", triggers=["x"], outputs=["y"], domains=["z"])
        del candidate["facets"]["permissions"]
        with self.assertRaisesRegex(matcher.CapabilityError, "permissions must be present"):
            self.run_match(candidate, [])

    def test_phrase_normalization_is_deterministic_and_evidence_is_sorted(self):
        candidate = capability("External.Demo", triggers=["  ADAPT   External Skill "], outputs=["Package"], domains=["Skill Authoring"])
        existing = capability("skills/example", triggers=["adapt external skill"], outputs=["package"], domains=["skill authoring"])
        self.assertEqual("REUSE_EXISTING", self.run_match(candidate, [existing])["decision"])
        self.assertEqual(self.run_match(candidate, [existing]), self.run_match(candidate, [existing]))


if __name__ == "__main__":
    unittest.main()
