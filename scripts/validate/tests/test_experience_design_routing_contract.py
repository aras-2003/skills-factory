import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
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
        cls.cases = {
            case["id"]: case
            for case in yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]
        }

    def test_candidate_identity_and_required_routes(self):
        self.assertEqual("experience-design-routing", self.metadata["name"])
        self.assertEqual("candidate", self.metadata["metadata"]["maturity"])
        for case_id in (
            "ux-route-design",
            "ux-route-critique",
            "ux-route-handoff",
            "ux-route-accessibility",
            "ux-route-visual-regression",
        ):
            with self.subTest(case=case_id):
                self.assertTrue(self.cases[case_id]["expected"]["should_trigger"])

    def test_near_misses_preserve_existing_output_intent(self):
        for case_id in (
            "ux-near-miss-report",
            "ux-near-miss-chart",
            "ux-near-miss-ordinary-answer",
        ):
            with self.subTest(case=case_id):
                self.assertFalse(self.cases[case_id]["expected"]["should_trigger"])
        self.assertIn("do not change the requested response format", self.body.lower())
        self.assertIn("single chart request", self.body.lower())

    def test_domain_provenance_fixture_is_frozen(self):
        case = self.cases["ux-route-provenance-preservation"]
        self.assertTrue(case["expected"]["should_trigger"])
        prompt = case["input"]
        for token in (
            "finding ID F-17",
            "source revision abcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "as-of date 2026-10-15",
            "uncertainty: low confidence",
            "written interface brief",
        ):
            with self.subTest(token=token):
                self.assertIn(token, prompt)
        self.assertIn(
            "Preserve each domain's evidence IDs, source revision, as-of date, uncertainty and output contract.",
            self.body,
        )

    def test_missing_artifact_does_not_imply_approval_or_code_edits(self):
        case = self.cases["ux-implementation-approval"]
        self.assertTrue(case["expected"]["should_trigger"])
        self.assertTrue(any("edit repository" in value for value in case["expected"]["must_not"]))
        self.assertIn("Do not infer permission to edit code", self.body)

    def test_unsupported_surface_is_not_reported_as_pass(self):
        self.assertIn("Chat, mobile, Cloud or Codex", self.body)
        self.assertIn("unsupported surface is `NOT_RUN`, not PASS", self.body)


if __name__ == "__main__":
    unittest.main()
