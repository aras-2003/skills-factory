import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/web-design/interface-design/SKILL.md"
CASES = ROOT / "skills/web-design/interface-design/tests/cases.yaml"


class InterfaceDesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SKILL.read_text(encoding="utf-8")
        match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", source, re.S)
        if not match:
            raise AssertionError("SKILL.md must have valid YAML frontmatter")
        cls.metadata = yaml.safe_load(match.group(1))
        cls.body = match.group(2)
        cls.cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]

    def test_candidate_metadata_and_identity(self):
        self.assertEqual(self.metadata["name"], "interface-design")
        self.assertEqual(self.metadata["metadata"]["maturity"], "candidate")
        self.assertEqual(self.metadata["metadata"]["version"], "0.1.3")

    def test_contract_sections_are_present(self):
        for section in (
            "## Purpose", "## Use when", "## Do not use when", "## Inputs",
            "## Procedure", "## Decision rules", "## Output contract", "## Quality checks",
        ):
            with self.subTest(section=section):
                self.assertIn(section, self.body)
        for required in ("Information hierarchy", "Responsive behavior", "States", "Accessibility"):
            with self.subTest(output=required):
                self.assertIn(required, self.body)

    def test_mobile_desktop_and_error_states_are_explicit(self):
        self.assertIn("mobile", self.body.lower())
        self.assertIn("desktop", self.body.lower())
        for state in ("loading", "empty", "error"):
            with self.subTest(state=state):
                self.assertIn(state, self.body.lower())

    def test_missing_data_uses_placeholders_instead_of_fabricated_records(self):
        self.assertIn("[order ID]", self.body)
        self.assertIn("[delay duration]", self.body)
        self.assertIn("do not fabricate populated records", self.body.lower())
        direct = next(c for c in self.cases if c["id"] == "interface-design-direct-positive")
        self.assertTrue(any("invent order data" in text.lower() for text in direct["expected"]["must_not"]))

    def test_fixtures_cover_positive_nearmiss_and_edge_cases(self):
        ids = {case["id"] for case in self.cases}
        self.assertGreaterEqual(len(self.cases), 6)
        self.assertIn("interface-design-direct-positive", ids)
        self.assertIn("interface-design-indirect-positive", ids)
        self.assertIn("interface-design-nearmiss-report-diagram", ids)
        self.assertIn("interface-design-nearmiss-implementation", ids)
        self.assertIn("interface-design-insufficient-context", ids)
        self.assertIn("interface-design-accessibility-edge", ids)

    def test_nearmisses_do_not_trigger_design_only_work(self):
        by_id = {case["id"]: case for case in self.cases}
        for case_id in (
            "interface-design-nearmiss-report-diagram",
            "interface-design-nearmiss-implementation",
        ):
            with self.subTest(case=case_id):
                self.assertFalse(by_id[case_id]["expected"]["should_trigger"])

    def test_permission_denial_is_not_conflated_with_empty_state(self):
        case = next(c for c in self.cases if c["id"] == "interface-design-accessibility-edge")
        joined = " ".join(case["expected"]["must"] + case["expected"]["must_not"]).lower()
        self.assertIn("permission", joined)
        self.assertIn("empty state", joined)

    def test_missing_context_gate_is_clarification_only(self):
        self.assertIn("entire response must be that clarification question", self.body)
        self.assertIn("do not add an introduction, examples, suggestions, a checklist", self.body)

    def test_product_unknowns_are_not_presented_as_existing_ui(self):
        self.assertIn("Do not present plausible labels or example content as existing product behavior", self.body)
        self.assertIn("Do not create an interactive preview, prototype, wireframe artifact", self.body)

    def test_indirect_flow_keeps_failure_recovery(self):
        self.assertIn("include at least one realistic failure path and its recovery", self.body)


if __name__ == "__main__":
    unittest.main()
