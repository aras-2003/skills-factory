import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/web-design/experience-design-routing/SKILL.md"
CASES = ROOT / "skills/web-design/experience-design-routing/tests/cases.yaml"


class ExperienceDesignRoutingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SKILL.read_text(encoding="utf-8")
        match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", source, re.S)
        if not match:
            raise AssertionError("SKILL.md must have valid YAML frontmatter")
        cls.metadata = yaml.safe_load(match.group(1))
        cls.body = match.group(2)
        cls.cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]
        cls.cases_by_id = {case["id"]: case for case in cls.cases}

    def test_candidate_identity_and_portability_boundary(self):
        self.assertEqual(self.metadata["name"], "experience-design-routing")
        self.assertEqual(self.metadata["metadata"]["maturity"], "candidate")
        self.assertEqual(self.metadata["metadata"]["version"], "0.1.1")
        self.assertIn("## Portability boundary", self.body)
        self.assertIn("confirm the actual host surface and tool receipt", self.body)
        self.assertIn("NOT_RUN, not PASS", self.body)

    def test_specialist_routes_remain_explicit_and_non_overlapping(self):
        for route in (
            "Design a new screen or short product flow: `interface-design`.",
            "Critique a supplied visual artifact and propose repairs: `design-critique`.",
            "Convert an approved concept into an engineering handoff: `implementation-brief`.",
            "Review implementation accessibility evidence and gaps: `accessibility-gate`.",
            "Compare a rendering to an approved baseline: `visual-regression-review`.",
        ):
            with self.subTest(route=route):
                self.assertIn(route, self.body)

    def test_near_misses_preserve_report_chart_and_plain_text_intent(self):
        expectations = {
            "ux-near-miss-report": "report",
            "ux-near-miss-chart": "chart",
            "ux-near-miss-ordinary-answer": "ordinary text",
        }
        for case_id, label in expectations.items():
            case = self.cases_by_id[case_id]
            with self.subTest(case=case_id):
                self.assertFalse(case["expected"]["should_trigger"], label)
                self.assertTrue(case["expected"].get("must_not"))
        ordinary = self.cases_by_id["ux-near-miss-ordinary-answer"]["expected"]["must_not"]
        self.assertTrue(any("change the requested response format" in item for item in ordinary))

    def test_domain_provenance_is_a_required_positive_case(self):
        case = self.cases_by_id["ux-route-provenance-preservation"]
        self.assertTrue(case["expected"]["should_trigger"])
        required = " ".join(case["expected"]["must"]).lower()
        for field in ("finding id f-17", "source revision", "as-of date 2026-10-15", "uncertainty", "low confidence"):
            with self.subTest(field=field):
                self.assertIn(field, required)
        self.assertIn("Preserve each domain's evidence IDs, source revision, as-of date, uncertainty and output contract.", self.body)

    def test_fixture_matrix_covers_each_specialist_and_code_boundary(self):
        required_ids = {
            "ux-route-design",
            "ux-route-critique",
            "ux-route-handoff",
            "ux-route-accessibility",
            "ux-route-visual-regression",
            "ux-near-miss-report",
            "ux-near-miss-chart",
            "ux-near-miss-ordinary-answer",
            "ux-route-provenance-preservation",
            "ux-implementation-approval",
            "ux-near-miss-implementation-request",
        }
        self.assertTrue(required_ids.issubset(self.cases_by_id))
        for case_id in required_ids:
            case = self.cases_by_id[case_id]
            expected = case["expected"]
            with self.subTest(case=case_id):
                self.assertIsInstance(expected.get("should_trigger"), bool)
                self.assertTrue(expected.get("must"))
                self.assertTrue(expected.get("must_not"))

    def test_explicit_implementation_is_not_replaced_by_design(self):
        case = self.cases_by_id["ux-near-miss-implementation-request"]
        self.assertFalse(case["expected"]["should_trigger"])
        self.assertIn("direct the request to the implementation workflow", " ".join(case["expected"]["must"]))
        self.assertIn("do not replace implementation", " ".join(case["expected"]["must_not"]).lower())


if __name__ == "__main__":
    unittest.main()
