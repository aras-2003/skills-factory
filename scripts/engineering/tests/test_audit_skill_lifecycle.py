from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "audit_skill_lifecycle.py"
spec = importlib.util.spec_from_file_location("audit_skill_lifecycle", HERE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def seed(root: Path, name: str = "example", cases: str | None = None) -> Path:
    skill = root / "skills" / "demo" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: example\ndescription: Use when a user requests a repeatable demo review, not a related calculation.\n'
        'metadata:\n  owner: owner\n  version: "1.0.0"\n  maturity: candidate\n'
        '  risk: low\n  last_reviewed: "2026-10-09"\n---\n'
        '# Example\n## Purpose\nReview examples.\n## Procedure\nCheck requirements.\n'
        '## Output contract\nReturn findings.\n', encoding="utf-8",
    )
    if cases is not None:
        test = skill / "tests" / "cases.yaml"
        test.parent.mkdir()
        test.write_text(cases, encoding="utf-8")
    return skill / "SKILL.md"


SUITE = """cases:
  - id: a
    case: direct positive
    input: Evaluate a demo request
    expected: {should_trigger: true, must: [review intent]}
  - id: b
    case: indirect positive
    input: Could you inspect a related demo?
    expected: {should_trigger: true, must: [review intent]}
  - id: c
    case: adjacent negative
    input: Perform a demo calculation instead
    expected: {should_trigger: false, must_not: [invoke review]}
  - id: d
    case: competitor near miss
    input: Calculate a demo score, do not review the content
    expected: {should_trigger: false, must_not: [invoke review]}
"""


class LifecycleAuditTests(unittest.TestCase):
    def test_complete_static_fixture_does_not_claim_runtime_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed(root, cases=SUITE)
            report = mod.audit(root)
            self.assertEqual(1, report["total_skills"])
            self.assertEqual("NOT_RUN", report["runtime_execution"])
            self.assertEqual("NOT_VERIFIED", report["runtime_behavioral_acceptance"])
            row = report["skills"][0]
            self.assertEqual(2, row["positive_cases"])
            self.assertEqual(2, row["negative_cases"])
            self.assertTrue(row["semantic_review"] == "REQUIRED")
            self.assertEqual("REVIEW_REQUIRED", row["status"])  # edge-case heuristic

    def test_zero_negatives_are_blocker_and_one_negative_is_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = seed(root, cases=SUITE)
            file = path.parent / "tests" / "cases.yaml"
            file.write_text(SUITE.split("  - id: c")[0], encoding="utf-8")
            result = mod.examine(path, root)
            self.assertEqual("STATIC_BLOCKER", result["status"])
            self.assertIn("ROUTING_POLARITY", {x["code"] for x in result["issues"]})
            file.write_text(SUITE.split("  - id: d")[0], encoding="utf-8")
            result = mod.examine(path, root)
            self.assertEqual("REVIEW_REQUIRED", result["status"])
            self.assertIn("NEAR_MISS_DIVERSITY", {x["code"] for x in result["issues"]})

    def test_nested_skill_package_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed(root, name="example", cases=SUITE)
            nested = root / "skills" / "oaf" / "enterprise-architecture" / "nested-skill"
            nested.mkdir(parents=True)
            source = (root / "skills" / "demo" / "example" / "SKILL.md").read_text(encoding="utf-8")
            (nested / "SKILL.md").write_text(source.replace("name: example", "name: nested-skill"), encoding="utf-8")
            (nested / "tests").mkdir()
            (nested / "tests" / "cases.yaml").write_text(SUITE, encoding="utf-8")
            report = mod.audit(root)
            self.assertEqual(2, report["total_skills"])

    def test_missing_suite_and_invalid_frontmatter_do_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = seed(root)
            self.assertEqual("STATIC_BLOCKER", mod.examine(path, root)["status"])
            path.write_text("broken frontmatter", encoding="utf-8")
            self.assertIn("FRONTMATTER_INVALID", {
                x["code"] for x in mod.examine(path, root)["issues"]
            })

    def test_real_catalog_is_audited_without_skipping_skills(self):
        root = HERE.parents[2]
        report = mod.audit(root)
        from yaml import safe_load
        from pathlib import Path
        actual = len(list((root / "skills").rglob("SKILL.md")))
        self.assertEqual(actual, report["total_skills"])
        self.assertEqual(len({row["name"] for row in report["skills"]}), actual)
        self.assertTrue(all(row["runtime_evidence"] == "NOT_RUN" for row in report["skills"]))


if __name__ == "__main__":
    unittest.main()
