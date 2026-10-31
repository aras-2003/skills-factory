Warning: truncated output (original token count: 11293)
Total output lines: 952

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import yaml

HERE = Path(__file__).resolve()
EVAL_DIR = HERE.parents[1]
ROOT = HERE.parents[3]
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

import campaign
import receipt
from common import load_campaign_cases, load_supplemental_cases
from scripts.package.build_utils import package_version


class RuntimeCampaignTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / ".tmp").mkdir(exist_ok=True)

    def test_historical_campaign_without_optional_routing_registry_does_not_read_repo_directory(self) -> None:
        from unittest.mock import patch
        from common import load_campaign_cases
        # Legacy campaign has explicit fallbacks/commerce but no routing file.
        with patch("common.load_campaign_config", return_value={
            "campaign": "historical-no-routing",
            "commerce_case_ids": [], "routing_case_ids": [],
            "executive_case_ids": [],
            "fallback_cases": [{
                "id": "fallback-synthetic", "target": "test",
                "mode": "explicit", "input": "fixture", "rubric": "fixture-rubric",
            }],
        }):
            cases = load_campaign_cases(ROOT, "historical-no-routing")
        self.assertIn("fallback-synthetic", cases)
        self.assertEqual("production-fallback", cases["fallback-synthetic"]["suite"])

    def test_orphaned_routing_ids_fail_closed(self) -> None:
        with patch("common.load_campaign_config", return_value={
            "campaign": "invalid-no-registry",
            "commerce_case_ids": [], "routing_case_ids": ["routing-001"],
            "executive_case_ids": [],
        }):
            with self.assertRaisesRegex(ValueError, "routing_case_ids set without"):
                load_campaign_cases(ROOT, "invalid-no-registry")

    def test_r20_preserves_r18_pin_and_rejects_future_behavior_drift(self) -> None:
        historical = yaml.safe_load((ROOT / 'evals/campaigns/runtime-validation-2026-10-r18/campaign.yaml').read_text())
        self.assertEqual('e51df8120031726a59f6f2acabf1bf7c021c94a4', historical['behavior_source_revision'])
        self.assertEqual('runtime-validation-2026-10-r20', campaign.config()['campaign'])
        with patch.object(campaign, 'behavior_changes', return_value=['skills/new/SKILL.md']):
            self.assertTrue(any('behavior changed after pinned SHA' in error for error in campaign.validate_campaign()))

    def test_investment_quality_candidate_is_hash_bound_and_not_runtime_approved(self) -> None:
        expected = {
            "skills/investing/security-underwriting/scripts/value_trap_gate.py",
            "skills/investing/valuation-scenario-review/SKILL.md",
            "skills/investing/valuation-scenario-review/scripts/valuation_scenarios.py",
        }
        self.assertEqual(expected, campaign.separately_validated_investment_quality_paths())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg_path = root / "evals/campaigns/investment-quality-2026-10/campaign.yaml"
            cfg_path.parent.mkdir(parents=True)
            cfg_path.write_text((ROOT / "evals/campaigns/investment-quality-2026-10/campaign.yaml").read_text())
            cfg = yaml.safe_load(cfg_path.read_text())
            for rel in expected | set(cfg["test_modules"]):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            self.assertEqual(set(), campaign.separately_validated_investment_quality_paths(root))

    def test_campaign_resolves_exact_scope_and_isolation(self) -> None:
        self.assertEqual([], campaign.validate_campaign())
        cases = load_campaign_cases(ROOT, campaign.config()["campaign"])
        self.assertEqual(42, len(cases))
        counts = {}
        for case in cases.values():
            counts[case["suite"]] = counts.get(case["suite"], 0) + 1
        self.assertEqual(
            {"commerce": 6, "routing": 22, "executive-role": 14},
            counts,
        )
        supplemental = load_supplemental_cases(ROOT, campaign.config()["campaign"])
        self.assertEqual(
            [
                "oaf-decision-bottleneck-natural-pl",
                "oaf-decision-rights-natural-pl",
                "oaf-interface-natural-pl",
            ],
            sorted(supplemental),
        )
        self.assertEqual("operating-model-review", supplemental["oaf-interface-natural-pl"]["target"])
        self.assertEqual("decision-bottleneck-analysis", supplemental["oaf-decision-bottleneck-natural-pl"]["target"])
        self.assertEqual("decision-rights-review", supplemental["oaf-decision-rights-natural-pl"]["target"])
        self.assertEqual(
            ["case-001-opportunity-hunter", "case-002-security-sizing", "case-003-portfolio-review", "case-004-theme-discovery", "case-006-attention-acn"],
            campaign.config().get("retest_focus_case_ids"),
        )

    def test_interface_design_candidate_isolated_from_frozen_r20(self) -> None:
        path = "skills/web-design/interface-design/SKILL.md"
        self.assertEqual({path}, campaign.separately_validated_interface_design_paths(ROOT))
        self.assertEqual([], campaign.validate_campaign())
        fixtures = yaml.safe_load((ROOT / "evals/runtime-fixtures.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("interface-design", fixtures["targets"])

    def test_design_critique_candidate_isolated_from_frozen_r20(self) -> None:
        path = "skills/web-design/design-critique/SKILL.md"
        self.assertEqual({path}, campaign.separately_validated_design_critique_paths(ROOT))
        self.assertEqual([], campaign.validate_campaign())
        fixtures = yaml.safe_load((ROOT / "evals/runtime-fixtures.yaml").read_text(encoding="utf-8"))
        self.assertNotIn("design-critique", fixtures["targets"])
        cases = yaml.safe_load((ROOT / "skills/web-design/design-critique/tests/cases.yaml").read_text())
        self.assertEqual(7, len(cases["cases"]))
        for case in cases["cases"]:
            for fixture in (case.get("fixtures") or {}).values():
                self.assertTrue((ROOT / "skills/web-design/design-critique/tests" / fixture).is_file())

    def test_ux04_quality_candidates_are_isolated_only_with_complete_source_contracts(self) -> None:
        paths = {
            "skills/web-design/implementation-brief/SKILL.md",
            "skills/web-design/visual-regression-review/SKILL.md",
            "skills/web-design/accessibility-gate/SKILL.md",
        }
        self.assertEqual(paths, campaign.separately_validated_web_design_quality_paths(ROOT))
        self.assertEqual([], campaign.validate_campaign())
        fixtures = yaml.safe_load((ROOT / "evals/runtime-fixtures.yaml").read_text(encoding="utf-8"))
        self.assertTrue({"implementation-brief", "visual-regression-review", "accessibility-gate"}.isdisjoint(fixtures["targets"]))
        cfg = yaml.safe_load((ROOT / "evals/campaigns/web-design-quality-2026-10/campaign.yaml").read_text())
        for candidate in cfg["candidate_skills"]:
            cases = yaml.safe_load((ROOT / candidate["test_cases"]).read_text())["cases"]
            self.assertEqual(6, len(cases))
            self.assertGreaterEqual(sum(c["expected"]["should_trigger"] is True for c in cases), 2)
            self.assertGreaterEqual(sum(c["expected"]["should_trigger"] is False for c in cases), 2)


    def test_unassigned_candidates_are_isolated_only_with_hash_bound_test_contracts(self) -> None:
        expected = {
            "skills/investing/historical-decision-replay/SKILL.md",
            "skills/investing/historical-decision-replay/scripts/engine.py",
            "skills/investing/technical-structure/SKILL.md",…7293 tokens truncated…-{name}"
                    dest = ROOT / evidence_rel / case_id / run_id
                    args = self._import_args(
                        case_id=case_id,
                        run_id=run_id,
                        lock=lock_path,
                        smoke=smoke_path,
                        output=output,
                        trace=trace,
                        status="REVIEW_REQUIRED",
                    )
                    with patch.object(campaign, "config", return_value=patched_cfg):
                        with self.assertRaisesRegex(ValueError, "invalid campaign lock"):
                            campaign.import_run(args)
                    self.assertFalse(dest.exists(), f"partial evidence written for {name}")

    def test_lock_rejects_unknown_active_import_case_before_writes(self) -> None:
        cfg = dict(campaign.config())
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            td_path = Path(td)
            prepared = td_path / "prepared"
            campaign.prepare(prepared, require_pinned_commit=False)
            lock_path = prepared / "lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            observed = self._observed_smoke(lock, "production")
            smoke_path = td_path / "smoke.json"
            smoke_path.write_text(json.dumps(observed), encoding="utf-8")
            output = td_path / "output.md"
            trace = td_path / "trace.json"
            output.write_text("offline\n", encoding="utf-8")
            trace.write_text(json.dumps({"selected_capabilities": []}), encoding="utf-8")
            evidence_rel = f".tmp/{td_path.name}/unknown-import-evidence"
            patched_cfg = dict(cfg)
            patched_cfg["evidence_root"] = evidence_rel
            args = self._import_args(
                case_id="unknown-active-case",
                run_id="offline-unknown",
                lock=lock_path,
                smoke=smoke_path,
                output=output,
                trace=trace,
                status="REVIEW_REQUIRED",
            )
            with patch.object(campaign, "config", return_value=patched_cfg):
                with self.assertRaisesRegex(ValueError, "unknown active campaign case"):
                    campaign.import_run(args)
            self.assertFalse((ROOT / evidence_rel / "unknown-active-case").exists())

    def test_bad_routing_can_be_archived_as_fail_but_not_pass(self) -> None:
        cfg = dict(campaign.config())
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            td_path = Path(td)
            prepared = td_path / "prepared"
            campaign.prepare(prepared, require_pinned_commit=False)
            lock_path = prepared / "lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            case_id = "career-role-eval-en"
            channel = lock["case_channels"][case_id]
            observed = self._observed_smoke(lock, channel)
            smoke_path = td_path / "smoke.json"
            smoke_path.write_text(json.dumps(observed), encoding="utf-8")
            output = td_path / "output.md"
            trace = td_path / "trace.json"
            output.write_text("Synthetic wrong-route output.\n", encoding="utf-8")
            trace.write_text(
                json.dumps({"selected_capabilities": [], "tool_calls": []}),
                encoding="utf-8",
            )
            evidence_rel = f".tmp/{td_path.name}/evidence-routing"
            patched_cfg = dict(cfg)
            patched_cfg["evidence_root"] = evidence_rel

            fail_args = self._import_args(
                case_id=case_id,
                run_id="offline-routing-fail",
                lock=lock_path,
                smoke=smoke_path,
                output=output,
                trace=trace,
                status="FAIL",
            )
            with patch.object(campaign, "config", return_value=patched_cfg):
                receipt_path = campaign.import_run(fail_args)
            data = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual("FAIL", data["evaluation"]["status"])
            self.assertTrue(data["execution"]["selection_findings"])
            self.assertEqual("offline", data["execution"]["evidence_origin"])

            pass_args = self._import_args(
                case_id=case_id,
                run_id="offline-routing-pass",
                lock=lock_path,
                smoke=smoke_path,
                output=output,
                trace=trace,
                status="PASS",
            )
            with patch.object(campaign, "config", return_value=patched_cfg):
                with self.assertRaisesRegex(ValueError, "PASS forbidden"):
                    campaign.import_run(pass_args)

    def test_smoke_rejects_old_release_with_same_name_version_and_catalog(self) -> None:
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            prepared = Path(td) / "prepared"
            campaign.prepare(prepared, require_pinned_commit=False)
            lock_path = prepared / "lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            observed = self._observed_smoke(lock, "production")
            observed["package"]["release_id"] = "1.8.0+stale0000000"
            observed_path = Path(td) / "stale-smoke.json"
            observed_path.write_text(json.dumps(observed), encoding="utf-8")
            errors = campaign.verify_smoke(lock_path, observed_path)
        self.assertTrue(any("package.release_id" in e for e in errors), errors)


    def test_receipt_paths_are_portable_and_trace_is_hashed(self) -> None:
        cfg = campaign.config()
        cases = load_campaign_cases(ROOT, campaign.config()["campaign"])
        case = cases["case-001-premium-vs-generic"]
        version, digest = receipt.current_component_identity(ROOT, case["target"])
        with tempfile.TemporaryDirectory(dir=(ROOT / ".tmp")) as td:
            run = Path(td)
            output = run / "output.md"
            trace = run / "trace.json"
            output.write_text("runtime output\n", encoding="utf-8")
            trace.write_text(json.dumps({"selected_capabilities": [case["target"]]}), encoding="utf-8")
            ns = argparse.Namespace(
                case_id=case["id"],
                status="REVIEW_REQUIRED",
                evidence_scope="current-version",
                source_revision=cfg["behavior_source_revision"],
                component=case["target"],
                component_version=version,
                component_digest=digest,
                provider="provider",
                model_id="model",
                reasoning="medium",
                catalog=[case["target"]],
                tools=["web"],
                prompt=(ROOT / case["input"]).read_text(encoding="utf-8"),
                output=str(output),
                tool_trace=str(trace),
                reviewer="unit-test",
                assisted=False,
                note=None,
            )
            old = os.environ.get("SOURCE_REVISION")
            os.environ["SOURCE_REVISION"] = cfg["behavior_source_revision"]
            try:
                record = receipt.create_receipt(ns)
            finally:
                if old is None:
                    os.environ.pop("SOURCE_REVISION", None)
                else:
                    os.environ["SOURCE_REVISION"] = old
            self.assertFalse(Path(record["execution"]["actual_output_path"]).is_absolute())
            self.assertFalse(Path(record["execution"]["tool_trace_path"]).is_absolute())
            self.assertEqual(64, len(record["execution"]["tool_trace_sha256"]))
            errors = receipt.validate_receipt_data(
                record,
                root=ROOT,
                current_revision=record["source_revision"],
            )
            self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
