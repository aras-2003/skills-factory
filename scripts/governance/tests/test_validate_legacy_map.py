from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/governance"))
from validate_legacy_map import blob_sha, validate  # noqa: E402


class HistoricalMapValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source_path = self.root / "docs/roadmap/2026-10-05/BACKLOG.json"
        self.map_path = self.root / "docs/governance/backlog-legacy-issue-map.json"
        self.source_path.parent.mkdir(parents=True)
        self.map_path.parent.mkdir(parents=True)
        self.write_fixture()

    def write_fixture(self, *, ids=("A", "B"), rows=None, valid_sha=True) -> None:
        source = json.dumps({"items": [{"id": name} for name in ids]}) + "\n"
        self.source_path.write_text(source, encoding="utf-8")
        mapping = {
            "source": self.source_path.relative_to(self.root).as_posix(),
            "source_blob_sha": blob_sha(source.encode("utf-8")) if valid_sha else "0" * 40,
            "items": rows if rows is not None else [
                {"legacy_id": "A", "issue": 1, "review_required": False},
                {"legacy_id": "B", "issue": 2, "review_required": True},
            ],
        }
        self.map_path.write_text(json.dumps(mapping), encoding="utf-8")

    def test_matching_unique_ids_are_only_static_valid(self) -> None:
        report, errors = validate(self.root)
        self.assertFalse(errors)
        self.assertEqual("STATIC_ID_MAP_OK", report["status"])
        self.assertEqual(2, report["mapped_count"])
        self.assertEqual("NOT_VERIFIED", report["project_v2_membership_and_fields"])

    def test_detects_missing_historical_id(self) -> None:
        self.write_fixture(ids=("A", "B", "C"))
        _, errors = validate(self.root)
        self.assertTrue(any("unmapped historical IDs: C" in item for item in errors))

    def test_rejects_duplicate_issues_and_historical_ids(self) -> None:
        self.write_fixture(rows=[
            {"legacy_id": "A", "issue": 1, "review_required": False},
            {"legacy_id": "A", "issue": 1, "review_required": True},
        ])
        _, errors = validate(self.root)
        self.assertTrue(any("duplicate IDs" in item for item in errors))
        self.assertTrue(any("same GitHub Issue" in item for item in errors))

    def test_malformed_source_id_fails_closed_without_type_error(self) -> None:
        self.write_fixture(ids=("A", {"nested": ["not an ID"]}))
        report, errors = validate(self.root)
        self.assertEqual("BLOCKED_SCHEMA", report["status"])
        self.assertTrue(any("nonempty strings" in error for error in errors))

    def test_malformed_mapping_id_fails_closed_without_sort_error(self) -> None:
        self.write_fixture(rows=[
            {"legacy_id": "A", "issue": 1, "review_required": False},
            {"legacy_id": 2, "issue": 2, "review_required": True},
        ])
        report, errors = validate(self.root)
        self.assertEqual("BLOCKED_SCHEMA", report["status"])
        self.assertTrue(any("nonempty strings" in error for error in errors))

    def test_must_not_silently_repin_stale_source(self) -> None:
        self.write_fixture(valid_sha=False)
        _, errors = validate(self.root)
        self.assertTrue(any("SHA mismatch" in item for item in errors))

    def test_rejects_unsafe_historical_source_path(self) -> None:
        doc = json.loads(self.map_path.read_text(encoding="utf-8"))
        doc["source"] = "../outside.json"
        self.map_path.write_text(json.dumps(doc), encoding="utf-8")
        report, errors = validate(self.root)
        self.assertEqual("BLOCKED_SOURCE", report["status"])
        self.assertTrue(errors)

    def test_real_repository_snapshot_is_static_only(self) -> None:
        report, errors = validate(ROOT)
        self.assertFalse(errors, errors)
        self.assertEqual(90, report["historical_count"])
        self.assertEqual(90, report["mapped_count"])
        self.assertEqual("NOT_RUN", report["runtime_evidence"])


if __name__ == "__main__":
    unittest.main()
