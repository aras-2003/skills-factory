"""Executable source checks for the worked #766 multi-consumer decision."""

import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "docs/architecture/decisions/2026-11-load-skill-source-pin.md"
BASELINE_RE = re.compile(r"^- Baseline source SHA: `([0-9a-f]{40})`$", re.MULTILINE)
EXPECTED_BASELINE = "e0f613cbaf80cf4a278e713794662250dab2b8bc"


def source_at(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "show", f"{revision}:{path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )


class ArchitectureSourceExampleTests(unittest.TestCase):
    def test_rollback_requires_caller_compatibility_before_reverting_v1_schema(self):
        decision = DECISION.read_text(encoding="utf-8")
        self.assertIn("## Rollback boundary", decision)
        self.assertRegex(
            decision,
            r"(?is)rollback boundary.*?before any caller sends `expected_source_revision`.*?"
            r"callers? must stop sending the field.*?server must never silently ignore.*?"
            r"exact error shape for invalid or stale revisions remains owner-gated",
        )

    def test_arch02_and_arch03_example_matches_two_pinned_backend_contracts(self):
        decision = DECISION.read_text(encoding="utf-8")
        match = BASELINE_RE.search(decision)
        self.assertIsNotNone(match, "decision must carry an exact baseline SHA")
        baseline = match.group(1)
        self.assertEqual(EXPECTED_BASELINE, baseline)
        self.assertEqual(
            baseline,
            subprocess.check_output(
                ["git", "--no-replace-objects", "rev-parse", "--verify", "--end-of-options", f"{baseline}^{{commit}}"],
                cwd=ROOT,
                text=True,
            ).strip(),
        )

        contract_path = "runtime/contracts/mcp-tools-v1.json"
        contract = json.loads(source_at(baseline, contract_path))
        self.assertEqual(["skill_name"], contract["tools"]["load_skill"])
        self.assertIn(f"{contract_path}#L6-L8", decision)

        python_server_path = "runtime/mcp/server.py"
        python_server = source_at(baseline, python_server_path)
        self.assertIn('def load_skill(skill_name: str', python_server)
        self.assertIn('"load_skill", {"skill_name": skill_name}', python_server)
        self.assertIn(f"{python_server_path}#L297-L303", decision)

        package_path = "runtime/mcp/skill_catalog.py"
        package = source_at(baseline, package_path)
        self.assertIn('def load_skill(skill_name: str)', package)
        self.assertIn('"source_revision": packaged_runtime_value("source_revision")', package)
        self.assertIn(f"{package_path}#L237-L272", decision)

        cloud_path = "adapters/skills-factory-cloud-next/src/cloud-tools.ts"
        cloud = source_at(baseline, cloud_path).splitlines()
        self.assertEqual(
            '  load_skill: z.object({ skill_name: z.string().trim().min(1).max(160) }).strict(),',
            cloud[27],
        )
        self.assertTrue(any('name: "load_skill"' in line and 'required: ["skill_name"]' in line
                            for line in cloud[125:131]))
        self.assertTrue(any("export function loadSkill(skillName: string)" in line for line in cloud))
        self.assertIn(f"{cloud_path}#L25-L29", decision)
        self.assertIn("#L182-L186", decision)
        self.assertIn("cloud-tools.ts#L128-L130", decision)

        self.assertIn("Status: `REVIEW_REQUIRED`", decision)
        self.assertIn("Candidate SHA: `NOT_CREATED`", decision)
        self.assertIn("`ARCH-02` remains `NOT_RUN`", decision)


if __name__ == "__main__":
    unittest.main()
