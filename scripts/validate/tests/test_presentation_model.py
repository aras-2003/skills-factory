from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))

from common import load_json  # noqa: E402
from presentation_model import normalize_legacy_deck, validate_deck  # noqa: E402


class PresentationModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(ROOT / "workflows/presentation-production/references/canonical-deck-v1.schema.json")
        cls.fixture = json.loads((ROOT / "docs/presentations/examples/canonical-deck-v1.json").read_text(encoding="utf-8"))

    def test_synthetic_fixture_is_valid(self) -> None:
        self.assertEqual([], validate_deck(self.fixture, self.schema))

    def test_json_round_trip_preserves_value_unit_source_notes_and_layout_tokens(self) -> None:
        encoded = json.dumps(self.fixture, ensure_ascii=False)
        decoded = json.loads(encoded)
        self.assertEqual(self.fixture, decoded)
        slide = decoded["slides"][0]
        self.assertEqual(1234567.89, slide["data_refs"][0]["value"])
        self.assertEqual("EUR", slide["data_refs"][0]["unit"])
        self.assertEqual(["synthetic:revenue-source"], slide["data_refs"][0]["source_ids"])
        self.assertEqual("Keep the synthetic-data caveat when reusing this fixture.", slide["notes"])
        self.assertEqual("12-column", slide["layout"]["tokens"]["grid"])

    def test_rejects_duplicate_slide_ids_and_dangling_exhibit_data(self) -> None:
        broken = json.loads(json.dumps(self.fixture))
        broken["slides"].append(json.loads(json.dumps(broken["slides"][0])))
        broken["slides"][0]["exhibits"][0]["supported_data"] = ["missing"]
        messages = "\n".join(issue.message for issue in validate_deck(broken, self.schema))
        self.assertIn("Duplicate ID", messages)
        self.assertIn("references missing data_ref_id", messages)

    def test_rejects_unknown_source_when_catalog_exists(self) -> None:
        broken = json.loads(json.dumps(self.fixture))
        broken["slides"][0]["data_refs"][0]["source_ids"] = ["missing-source"]
        self.assertTrue(any("absent from deck.sources" in issue.message for issue in validate_deck(broken, self.schema)))

    def test_normalizer_archives_full_legacy_input_and_does_not_guess_editability(self) -> None:
        legacy = {
            "deck_id": "legacy", "slides": [{"id": "s1", "role": "insight", "headline": "A claim",
                "claim_ids": ["c1"], "speaker_notes": "Preserve this", "editability": "EDITABLE_NATIVE",
                "layout_id": "two-column", "custom_field": {"kept": True}}],
        }
        normalized, warnings = normalize_legacy_deck(legacy)
        slide = normalized["slides"][0]
        self.assertEqual("s1", slide["slide_id"])
        self.assertEqual("A claim", slide["action_title"])
        self.assertEqual("Preserve this", slide["notes"])
        self.assertEqual("UNKNOWN", slide["desired_editability"])
        self.assertEqual(legacy, normalized["extensions"]["legacy_source"])
        self.assertEqual(legacy["slides"][0], slide["extensions"]["legacy_source"])
        self.assertTrue(any("editability" in warning for warning in warnings))
        self.assertEqual([], validate_deck(normalized, self.schema))


if __name__ == "__main__":
    unittest.main()
