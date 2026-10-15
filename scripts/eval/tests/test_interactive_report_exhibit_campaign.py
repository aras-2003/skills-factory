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
import interactive_report_exhibit_campaign as exhibit_campaign


class InteractiveReportExhibitCampaignTests(unittest.TestCase):
    def test_exact_candidate_paths_have_a_separate_not_run_handoff(self):
        self.assertEqual([], exhibit_campaign.validate())
        self.assertEqual(
            exhibit_campaign.EXPECTED_PATHS,
            campaign.separately_validated_interactive_report_exhibit_paths(ROOT),
        )
        self.assertEqual([], campaign.validate_campaign())

    def test_expanding_declared_paths_revokes_behavior_pin_exclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = exhibit_campaign.CONFIG_REL
            dst = root / rel
            dst.parent.mkdir(parents=True)
            shutil.copy2(ROOT / rel, dst)
            for source in exhibit_campaign.EXPECTED_PATHS:
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source, path)
            data = yaml.safe_load(dst.read_text())
            data["out_of_scope_behavior_paths"].append("skills/other/SKILL.md")
            dst.write_text(yaml.safe_dump(data))
            self.assertEqual(set(), campaign.separately_validated_interactive_report_exhibit_paths(root))

    def test_not_run_and_no_release_approval_are_mandatory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = exhibit_campaign.CONFIG_REL
            dst = root / rel
            dst.parent.mkdir(parents=True)
            shutil.copy2(ROOT / rel, dst)
            for source in exhibit_campaign.EXPECTED_PATHS:
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source, path)
            data = yaml.safe_load(dst.read_text())
            data["runtime_status"] = "PASS"
            data["release_approved"] = True
            dst.write_text(yaml.safe_dump(data))
            self.assertEqual(set(), campaign.separately_validated_interactive_report_exhibit_paths(root))

    def test_candidate_requires_six_frozen_cases_per_skill(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = exhibit_campaign.CONFIG_REL
            dst = root / rel
            dst.parent.mkdir(parents=True)
            shutil.copy2(ROOT / rel, dst)
            for source in exhibit_campaign.EXPECTED_PATHS:
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source, path)
            report_tests = root / "skills/meta/report-composer/tests/cases.yaml"
            report_tests.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "skills/meta/report-composer/tests/cases.yaml", report_tests)
            visual_tests = root / "skills/meta/visual-output-design/tests/cases.yaml"
            visual_tests.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "skills/meta/visual-output-design/tests/cases.yaml", visual_tests)
            for name in ("report-composer", "visual-output-design"):
                source = root / f"skills/meta/{name}/SKILL.md"
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / f"skills/meta/{name}/SKILL.md", source)
            data = yaml.safe_load(dst.read_text())
            data["candidate_skills"]["report-composer"]["required_case_ids"].pop()
            dst.write_text(yaml.safe_dump(data))
            self.assertEqual(set(), campaign.separately_validated_interactive_report_exhibit_paths(root))


if __name__ == "__main__":
    unittest.main()
