from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]


class WebsiteQualityReviewContractTests(unittest.TestCase):
    def test_suite_covers_review_and_near_misses_without_runtime_claims(self) -> None:
        skill = (ROOT / "skills/web-design/website-quality-review/SKILL.md").read_text()
        suite = yaml.safe_load((ROOT / "skills/web-design/website-quality-review/tests/cases.yaml").read_text())
        cases = suite["cases"]
        self.assertEqual(6, len(cases))
        self.assertIn("read-only", skill)
        self.assertIn("desktop", skill)
        self.assertIn("mobile", skill)
        self.assertIn("NOT_RUN", skill)
        self.assertIn("BLOCKED", skill)
        self.assertGreaterEqual(sum(c["expected"]["should_trigger"] is True for c in cases), 2)
        self.assertGreaterEqual(sum(c["expected"]["should_trigger"] is False for c in cases), 2)
        self.assertTrue(all(c["expected"].get("must_not") for c in cases))


if __name__ == "__main__":
    unittest.main()
