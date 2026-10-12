from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/eval/campaign.py"
spec = importlib.util.spec_from_file_location("runtime_campaign", SCRIPT)
campaign = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(campaign)


class InvestmentStoreCampaignPinTests(unittest.TestCase):
    def test_exact_unexecuted_campaign_covers_only_store_skill(self) -> None:
        self.assertEqual(
            {"skills/investing/investment-record-store/SKILL.md"},
            campaign.separately_validated_investment_store_paths(ROOT),
        )

    def test_campaign_cannot_exempt_a_different_behavior_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = root / "evals/campaigns/investment-store-bootstrap-followup-2026-10"
            campaign_dir.mkdir(parents=True)
            skill_path = root / "skills/investing/investment-record-store/SKILL.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text('version: "1.0.2"\\n', encoding="utf-8")
            cfg = json.loads(
                (ROOT / "evals/campaigns/investment-store-bootstrap-followup-2026-10/campaign.json")
                .read_text(encoding="utf-8")
            )
            cfg["out_of_scope_behavior_paths"] = ["skills/another-skill/SKILL.md"]
            (campaign_dir / "campaign.json").write_text(json.dumps(cfg), encoding="utf-8")
            self.assertEqual(set(), campaign.separately_validated_investment_store_paths(root))


if __name__ == "__main__":
    unittest.main()
