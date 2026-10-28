import csv
import hashlib
import json
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_source_corpus as verifier
from verify_source_corpus import CorpusError, inspect_archive


class SourceCorpusTests(unittest.TestCase):
    def _archive(self, entries):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.zip"
        with ZipFile(path, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
        return path

    def _expected(self, path):
        return {
            "id": "fixture",
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_url": "https://example.invalid/source",
            "license_status": "fixture",
        }

    def test_hashes_members_and_identifies_license_files_without_extracting(self):
        path = self._archive([
            ("pack/SKILL.md", b"# Fixture skill\n"),
            ("pack/LICENSE", b"MIT License\n"),
        ])
        summary, files = inspect_archive(path, self._expected(path))
        self.assertTrue(summary["archive_sha256_verified"])
        self.assertEqual(2, summary["file_count"])
        self.assertEqual(1, summary["skill_md_count"])
        self.assertEqual("pack/LICENSE", summary["license_files"][0]["path"])
        self.assertFalse((path.parent / "pack").exists())
        self.assertEqual(2, len(files))

    def test_rejects_archive_hash_mismatch(self):
        path = self._archive([("safe.md", b"content")])
        expected = self._expected(path)
        expected["sha256"] = "0" * 64
        with self.assertRaisesRegex(CorpusError, "SHA-256 mismatch"):
            inspect_archive(path, expected)

    def test_rejects_posix_and_windows_path_traversal(self):
        for member in ("../outside.md", "C:\\outside.md", "folder\\..\\outside.md"):
            with self.subTest(member=member):
                path = self._archive([(member, b"content")])
                with self.assertRaisesRegex(CorpusError, "unsafe member path"):
                    inspect_archive(path, self._expected(path))

    def test_rejects_duplicate_member_paths(self):
        path = tempfile.TemporaryDirectory()
        self.addCleanup(path.cleanup)
        archive_path = Path(path.name) / "duplicate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("same.md", b"first")
                archive.writestr("same.md", b"second")
        with self.assertRaisesRegex(CorpusError, "duplicate member path"):
            inspect_archive(archive_path, self._expected(archive_path))

    def test_build_writes_a_complete_sorted_index_and_manifest(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        source_dir = Path(directory.name)
        first = source_dir / "first.zip"
        second = source_dir / "second.zip"
        for path, entries in (
            (first, [("pack/SKILL.md", b"skill"), ("pack/README.md", b"readme")]),
            (second, [("other/LICENSE", b"license")]),
        ):
            with ZipFile(path, "w") as archive:
                for name, content in entries:
                    archive.writestr(name, content)

        original_archives = verifier.ARCHIVES
        self.addCleanup(setattr, verifier, "ARCHIVES", original_archives)
        verifier.ARCHIVES = (
            {**self._expected(first), "filename": first.name},
            {**self._expected(second), "filename": second.name},
        )
        manifest_path = source_dir / "manifest.json"
        index_path = source_dir / "index.csv"
        manifest = verifier.build(source_dir, manifest_path, index_path)

        with index_path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(3, len(rows))
        self.assertEqual(sorted(rows, key=lambda row: (row["archive_id"], row["path"])), rows)
        self.assertEqual([2, 1], [item["file_count"] for item in manifest["archives"]])
        self.assertEqual(manifest, json.loads(manifest_path.read_text(encoding="utf-8")))
        self.assertEqual(1, manifest["archives"][0]["skill_md_count"])
        self.assertEqual("other/LICENSE", manifest["archives"][1]["license_files"][0]["path"])

    def test_committed_index_matches_manifest_inventory(self):
        root = Path(__file__).resolve().parents[3]
        manifest = json.loads((root / "docs/strategy-os/strategy-source-manifest.json").read_text(encoding="utf-8"))
        index_path = root / "docs/strategy-os/strategy-source-file-index.csv"
        with index_path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(["archive_id", "archive_sha256", "path", "size_bytes", "sha256", "extension"], reader.fieldnames)
            rows = list(reader)
        self.assertEqual(350, len(rows))
        self.assertEqual(sum(item["file_count"] for item in manifest["archives"]), len(rows))
        for item in manifest["archives"]:
            archive_rows = [row for row in rows if row["archive_id"] == item["id"]]
            self.assertEqual(item["file_count"], len(archive_rows), item["id"])
            self.assertTrue(all(row["archive_sha256"] == item["sha256"] for row in archive_rows), item["id"])
            self.assertTrue(all(len(row["sha256"]) == 64 for row in archive_rows), item["id"])

    def test_benchmark_register_covers_all_oria_skills_without_inventing_scores(self):
        root = Path(__file__).resolve().parents[3]
        with (root / "docs/strategy-os/strategy-source-file-index.csv").open(newline="", encoding="utf-8") as stream:
            source_rows = list(csv.DictReader(stream))
        expected = {(row["archive_id"], row["path"]): row for row in source_rows
                    if row["archive_id"].startswith("oria-") and row["path"].endswith("SKILL.md")}
        with (root / "docs/strategy-os/strategy-skill-benchmark-register.csv").open(newline="", encoding="utf-8") as stream:
            benchmark_rows = list(csv.DictReader(stream))
        self.assertEqual(92, len(expected))
        self.assertEqual(set(expected), {(row["archive_id"], row["source_skill_path"]) for row in benchmark_rows})
        for row in benchmark_rows:
            source_row = expected[(row["archive_id"], row["source_skill_path"])]
            self.assertEqual(source_row["sha256"], row["source_skill_sha256"])
            self.assertEqual(source_row["archive_sha256"], row["archive_sha256"])
            self.assertEqual("N/O", row["quality_score_1_to_5"])
            self.assertEqual("NOT_RUN", row["benchmark_status"])
            self.assertEqual("N/O", row["cost_usd"])
            self.assertEqual("NOT_RECORDED", row["cost_status"])


if __name__ == "__main__":
    unittest.main()
