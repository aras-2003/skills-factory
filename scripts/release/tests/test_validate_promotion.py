from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.release.validate_promotion import validate_promotion


class ValidatePromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for path in (
            "plugins/skills-factory-lab",
            "plugins/skills-factory",
            "dist/chatgpt-skills",
            "docs",
            "release",
        ):
            (self.root / path).mkdir(parents=True, exist_ok=True)
        self.revision = "a" * 40
        lab = {
            "source_revision": self.revision,
            "release_id": "0.33.1+aaaaaaaaaaaa",
            "payload_content_sha256": "b" * 64,
            "version": "0.33.1",
            "channel": "lab",
        }
        self._write("plugins/skills-factory-lab/release-manifest.json", lab)
        self._write("docs/lab-release.json", lab)
        self._write("plugins/skills-factory/release-manifest.json", {
            "source_revision": self.revision, "channel": "plugin"
        })
        self._write("dist/chatgpt-skills/release-manifest.json", {
            "source_revision": self.revision, "channel": "chatgpt-zip"
        })
        self._write("release/promotion-evidence.json", {
            "source_revision": self.revision,
            "lab_release_id": lab["release_id"],
            "lab_payload_content_sha256": lab["payload_content_sha256"],
            "status": "PASS",
            "run_id": "123456",
            "run_url": "https://github.com/aras-2003/skills-factory/actions/runs/123456",
            "observed_at": "2026-10-06T10:00:00Z",
        })

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, relative: str, value: dict) -> None:
        (self.root / relative).write_text(json.dumps(value), encoding="utf-8")

    def test_accepts_production_artifacts_bound_to_lab_receipt(self) -> None:
        self.assertEqual([], validate_promotion(self.root, require_ancestor=False))

    def test_rejects_a_production_package_from_another_source(self) -> None:
        self._write("plugins/skills-factory/release-manifest.json", {
            "source_revision": "c" * 40, "channel": "plugin"
        })
        errors = validate_promotion(self.root, require_ancestor=False)
        self.assertTrue(any("exact Lab source revision" in error for error in errors))

    def test_rejects_runtime_evidence_for_another_lab_digest(self) -> None:
        evidence = json.loads((self.root / "release/promotion-evidence.json").read_text())
        evidence["lab_payload_content_sha256"] = "d" * 64
        self._write("release/promotion-evidence.json", evidence)
        errors = validate_promotion(self.root, require_ancestor=False)
        self.assertTrue(any("exact Lab candidate" in error for error in errors))

    def test_rejects_nonhex_lab_source_revision(self) -> None:
        lab = json.loads((self.root / "plugins/skills-factory-lab/release-manifest.json").read_text())
        lab["source_revision"] = "g" * 40
        self._write("plugins/skills-factory-lab/release-manifest.json", lab)
        errors = validate_promotion(self.root, require_ancestor=False)
        self.assertTrue(any("full 40-character source_revision" in e for e in errors))

    def test_rejects_nonhex_lab_payload_digest(self) -> None:
        lab = json.loads((self.root / "plugins/skills-factory-lab/release-manifest.json").read_text())
        lab["payload_content_sha256"] = "z" * 64
        self._write("plugins/skills-factory-lab/release-manifest.json", lab)
        errors = validate_promotion(self.root, require_ancestor=False)
        self.assertTrue(any("SHA-256 payload digest" in e for e in errors))

    def test_rejects_missing_runtime_receipt(self) -> None:
        (self.root / "release/promotion-evidence.json").unlink()
        errors = validate_promotion(self.root, require_ancestor=False)
        self.assertTrue(any("promotion-evidence.json" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
