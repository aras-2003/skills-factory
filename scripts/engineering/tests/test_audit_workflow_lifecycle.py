from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "audit_workflow_lifecycle.py"
spec = importlib.util.spec_from_file_location("audit_workflow_lifecycle", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class WorkflowProcessAuditTests(unittest.TestCase):
    def test_all_registered_workflows_and_runtime_remain_unverified(self):
        root = SCRIPT.parents[2]
        report = mod.audit(root)
        self.assertEqual(16, report["total"])
        self.assertEqual(16, len({x["name"] for x in report["workflows"]}))
        self.assertEqual("NOT_RUN", report["runtime"])
        self.assertEqual("REQUIRED", report["semantic_review"])
        self.assertFalse(report["statuses"].get("STATIC_BLOCKER", 0), report["workflows"])
        self.assertTrue(all(x["runtime_evidence"] == "NOT_RUN" and x["runtime_outcome"] is None
                            for x in report["workflows"]))

    def test_central_fixture_coverage_is_not_misreported_as_absent(self):
        root = SCRIPT.parents[2]
        report = mod.audit(root)
        rows = {x["name"]: x for x in report["workflows"]}
        self.assertGreater(rows["commerce-product-deep-dive"]["central_eval_case_count"], 0)
        self.assertNotIn(
            "NO_LOCAL_OR_CENTRAL_WORKFLOW_SUITE_CHECK_ALTERNATE_CAMPAIGNS",
            rows["commerce-product-deep-dive"]["review_signals"],
        )
        # A central fixture count of zero is not a missing-test warning when a
        # source workflow already has an isolated local tests/cases.yaml suite.
        for name in ("oaf-strategy-execution-reset", "investment-os-review", "investment-portfolio-observation"):
            with self.subTest(workflow=name):
                self.assertEqual(0, rows[name]["central_eval_case_count"])
                self.assertTrue(rows[name]["local_test_suite_present"])
                self.assertNotIn(
                    "NO_LOCAL_OR_CENTRAL_WORKFLOW_SUITE_CHECK_ALTERNATE_CAMPAIGNS",
                    rows[name]["review_signals"],
                )

    def test_no_local_or_central_cases_is_a_review_signal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "workflows" / "demo" / "WORKFLOW.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "# Demo\n\n## Purpose\nReview requests.\n\n## Sequence\n"
                "Validate.\n\n## Output contract\nGive a summary.\n"
                "## Stop conditions\nStop without evidence.\n",
                encoding="utf-8",
            )
            (root / "workflows" / "runtime-registry.yaml").write_text(
                'workflows:\n  - name: demo\n    workflow: workflows/demo/WORKFLOW.md\n'
                '    description: "Use this workflow to review a bounded request."\n'
                '    metadata: {owner: team, version: "1.0", maturity: draft, risk: low, last_reviewed: "2026-10-09"}\n'
                '    channels: {plugin: supported}\n'
                '    dependencies: {required: [], optional: []}\n', encoding="utf-8",
            )
            row = mod.audit(root)["workflows"][0]
            self.assertFalse(row["local_test_suite_present"])
            self.assertEqual(0, row["central_eval_case_count"])
            self.assertIn("NO_LOCAL_OR_CENTRAL_WORKFLOW_SUITE_CHECK_ALTERNATE_CAMPAIGNS", row["review_signals"])

    def test_invalid_missing_path_or_metadata_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workflows").mkdir()
            (root / "workflows" / "runtime-registry.yaml").write_text(
                'workflows:\n  - name: bad\n    workflow: workflows/missing/WORKFLOW.md\n'
                '    channels: {plugin: supported}\n'
                '    dependencies: {required: [], optional: []}\n'
                '    description: "Use this workflow for a real request."\n',
                encoding="utf-8",
            )
            r = mod.audit(root)
            self.assertEqual(1, r["statuses"]["STATIC_BLOCKER"])
            self.assertIn("registered WORKFLOW.md missing", r["workflows"][0]["errors"])

    def test_unregistered_workflow_is_not_silently_included(self):
        root = SCRIPT.parents[2]
        r = mod.audit(root)
        self.assertNotIn("skill-development", [x["name"] for x in r["workflows"]])
        self.assertTrue((root / "workflows/skill-development/WORKFLOW.md").is_file())


if __name__ == "__main__":
    unittest.main()
