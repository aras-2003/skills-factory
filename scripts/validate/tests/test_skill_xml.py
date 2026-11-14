from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
from validate_skill_xml import XmlValidationError, validate_skill_file, validate_xml_body  # noqa: E402

FIXTURES = HERE.parent / "fixtures" / "skill-xml"


class SkillXmlValidationTests(unittest.TestCase):
    def test_valid_fixture(self) -> None:
        validate_xml_body((FIXTURES / "valid.xml").read_text(encoding="utf-8"))

    def test_malformed_xml_reports_line(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, r"malformed XML"):
            validate_xml_body((FIXTURES / "malformed.xml").read_text(encoding="utf-8"))

    def test_missing_required_section(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, "required section <steps>"):
            validate_xml_body((FIXTURES / "missing-section.xml").read_text(encoding="utf-8"))

    def test_empty_or_placeholder_content(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, "meaningful text"):
            validate_xml_body((FIXTURES / "placeholder.xml").read_text(encoding="utf-8"))

    def test_duplicate_section(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, "duplicate top-level section <purpose>"):
            validate_xml_body((FIXTURES / "duplicate.xml").read_text(encoding="utf-8"))

    def test_unknown_section(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, "unknown top-level section <summary>"):
            validate_xml_body((FIXTURES / "unknown.xml").read_text(encoding="utf-8"))

    def test_entity_declarations_are_rejected(self) -> None:
        with self.assertRaisesRegex(XmlValidationError, "declarations are not allowed"):
            validate_xml_body((FIXTURES / "untrusted-entity.xml").read_text(encoding="utf-8"))

    def test_template_has_valid_frontmatter_and_xml(self) -> None:
        validate_skill_file(HERE.parents[3] / "templates" / "skill-template" / "SKILL.md")


if __name__ == "__main__":
    unittest.main()
