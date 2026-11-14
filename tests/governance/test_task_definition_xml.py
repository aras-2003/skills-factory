"""The proposed human-readable TDC XML example remains well-formed and complete."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


DOC = Path(__file__).resolve().parents[2] / "docs/governance/TASK-DEFINITION-STANDARD.md"


class TaskDefinitionXmlTest(unittest.TestCase):
    def test_documented_xml_format_has_readable_planning_metadata(self):
        text = DOC.read_text(encoding="utf-8")
        match = re.search(
            r"## Minimal XML representation.*?```xml\s*(.*?)\s*```",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "TDC XML example is missing")
        root = ET.fromstring(match.group(1))
        self.assertEqual(root.tag, "task_definition")
        self.assertEqual(root.attrib.get("version"), "1.2")

        metadata = root.find("planning_metadata")
        self.assertIsNotNone(metadata)
        for tag, code_attribute in (("priority", "code"), ("size", "code")):
            element = metadata.find(tag)
            self.assertIsNotNone(element)
            self.assertTrue(element.attrib.get(code_attribute))
            self.assertTrue(element.text and len(element.text.strip()) > 20)
        for tag in ("area", "project_status", "project_iteration"):
            element = metadata.find(tag)
            self.assertIsNotNone(element)
            self.assertTrue(element.text and len(element.text.strip()) > 10)

        impact = root.find("architecture_impact")
        self.assertIsNotNone(impact)
        self.assertIn(impact.attrib.get("level"), {"A0", "A1", "A2", "A3", "A4"})
        self.assertEqual(impact.attrib.get("review_state"), "PROPOSED")
        self.assertTrue(impact.findtext("summary"))


if __name__ == "__main__":
    unittest.main()
