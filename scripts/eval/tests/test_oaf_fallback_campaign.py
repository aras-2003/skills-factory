from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import campaign

CONFIG = Path("evals/campaigns/oaf-health-check-fallback-2026-10/campaign.yaml")
WORKFLOW = "workflows/oaf-health-check/WORKFLOW.md"


class OafFallbackCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        cfg = yaml.safe_load((ROOT / CONFIG).read_text())
        for rel in [CONFIG, "workflows/runtime-registry.yaml", "evals/runtime-fixtures.yaml", *cfg["source_sha256"]]:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)

    def check(self):
        return campaign.separately_validated_oaf_fallback_paths(self.root)

    def test_only_exact_case_covered_candidate_is_separate_from_r20(self):
        self.assertEqual({WORKFLOW}, self.check())
        self.assertEqual({WORKFLOW}, campaign.separately_validated_oaf_fallback_paths(ROOT))

    def test_source_drift_revokes_scope(self):
        path = self.root / WORKFLOW
        path.write_text(path.read_text() + "\nChanged behavior.\n")
        self.assertEqual(set(), self.check())

    def test_removed_fixture_revokes_scope(self):
        (self.root / "evals/oaf-health-check/fallback-strategy-disabled-lab-001.input.md").unlink()
        self.assertEqual(set(), self.check())

    def test_expanded_scope_or_fabricated_pass_is_rejected(self):
        path = self.root / CONFIG
        original = yaml.safe_load(path.read_text())
        for field, value in (("runtime_status", "PASS"), ("release_approved", True),
                             ("out_of_scope_behavior_paths", [WORKFLOW, "skills/other/SKILL.md"])):
            with self.subTest(field=field):
                data = dict(original)
                data[field] = value
                path.write_text(yaml.safe_dump(data))
                self.assertEqual(set(), self.check())


if __name__ == "__main__":
    unittest.main()
