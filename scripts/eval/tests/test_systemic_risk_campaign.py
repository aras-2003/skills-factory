from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import campaign


class SystemicRiskCampaignTests(unittest.TestCase):
    def test_exact_hash_bound_scope_has_a_not_run_campaign(self) -> None:
        expected = {
            "skills/investing/investment-attention-triage/SKILL.md",
            "skills/investing/investment-attention-triage/references/systemic-risk-indicator-registry.yaml",
            "skills/investing/portfolio-state-review/SKILL.md",
            "workflows/investment-portfolio-observation/WORKFLOW.md",
        }
        self.assertEqual(expected, campaign.separately_validated_systemic_risk_paths())

    def test_source_drift_invalidates_the_exception(self) -> None:
        (campaign.ROOT / ".tmp").mkdir(exist_ok=True)
        root = Path(tempfile.mkdtemp(dir=campaign.ROOT / ".tmp"))
        self.addCleanup(shutil.rmtree, root)
        for rel in (
            "evals/campaigns/systemic-risk-signals-2026-10/campaign.yaml",
            "evals/campaigns/systemic-risk-signals-2026-10/cases.yaml",
            "skills/investing/investment-attention-triage/SKILL.md",
            "skills/investing/investment-attention-triage/references/systemic-risk-indicator-registry.yaml",
            "skills/investing/portfolio-state-review/SKILL.md",
            "workflows/investment-portfolio-observation/WORKFLOW.md",
            "scripts/validate/tests/test_integrated_reporting.py",
            "skills/investing/investment-attention-triage/tests/cases.yaml",
        ):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(campaign.ROOT / rel, target)
        changed = root / "skills/investing/portfolio-state-review/SKILL.md"
        changed.write_text(changed.read_text() + "\nchanged\n", encoding="utf-8")
        self.assertEqual(set(), campaign.separately_validated_systemic_risk_paths(root))


if __name__ == "__main__":
    unittest.main()
