from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import external_skill_intake as intake
import external_skill_update as update


REPO = "example-org/example-skills"
BASE_COMMIT = "a" * 40
CANDIDATE_COMMIT = "b" * 40
BASE_FILES = {
    "SKILL.md": b"---\nname: demo-skill\ndescription: Synthetic fixture\nallowed-tools: [Read]\n---\n# Demo\n",
    "LICENSE": b"MIT License\n",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source(commit: str, files: dict[str, bytes]) -> dict:
    archive_digest = sha((commit + "archive").encode())
    return {
        "type": "github_repository", "repository": REPO, "commit": commit, "subdir": "skills/demo",
        "source_url": f"https://github.com/{REPO}/tree/{commit}/skills/demo",
        "source_digest": archive_digest,
        "author": {"state": "PROVIDER_COMMIT_METADATA", "name": "Fixture", "login": "fixture", "commit_sha": commit},
    }


def receipt_and_review() -> tuple[dict, dict, dict]:
    baseline_source = source(BASE_COMMIT, BASE_FILES)
    receipt, _manifest = intake.build_receipt(baseline_source, BASE_FILES, scan_fn=lambda _root, today=None: ([], []))
    receipt["license_decision"] = "APPROVED"
    review = {
        "schema_version": 1,
        "receipt_sha256": intake.receipt_digest(receipt),
        "inventory_sha256": receipt["inventory_sha256"],
        "source": {"repository": REPO, "commit": BASE_COMMIT},
        "reviewer": "fixture-reviewer", "reviewed_at": "2026-11-16T00:00:00Z",
        "rationale": "Synthetic accepted baseline for deterministic update review tests.",
        "license_decision": "APPROVED", "security_decision": "APPROVED",
        "license_evidence_reference": "fixture:license", "security_evidence_reference": "fixture:security",
    }
    return receipt, review, baseline_source


def registry_for(receipt: dict, *, include_unknown: bool = False) -> dict:
    inventory = receipt["inventory_sha256"]
    anchor = {
        "kind": "skill", "name": "demo-skill", "source": "skills/demo/SKILL.md", "source_sha256": sha(b"local baseline"),
        "classification": "IMPORTED",
        "upstream": {"provider": "github", "url": f"https://github.com/{REPO}", "path": "skills/demo", "content_sha256": inventory, "version": None, "commit": BASE_COMMIT, "attribution": ["example-org"]},
        "components": [], "dependencies": [], "basis_evidence": ["fixture:review"],
        "local_modifications": {"status": "NONE", "items": []},
        "license": {"status": "VERIFIED", "spdx_id": "MIT", "attribution": ["example-org"]},
        "update_policy": "PINNED_MANUAL", "verification": {"state": "VERIFIED", "reviewed_at": "2026-11-16", "owner": "fixture"},
    }
    direct = {
        "kind": "skill", "name": "direct-user", "source": "skills/tool/SKILL.md", "source_sha256": sha(b"direct"),
        "classification": "OWN", "upstream": None, "components": [], "dependencies": [anchor["source"]], "basis_evidence": ["fixture:owned"],
        "local_modifications": {"status": "NONE", "items": []},
        "license": {"status": "NOT_APPLICABLE", "spdx_id": None, "attribution": []},
        "update_policy": "MANUAL_REVIEW", "verification": {"state": "VERIFIED", "reviewed_at": "2026-11-16", "owner": "fixture"},
    }
    transitive = {
        "kind": "workflow", "name": "workflow-user", "source": "workflows/demo/WORKFLOW.md", "source_sha256": sha(b"workflow"),
        "classification": "OWN", "upstream": None, "components": [], "dependencies": [direct["source"]], "basis_evidence": ["fixture:workflow"],
        "local_modifications": {"status": "NONE", "items": []},
        "license": {"status": "NOT_APPLICABLE", "spdx_id": None, "attribution": []},
        "update_policy": "MANUAL_REVIEW", "verification": {"state": "VERIFIED", "reviewed_at": "2026-11-16", "owner": "fixture"},
    }
    records = [anchor, direct, transitive]
    if include_unknown:
        unknown = {
            "kind": "skill", "name": "unknown-skill", "source": "skills/unknown/SKILL.md", "source_sha256": sha(b"unknown"),
            "classification": "UNKNOWN", "upstream": None, "components": [], "dependencies": [], "basis_evidence": [],
            "local_modifications": {"status": "UNKNOWN", "items": []},
            "license": {"status": "UNKNOWN", "spdx_id": None, "attribution": []},
            "update_policy": "MANUAL_REVIEW", "verification": {"state": "NOT_CLASSIFIED", "reviewed_at": None, "owner": "fixture"},
        }
        records.append(unknown)
    return {"schema_version": 1, "records": records}


def build_report(*, candidate_files: dict[str, bytes] | None = None, registry: dict | None = None, candidate_commit: str = CANDIDATE_COMMIT, candidate_modes: dict | None = None) -> dict:
    receipt, review, baseline_source = receipt_and_review()
    baseline_modes = {path: 0o644 for path in BASE_FILES}
    if registry is None:
        registry = registry_for(receipt)
    candidate_source = source(candidate_commit, candidate_files) if candidate_files is not None else None
    return update.build_update_report(
        baseline_receipt=receipt, baseline_review=review,
        baseline_source=baseline_source, baseline_files=BASE_FILES, baseline_modes=baseline_modes,
        candidate_source=candidate_source, candidate_files=candidate_files,
        candidate_modes=candidate_modes if candidate_modes is not None else ({path: 0o644 for path in candidate_files} if candidate_files else None),
        registry=registry,
    )


class ExternalSkillUpdateTests(unittest.TestCase):
    def test_exact_accepted_pin_is_unchanged_only_when_receipt_and_inventory_match(self) -> None:
        receipt, review, baseline_source = receipt_and_review()
        report = update.build_update_report(
            baseline_receipt=receipt, baseline_review=review, baseline_source=baseline_source,
            baseline_files=BASE_FILES, baseline_modes={path: 0o644 for path in BASE_FILES},
            candidate_source=baseline_source, candidate_files=BASE_FILES,
            candidate_modes={path: 0o644 for path in BASE_FILES}, registry=registry_for(receipt),
        )
        self.assertEqual("UNCHANGED", report["comparison_status"])
        self.assertEqual("UNCHANGED", report["status"])
        self.assertEqual("APPROVED", report["license_changes"]["decision"])
        self.assertEqual([], report["blockers"])

    def test_changed_candidate_reports_permissions_license_resources_modes_and_deprecation(self) -> None:
        candidate_files = {
            "SKILL.md": b"---\nname: demo-skill\ndescription: Synthetic fixture\nallowed-tools: [Read, Write]\n---\nThis API is deprecated.\n",
            "LICENSE": b"Apache License\n",
            "scripts/helper.sh": b"#!/bin/sh\necho fixture\n",
        }
        report = build_report(candidate_files=candidate_files, candidate_modes={"SKILL.md": 0o644, "LICENSE": 0o600, "scripts/helper.sh": 0o755})
        self.assertEqual("NOT_READY", report["status"])
        self.assertEqual("REVIEW_REQUIRED", report["comparison_status"])
        self.assertEqual(["SKILL.md"], report["permission_changes"]["changed_paths"])
        self.assertEqual("REVIEW_REQUIRED", report["license_changes"]["decision"])
        self.assertEqual(["LICENSE"], report["license_changes"]["changed"])
        self.assertEqual(["scripts/helper.sh"], [row["path"] for row in report["resource_changes"]["added"]])
        self.assertEqual([{"path": "scripts/helper.sh", "mode": 0o755, "executable": True}], report["executable_mode"]["added"])
        self.assertEqual([{"path": "LICENSE", "before_mode": 0o644, "after_mode": 0o600, "before_executable": False, "after_executable": False}], report["executable_mode"]["changed"])
        self.assertIn({"path": "SKILL.md", "before": {}, "after": {"DEPRECATED": 1}}, report["deprecation_signals"])
        self.assertEqual("NOT_AUTHORIZED", report["authorization_state"])
        self.assertTrue(report["review_required"])
        self.assertEqual([], report["blockers"])
        schema = json.loads(update.REPORT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)

    def test_current_incomplete_registry_blocks_consumer_completeness_without_claiming_none(self) -> None:
        receipt, _review, _source = receipt_and_review()
        report = build_report(candidate_files=BASE_FILES, candidate_commit=BASE_COMMIT, registry=registry_for(receipt, include_unknown=True))
        self.assertEqual("UNKNOWN", report["consumer_impact"]["status"])
        self.assertFalse(report["consumer_impact"]["complete"])
        self.assertEqual(["skills/tool/SKILL.md"], report["consumer_impact"]["direct_consumers"])
        self.assertEqual(["workflows/demo/WORKFLOW.md"], report["consumer_impact"]["transitive_consumers"])
        self.assertIn("CONSUMER_LINEAGE_INCOMPLETE", report["blockers"])
        self.assertEqual("UNCHANGED", report["comparison_status"])
        self.assertEqual("BLOCKED", report["status"])

    def test_repository_registry_does_not_claim_complete_or_empty_impact_without_verified_lineage(self) -> None:
        registry_path = Path(__file__).resolve().parents[3] / "provenance/registry.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        receipt, review, baseline_source = receipt_and_review()
        baseline_modes = {path: 0o644 for path in BASE_FILES}
        report = update.build_update_report(
            baseline_receipt=receipt, baseline_review=review,
            baseline_source=baseline_source, baseline_files=BASE_FILES,
            baseline_modes=baseline_modes, candidate_source=baseline_source,
            candidate_files=BASE_FILES, candidate_modes=baseline_modes,
            registry=registry,
        )

        self.assertEqual("UNKNOWN", report["consumer_impact"]["status"])
        self.assertFalse(report["consumer_impact"]["complete"])
        self.assertIn("ACCEPTED_LINEAGE_NOT_FOUND", report["blockers"])
        self.assertIn("CONSUMER_LINEAGE_INCOMPLETE", report["blockers"])
        self.assertEqual("BLOCKED", report["status"])

    def test_dependency_cycles_terminate_and_mark_impact_incomplete(self) -> None:
        receipt, _review, _source = receipt_and_review()
        registry = registry_for(receipt)
        registry["records"][0]["dependencies"] = ["workflows/demo/WORKFLOW.md"]
        report = build_report(candidate_files=BASE_FILES, candidate_commit=BASE_COMMIT, registry=registry)
        self.assertFalse(report["consumer_impact"]["complete"])
        self.assertTrue(any("cycle detected" in error for error in report["consumer_impact"]["errors"]))
        self.assertIn("CONSUMER_LINEAGE_INCOMPLETE", report["blockers"])

    def test_missing_consumer_edge_target_marks_impact_incomplete(self) -> None:
        receipt, _review, _source = receipt_and_review()
        registry = registry_for(receipt)
        registry["records"][1]["dependencies"] = ["skills/missing/SKILL.md"]
        report = build_report(candidate_files=BASE_FILES, candidate_commit=BASE_COMMIT, registry=registry)
        self.assertFalse(report["consumer_impact"]["complete"])
        self.assertTrue(any("missing" in error for error in report["consumer_impact"]["errors"]))
        self.assertIn("CONSUMER_LINEAGE_INCOMPLETE", report["blockers"])

    def test_unavailable_candidate_is_blocked_and_never_reported_unchanged(self) -> None:
        report = build_report(candidate_files=None)
        self.assertEqual("BLOCKED", report["comparison_status"])
        self.assertEqual("BLOCKED", report["status"])
        self.assertIn("CANDIDATE_SOURCE_UNAVAILABLE", report["blockers"])
        schema = json.loads(update.REPORT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)

    def test_missing_baseline_mode_evidence_blocks_a_clean_unchanged_result(self) -> None:
        receipt, review, baseline_source = receipt_and_review()
        report = update.build_update_report(
            baseline_receipt=receipt, baseline_review=review, baseline_source=baseline_source,
            baseline_files=BASE_FILES, baseline_modes={path: None for path in BASE_FILES},
            candidate_source=baseline_source, candidate_files=BASE_FILES,
            candidate_modes={path: 0o644 for path in BASE_FILES}, registry=registry_for(receipt),
        )
        self.assertEqual("UNCHANGED", report["comparison_status"])
        self.assertEqual("BLOCKED", report["status"])
        self.assertIn("EXECUTABLE_MODE_UNKNOWN", report["blockers"])

    def test_unavailable_baseline_has_schema_valid_blocked_report(self) -> None:
        receipt, review, _baseline_source = receipt_and_review()
        report = update._baseline_unavailable_report(
            receipt, review, registry_for(receipt),
            {"repository": REPO, "commit": CANDIDATE_COMMIT, "subdir": "skills/demo"},
            "IntakeError", "BASELINE_DIGEST_MISMATCH",
        )
        schema = json.loads(update.REPORT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)
        self.assertEqual("BLOCKED", report["status"])
        self.assertIn("BASELINE_DIGEST_MISMATCH", report["blockers"])

    def test_cli_reuses_baseline_subdirectory_and_emits_review_report(self) -> None:
        receipt, review, baseline_source = receipt_and_review()
        registry = registry_for(receipt)
        candidate_source = source(CANDIDATE_COMMIT, BASE_FILES)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt_path, review_path, registry_path = root / "receipt.json", root / "review.json", root / "registry.yaml"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")
            registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

            class StdoutBuffer:
                def __init__(self) -> None:
                    self.buffer = io.BytesIO()

            output = StdoutBuffer()
            with patch.object(update.intake, "fetch_github_source_with_modes", side_effect=[
                (baseline_source, BASE_FILES, {path: 0o644 for path in BASE_FILES}),
                (candidate_source, BASE_FILES, {path: 0o644 for path in BASE_FILES}),
            ]) as fetch, patch.object(sys, "stdout", output):
                status = update.main([
                    "--baseline-receipt", str(receipt_path), "--baseline-review", str(review_path),
                    "--candidate-repository", REPO, "--candidate-commit", CANDIDATE_COMMIT,
                    "--registry", str(registry_path),
                ])
            self.assertEqual(0, status)
            self.assertEqual("skills/demo", fetch.call_args_list[1].args[2])
            report = json.loads(output.buffer.getvalue())
            self.assertEqual("REVIEW_REQUIRED", report["comparison_status"])
            self.assertEqual(CANDIDATE_COMMIT, report["candidate"]["commit"])

    def test_cli_fetch_failure_emits_blocked_report_for_requested_candidate(self) -> None:
        receipt, review, baseline_source = receipt_and_review()
        registry = registry_for(receipt)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt_path, review_path, registry_path = root / "receipt.json", root / "review.json", root / "registry.yaml"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            review_path.write_text(json.dumps(review), encoding="utf-8")
            registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")

            class StdoutBuffer:
                def __init__(self) -> None:
                    self.buffer = io.BytesIO()

            output = StdoutBuffer()
            with patch.object(update.intake, "fetch_github_source_with_modes", side_effect=[
                (baseline_source, BASE_FILES, {path: 0o644 for path in BASE_FILES}),
                intake.IntakeError("synthetic unavailable source"),
            ]), patch.object(sys, "stdout", output):
                status = update.main([
                    "--baseline-receipt", str(receipt_path), "--baseline-review", str(review_path),
                    "--candidate-repository", REPO, "--candidate-commit", CANDIDATE_COMMIT,
                    "--registry", str(registry_path),
                ])
            self.assertEqual(2, status)
            report = json.loads(output.buffer.getvalue())
            self.assertEqual("BLOCKED", report["comparison_status"])
            self.assertEqual(CANDIDATE_COMMIT, report["candidate"]["commit"])
            self.assertIn("CANDIDATE_SOURCE_UNAVAILABLE", report["blockers"])

    def test_baseline_inventory_or_approval_mismatch_fails_closed(self) -> None:
        receipt, review, baseline_source = receipt_and_review()
        with self.assertRaisesRegex(update.UpdateError, "inventory does not match"):
            update.build_update_report(
                baseline_receipt=receipt, baseline_review=review, baseline_source=baseline_source,
                baseline_files={"SKILL.md": b"changed"}, baseline_modes={},
                candidate_source=baseline_source, candidate_files=BASE_FILES, candidate_modes={}, registry=registry_for(receipt),
            )
        bad_review = dict(review, receipt_sha256="0" * 64)
        with self.assertRaisesRegex(update.UpdateError, "lacks a valid approval"):
            update.build_update_report(
                baseline_receipt=receipt, baseline_review=bad_review, baseline_source=baseline_source,
                baseline_files=BASE_FILES, baseline_modes={path: 0o644 for path in BASE_FILES}, candidate_source=baseline_source,
                candidate_files=BASE_FILES, candidate_modes={path: 0o644 for path in BASE_FILES}, registry=registry_for(receipt),
            )

    def test_report_schema_is_valid_and_deterministic(self) -> None:
        schema = json.loads(update.REPORT_SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        receipt, review, baseline_source = receipt_and_review()
        registry = registry_for(receipt)
        before = json.dumps({"receipt": receipt, "review": review, "registry": registry}, sort_keys=True)
        report_a = build_report(candidate_files=BASE_FILES, candidate_commit=BASE_COMMIT)
        report_b = build_report(candidate_files=BASE_FILES, candidate_commit=BASE_COMMIT)
        self.assertEqual(report_a, report_b)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(report_a)
        update.build_update_report(
            baseline_receipt=receipt, baseline_review=review, baseline_source=baseline_source,
            baseline_files=BASE_FILES, baseline_modes={path: 0o644 for path in BASE_FILES},
            candidate_source=baseline_source, candidate_files=BASE_FILES,
            candidate_modes={path: 0o644 for path in BASE_FILES}, registry=registry,
        )
        self.assertEqual(before, json.dumps({"receipt": receipt, "review": review, "registry": registry}, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
