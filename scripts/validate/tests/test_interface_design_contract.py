import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
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
        cls.cases = {
            case["id"]: case
            for case in yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]
        }

    def test_candidate_identity_and_explicit_opening_article(self):
        self.assertEqual("interface-design", self.metadata["name"])
        self.assertEqual("0.1.19", self.metadata["metadata"]["version"])
        self.assertEqual("candidate", self.metadata["metadata"]["maturity"])
        self.assertIn(
            "I’ll use interface-design for the <screen or flow name>.", self.body
        )
        self.assertIn('Keep the definite article “the” before the name', self.body)
        self.assertIn("Do not omit “the”", self.body)

    def test_positive_case_openers_match_the_required_exact_template(self):
        for case_id in (
            "interface-design-direct-positive",
            "interface-design-indirect-positive",
            "interface-design-accessibility-edge",
        ):
            with self.subTest(case=case_id):
                expected = self.cases[case_id]["expected"]["must"]
                opener = next(
                    value.removeprefix("begin with the unformatted sentence ").strip('"')
                    for value in expected
                    if value.startswith("begin with the unformatted sentence ")
                )
                self.assertTrue(opener.startswith("I’ll use interface-design for the "))
                self.assertTrue(opener.endswith("."))

    def test_derived_onboarding_label_includes_article_without_problem_text(self):
        opener = next(
            value.removeprefix("begin with the unformatted sentence ").strip('"')
            for value in self.cases["interface-design-indirect-positive"]["expected"]["must"]
            if value.startswith("begin with the unformatted sentence ")
        )
        self.assertEqual(
            "I’ll use interface-design for the mobile-first onboarding flow.", opener
        )
        self.assertIn(
            'derive a short noun phrase from the requested deliverable', self.body
        )

    def test_clarification_only_case_remains_a_single_exact_question(self):
        expected = self.cases["interface-design-insufficient-context"]["expected"]["must"]
        question = next(value for value in expected if value.startswith('When all three fields'))
        self.assertIn("ask exactly:", question)
        exact_question = (
            "For an interface-design brief, what screen or flow should change, "
            "who will use it and what task should they complete, and should it "
            "target mobile, desktop, or a specific runtime?"
        )
        self.assertIn("copy and return this plain-text line verbatim and alone", self.body)
        self.assertIn(f"\n{exact_question}\n", self.body)
        self.assertIn("no quotation marks, code formatting, introduction, translation, paraphrase", self.body)


if __name__ == "__main__":
    unittest.main()
