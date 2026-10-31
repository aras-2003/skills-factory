from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
EVAL = ROOT / "scripts/eval"
if str(EVAL) not in sys.path:
    sys.path.insert(0, str(EVAL))
import campaign

NAMES = {
    "oaf-strategy-execution-reset",
    "investment-attention-review",
    "investment-security-review",
    "investment-theme-discovery",
}
SCOPED = {f"workflows/{name}/WORKFLOW.md" for name in NAMES}
CAMPAIGN_ROOT = Path("evals/campaigns/iteration-02-workflow-hardening-2026-10")


class DedicatedWorkflowVersionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in [
            "workflows/runtime-registry.yaml",
            CAMPAIGN_ROOT / "campaign.yaml",
            CAMPAIGN_ROOT / "cases.yaml",
            *SCOPED,
        ]:
            src = ROOT / path
            dst = self.root / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def check(self):
        return campaign.separately_validated_iteration02_workflow_paths(self.root)

    def test_only_four_exact_workflows_are_separately_source_validated(self):
        self.assertEqual(SCOPED, self.check())
        self.assertEqual(SCOPED, campaign.separately_validated_iteration02_workflow_paths(ROOT))

    def test_historical_r20_source_pin_is_never_rewritten(self):
        data = yaml.safe_load((ROOT / "evals/campaigns/runtime-validation-2026-10-r20/campaign.yaml").read_text())
        self.assertEqual("914759e78bf093f569cdfba6eb57a04dc3a7a633", data["behavior_source_revision"])
        self.assertFalse(data.get("release_approved", False))

    def test_wrong_workflow_version_revokes_exemption(self):
        path = self.root / "workflows/runtime-registry.yaml"
        s = path.read_text()
        s = s.replace('version: "0.4.2"', 'version: "0.4.0"', 1)
        path.write_text(s)
        self.assertEqual(set(), self.check())

    def test_missing_or_unrecognized_fixture_does_not_exempt_any_source(self):
        path = self.root / CAMPAIGN_ROOT / "cases.yaml"
        data = yaml.safe_load(path.read_text())
        data["cases"].pop()
        path.write_text(yaml.safe_dump(data))
        self.assertEqual(set(), self.check())

    def test_removing_write_refusal_revokes_exemption(self):
        path = self.root / "workflows/investment-security-review/WORKFLOW.md"
        path.write_text(path.read_text().replace("NOT_WRITTEN", "SAVED_ALWAYS"))
        self.assertEqual(set(), self.check())

    def test_expanding_allowed_path_set_is_not_silent(self):
        path = self.root / CAMPAIGN_ROOT / "campaign.yaml"
        data = yaml.safe_load(path.read_text())
        data["out_of_scope_behavior_paths"].append("workflows/unsafe-new-flow/WORKFLOW.md")
        path.write_text(yaml.safe_dump(data))
        self.assertEqual(set(), self.check())

    def test_fabricated_runtime_pass_does_not_exempt_path(self):
        path = self.root / CAMPAIGN_ROOT / "campaign.yaml"
        data = yaml.safe_load(path.read_text())
        data["runtime_status"] = "PASS"
        path.write_text(yaml.safe_dump(data))
        self.assertEqual(set(), self.check())

    def test_negative_routing_case_requires_frozen_should_trigger_type(self):
        path = self.root / CAMPAIGN_ROOT / "cases.yaml"
        data = yaml.safe_load(path.read_text())
        data["cases"][0]["expected"]["should_trigger"] = "true"
        path.write_text(yaml.safe_dump(data))
        self.assertEqual(set(), self.check())

    def test_current_campaign_still_does_not_prove_model_behavior(self):
        config = yaml.safe_load((ROOT / CAMPAIGN_ROOT / "campaign.yaml").read_text())
        self.assertEqual("NOT_RUN", config["provider_execution"])
        self.assertEqual("NOT_RUN", config["independent_evaluation"])
        self.assertIs(config["release_approved"], False)


if __name__ == "__main__":
    unittest.main()
