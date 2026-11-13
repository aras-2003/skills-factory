from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "security"))
import external_skill_intake as intake
import propose_skill_adaptation as adaptation

SKILL = b"""---
name: demo-skill
description: Adapt a reviewed external skill into a portable package when its capabilities complement this repository.
---
## Purpose
A synthetic fixture.

## Procedure
Use the reviewed fixture only.

## Output contract
Produce a proposal.
"""
COMMIT = "a" * 40
REPO = "example-org/example-skills"


def make_inputs(root: Path, *, decision: str = "EXTEND", security_status: str = "REVIEW_REQUIRED", skill_bytes: bytes = SKILL):
    receipt, _manifest = intake.build_receipt(
        {"type": "github_repository", "repository": REPO, "commit": COMMIT,
         "source_digest": "b" * 64, "subdir": None,
         "author": {"state": "UNKNOWN", "name": None, "login": None, "commit_sha": None}},
        {"SKILL.md": skill_bytes, "references/guide.md": b"Synthetic reference."},
        scan_fn=lambda _root, today=None: ([], []),
    )
    receipt["security_review"]["status"] = security_status
    receipt_path = root / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    quarantine = root / "quarantine"
    quarantine.mkdir()
    (quarantine / "SKILL.md").write_bytes(skill_bytes)
    (quarantine / "references").mkdir()
    (quarantine / "references" / "guide.md").write_bytes(b"Synthetic reference.")

    matcher_report = {
        "schema_version": 1,
        "candidate_identity": "external:example/demo",
        "decision": decision,
        "human_review_required": decision != "REUSE_EXISTING",
        "escalation_required": False,
        "inventory_complete": True,
        "reason_codes": ["SYNTHETIC_FIXTURE"],
        "matched_capabilities": ["skills/meta/skill-authoring"] if decision == "EXTEND" else [],
        "conflicts": [],
        "candidate_facts": {
            "dependencies": {"status": "COMPARED", "values": [], "evidence": {}},
        },
        "comparisons": [{"identity": "skills/meta/skill-authoring", "evidence": {}, "conflict": False}],
    }
    matcher_path = root / "matcher.json"
    matcher_path.write_text(json.dumps(matcher_report, sort_keys=True), encoding="utf-8")
    receipt_sha = intake.receipt_digest(receipt)
    matcher_sha = hashlib.sha256((json.dumps(matcher_report, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
    review = {
        "schema_version": 1,
        "receipt_sha256": receipt_sha,
        "inventory_sha256": receipt["inventory_sha256"],
        "matcher_report_sha256": matcher_sha,
        "source": receipt["source"],
        "reviewer": "fixture-reviewer",
        "reviewed_at": "2026-11-13T17:00:00Z",
        "rationale": "Synthetic review of the exact receipt and matcher evidence.",
        "approved_decision": decision,
        "runtime_dependency_review": {
            "status": "NO_RUNTIME_DEPENDENCIES",
            "dependencies": [],
            "rationale": "The exact matcher report lists no runtime dependencies.",
        },
    }
    review_path = root / "review.json"
    review_path.write_text(json.dumps(review, sort_keys=True), encoding="utf-8")
    output = root / "proposal"
    return receipt_path, quarantine, matcher_path, review_path, output


class ProposeSkillAdaptationTests(unittest.TestCase):
    def test_creates_portable_lineage_bound_proposal_without_promoting_unknown_license(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = make_inputs(root)
            result = adaptation.create_proposal(*args)
            self.assertEqual("ADAPTATION_SEED_CREATED", result["status"])
            self.assertFalse(result["release_eligible"])
            package = args[-1] / "demo-skill"
            self.assertTrue((package / "SKILL.md").exists())
            self.assertEqual(b"Synthetic reference.", (package / "references/guide.md").read_bytes())
            manifest = json.loads((args[-1] / "proposal.json").read_text())
            self.assertEqual("UNKNOWN", manifest["license_decision"])
            self.assertFalse(manifest["automatic_merge_or_publish"])
            self.assertEqual("NOT_STARTED", manifest["local_modifications"]["status"])
            self.assertEqual(64, len(manifest["package_sha256"]))

    def test_tampered_quarantine_bytes_are_refused_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            (args[1] / "SKILL.md").write_bytes(SKILL + b"tamper")
            with self.assertRaisesRegex(adaptation.ProposalError, "exact intake receipt"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_missing_or_stale_human_review_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            review = json.loads(args[3].read_text())
            review["matcher_report_sha256"] = "0" * 64
            args[3].write_text(json.dumps(review))
            with self.assertRaisesRegex(adaptation.ProposalError, "exact matcher report"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_duplicate_or_conflict_decision_cannot_emit_package(self):
        for decision in ("REUSE_EXISTING", "REJECT"):
            with self.subTest(decision=decision), tempfile.TemporaryDirectory() as temp:
                args = make_inputs(Path(temp), decision=decision)
                with self.assertRaisesRegex(adaptation.ProposalError, "not an adaptation decision"):
                    adaptation.create_proposal(*args)
                self.assertFalse(args[-1].exists())

    def test_rejected_license_intake_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            receipt = json.loads(args[0].read_text())
            receipt["license_decision"] = "REJECTED"
            args[0].write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            # Rebind the human review to the exact changed receipt; license rejection remains a hard stop.
            review = json.loads(args[3].read_text())
            review["receipt_sha256"] = intake.receipt_digest(receipt)
            args[3].write_text(json.dumps(review, sort_keys=True), encoding="utf-8")
            with self.assertRaisesRegex(adaptation.ProposalError, "rejected license intake"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_unsupported_dependency_blocks_proposal_and_dependency_list_is_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            report = json.loads(args[2].read_text())
            report["candidate_facts"]["dependencies"]["values"] = ["python standard library"]
            report["candidate_facts"]["dependencies"]["evidence"] = {"python standard library": []}
            args[2].write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
            receipt = json.loads(args[0].read_text())
            receipt_sha = intake.receipt_digest(receipt)
            matcher_sha = hashlib.sha256((json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
            review = json.loads(args[3].read_text())
            review.update({"receipt_sha256": receipt_sha, "matcher_report_sha256": matcher_sha})
            review["runtime_dependency_review"] = {
                "status": "SUPPORTED",
                "dependencies": [{"name": "python standard library", "status": "UNSUPPORTED", "evidence": "Not available in the target runtime."}],
                "rationale": "Synthetic unsupported dependency test.",
            }
            args[3].write_text(json.dumps(review, sort_keys=True), encoding="utf-8")
            with self.assertRaisesRegex(adaptation.ProposalError, "block adaptation"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_supported_dependency_review_is_preserved_in_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            report = json.loads(args[2].read_text())
            report["candidate_facts"]["dependencies"]["values"] = ["python standard library"]
            report["candidate_facts"]["dependencies"]["evidence"] = {"python standard library": []}
            args[2].write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
            review = json.loads(args[3].read_text())
            review["matcher_report_sha256"] = hashlib.sha256((json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()
            review["runtime_dependency_review"] = {
                "status": "SUPPORTED",
                "dependencies": [{"name": "python standard library", "status": "SUPPORTED", "evidence": "Present in the target runtime baseline."}],
                "rationale": "The exact dependency is available in the supported runtime.",
            }
            args[3].write_text(json.dumps(review, sort_keys=True), encoding="utf-8")
            result = adaptation.create_proposal(*args)
            self.assertEqual("ADAPTATION_SEED_CREATED", result["status"])
            manifest = json.loads((args[-1] / "proposal.json").read_text())
            self.assertEqual("SUPPORTED", manifest["runtime_dependency_review"]["status"])
            self.assertEqual("python standard library", manifest["runtime_dependency_review"]["dependencies"][0]["name"])

    def test_review_dependency_assessment_must_match_exact_report(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            review = json.loads(args[3].read_text())
            review["runtime_dependency_review"]["rationale"] = ""
            args[3].write_text(json.dumps(review, sort_keys=True), encoding="utf-8")
            with self.assertRaisesRegex(adaptation.ProposalError, "requires a rationale"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_blocked_security_intake_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp), security_status="BLOCKED")
            with self.assertRaisesRegex(adaptation.ProposalError, "blocked security intake"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())

    def test_extra_quarantine_files_and_symlinks_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            (args[1] / "unexpected.txt").write_text("extra")
            with self.assertRaisesRegex(adaptation.ProposalError, "unexpected"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            (args[1] / "link").symlink_to(args[1] / "SKILL.md")
            with self.assertRaisesRegex(adaptation.ProposalError, "symbolic link"):
                adaptation.create_proposal(*args)

    def test_proposal_cannot_write_into_canonical_skill_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            args = list(make_inputs(Path(temp)))
            canonical_skills = ROOT / "skills"
            canonical_skills.mkdir(exist_ok=True)
            args[-1] = canonical_skills / "should-never-exist"
            with self.assertRaisesRegex(adaptation.ProposalError, "canonical skills"):
                adaptation.create_proposal(*args)
            self.assertFalse(args[-1].exists())


    def test_finalizes_changed_package_with_exact_human_change_record(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            adaptation.create_proposal(*args)
            proposal_manifest = json.loads((args[-1] / "proposal.json").read_text())
            package_skill = args[-1] / "demo-skill" / "SKILL.md"
            package_skill.write_bytes(SKILL + b"\n## Added local safeguard\nRequire a reviewer.\n")
            change_record = {
                "schema_version": 1,
                "intake_receipt_sha256": proposal_manifest["intake_receipt_sha256"],
                "source_package_sha256": proposal_manifest["source_package_sha256"],
                "matcher_report_sha256": proposal_manifest["matcher_report_sha256"],
                "reviewer": "fixture-reviewer",
                "reviewed_at": "2026-11-13T17:01:00Z",
                "rationale": "Adds an explicit local trigger boundary after duplicate review.",
                "changes": [{"path": "SKILL.md", "rationale": "Documents the local trigger boundary."}],
            }
            change_path = Path(temp) / "changes.json"
            change_path.write_text(json.dumps(change_record), encoding="utf-8")
            result = adaptation.finalize_proposal(args[-1], change_path)
            self.assertEqual("FINALIZED_SCOPED_PR_PROPOSAL", result["status"])
            updated = json.loads((args[-1] / "proposal.json").read_text())
            self.assertEqual("HUMAN_REVIEWED", updated["local_modifications"]["status"])
            self.assertEqual("MODIFIED", updated["local_modifications"]["items"][0]["change"])
            expected_change_sha = hashlib.sha256((json.dumps(change_record, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()).hexdigest()
            self.assertEqual(expected_change_sha, updated["change_record_sha256"])
            self.assertFalse(updated["release_eligible"])

    def test_nonportable_compatibility_is_a_blocker_at_finalization(self):
        invalid_skill = (
            b"""---
name: demo-skill
description: Adapt a reviewed external skill into a portable package when its capabilities complement this repository.
compatibility: """
            + b"x" * 501
            + b"\n---\n## Purpose\nA synthetic fixture.\n\n## Procedure\nUse the reviewed fixture only.\n\n## Output contract\nProduce a proposal.\n"
        )
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp), skill_bytes=invalid_skill)
            adaptation.create_proposal(*args)
            change_path = Path(temp) / "changes.json"
            change_path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(adaptation.ProposalError, "fails repository portability validation"):
                adaptation.finalize_proposal(args[-1], change_path)

    def test_finalization_refuses_unrecorded_local_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            adaptation.create_proposal(*args)
            proposal_manifest = json.loads((args[-1] / "proposal.json").read_text())
            (args[-1] / "demo-skill" / "SKILL.md").write_bytes(SKILL + b"\nlocal change")
            change_path = Path(temp) / "changes.json"
            change_path.write_text(json.dumps({
                "schema_version": 1,
                "intake_receipt_sha256": proposal_manifest["intake_receipt_sha256"],
                "source_package_sha256": proposal_manifest["source_package_sha256"],
                "matcher_report_sha256": proposal_manifest["matcher_report_sha256"],
                "reviewer": "fixture-reviewer",
                "reviewed_at": "2026-11-13T17:01:00Z",
                "rationale": "Incomplete synthetic review.",
                "changes": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(adaptation.ProposalError, "describe every"):
                adaptation.finalize_proposal(args[-1], change_path)

    def test_output_must_be_new_and_parent_real(self):
        with tempfile.TemporaryDirectory() as temp:
            args = make_inputs(Path(temp))
            args[-1].mkdir()
            with self.assertRaisesRegex(adaptation.ProposalError, "must not already exist"):
                adaptation.create_proposal(*args)


if __name__ == "__main__":
    unittest.main()
