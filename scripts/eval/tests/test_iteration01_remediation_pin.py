from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/eval'))
import campaign

REL = 'evals/campaigns/iteration-01-runtime-remediation-2026-10/source-coverage.json'

class Iteration01RemediationPinTests(unittest.TestCase):
    def test_only_exact_workflow_and_registry_are_covered(self):
        self.assertEqual({'workflows/investment-attention-review/WORKFLOW.md', 'workflows/runtime-registry.yaml'},
                         campaign.separately_validated_iteration01_paths(ROOT))

    def test_invalid_coverage_keeps_behavior_inside_historical_pin(self):
        for mutation in ('path', 'revision', 'retest', 'executed', 'assertions'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for rel in (REL, 'evals/campaigns/iteration-01-safety-governance-2026-10/campaign.json',
                            'workflows/runtime-registry.yaml', 'workflows/investment-attention-review/WORKFLOW.md',
                            'workflows/investment-attention-review/tests/cases.yaml'):
                    target = root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / rel, target)
                cfg = json.loads((root / REL).read_text())
                if mutation == 'path':
                    cfg['out_of_scope_behavior_paths'].append('skills/another/SKILL.md')
                elif mutation == 'revision':
                    cfg['frozen_campaign_sha256'] = '0' * 64
                elif mutation == 'retest':
                    cfg['required_frozen_retests'] = ['I01-GOV-001']
                elif mutation == 'executed':
                    cfg['runtime_status'] = 'PASS'
                else:
                    (root / 'workflows/investment-attention-review/tests/cases.yaml').write_text('cases: []\n')
                (root / REL).write_text(json.dumps(cfg))
                self.assertEqual(set(), campaign.separately_validated_iteration01_paths(root))

if __name__ == '__main__':
    unittest.main()
