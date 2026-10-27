import hashlib
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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


if __name__ == "__main__":
    unittest.main()
