"""ARC-06 export bundle contract tests using one exact evidence-aware fixture."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from scripts.architecture.export_bundle import ExportError, FORMAT_MATRIX, build_export_bundle

REV = "a" * 40
REF = {"uri": "repo://docs/example.md", "revision": REV, "locator": "L1"}


def fixture():
    def node(node_id, kind, label, state="observed", evidence=None):
        return {"id": node_id, "type": kind, "label": label, "state": state,
                "evidence": copy.deepcopy(REF if evidence is None else evidence)}
    return {
        "schema_version": 1,
        "model_id": "arc06-export-fixture",
        "source_revision": REV,
        "nodes": [
            node("workflow:root", "workflow", "Root <script>alert(1)</script>"),
            node("tool:report", "tool", "Report renderer"),
            node("unknown:owner", "unknown", "Unverified owner", state="unknown", evidence=[]),
        ],
        "edges": [
            {"id": "edge:calls", "type": "calls", "from": "workflow:root", "to": "tool:report",
             "state": "observed", "evidence": [copy.deepcopy(REF)]},
            {"id": "edge:unknown", "type": "unknown", "from": "workflow:root", "to": "unknown:owner",
             "state": "unknown", "evidence": []},
        ],
    }


class ExportBundleTests(unittest.TestCase):
    def test_one_fixture_retains_all_model_ids_metadata_and_unknowns(self):
        model = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bundle"
            result = build_export_bundle(model, out)
            svg = (out / "architecture.svg").read_text(encoding="utf-8")
            equivalent = (out / "architecture.txt").read_text(encoding="utf-8")
            manifest = json.loads((out / "export-manifest.json").read_text(encoding="utf-8"))

        root = ElementTree.fromstring(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIsNotNone(root.find("svg:title", ns))
        self.assertIsNotNone(root.find("svg:desc", ns))
        self.assertIn("data-model-id", svg)
        for node in model["nodes"]:
            self.assertIn(node["id"], svg)
            self.assertIn(node["id"], equivalent)
            self.assertIn(node["id"], manifest["node_ids"])
        for edge in model["edges"]:
            self.assertIn(edge["id"], svg)
            self.assertIn(edge["id"], equivalent)
            self.assertIn(edge["id"], manifest["edge_ids"])
        self.assertIn("UNKNOWN", svg)
        self.assertIn("UNKNOWN", equivalent)
        self.assertIn("&lt;script&gt;", svg)
        self.assertNotIn("<script>", svg)
        self.assertEqual(manifest["source_revision"], REV)
        self.assertEqual(manifest["node_count"], len(model["nodes"]))
        self.assertEqual(manifest["edge_count"], len(model["edges"]))
        self.assertEqual(result["model_digest"], manifest["model_digest"])

    def test_export_matrix_is_explicit_about_flattening_and_boundaries(self):
        self.assertEqual(set(FORMAT_MATRIX), {"html", "svg", "png", "docx", "pdf", "pptx"})
        self.assertTrue(FORMAT_MATRIX["html"]["mode"] == "interactive")
        self.assertTrue(FORMAT_MATRIX["svg"]["generated_here"])
        for name in ("png", "docx", "pdf", "pptx"):
            self.assertFalse(FORMAT_MATRIX[name]["generated_here"])
            self.assertIn("architecture.txt", FORMAT_MATRIX[name]["accessible_equivalent"])
        self.assertIn("editable native shapes are not generated", FORMAT_MATRIX["pptx"]["embedding"])

    def test_output_must_be_fresh_and_non_symlinked(self):
        model = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bundle"
            out.mkdir()
            (out / "keep.txt").write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(ExportError, "fresh empty"):
                build_export_bundle(model, out)
            target = Path(tmp) / "target"
            target.mkdir()
            link = Path(tmp) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ExportError):
                build_export_bundle(model, link)
            self.assertEqual((out / "keep.txt").read_text(encoding="utf-8"), "preserve")

    def test_invalid_ir_fails_before_artifacts_are_written(self):
        model = fixture()
        model["edges"][0]["to"] = "missing"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bundle"
            with self.assertRaises(ValueError):
                build_export_bundle(model, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
