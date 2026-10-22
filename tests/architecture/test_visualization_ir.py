"""Run: python3 -m unittest discover -s tests/architecture -p 'test_visualization_ir.py'"""
import copy
import unittest

from scripts.architecture.visualization_ir import ModelValidationError, canonical_json, model_digest, validate_model


def fixture():
    src = {"uri": "repo://skills/oaf/README.md", "revision": "sha256:demo", "locator": "L1-L2"}
    node = lambda key: {"id": key, "type": "skill", "label": key, "state": "observed", "evidence": [src]}
    return {"schema_version": 1, "model_id": "demo", "source_revision": "sha256:demo",
            "nodes": [node("b"), node("a")],
            "edges": [{"id": "edge", "type": "calls", "from": "a", "to": "b", "state": "observed", "evidence": [src]}]}


class VisualizationIRTests(unittest.TestCase):
    def test_valid_and_order_independent(self):
        one = fixture()
        two = copy.deepcopy(one)
        two["nodes"].reverse()
        self.assertEqual(canonical_json(one), canonical_json(two))
        self.assertEqual(model_digest(one), model_digest(two))
        self.assertEqual([x["id"] for x in validate_model(one)["nodes"]], ["a", "b"])

    def test_unknown_allowed_only_explicit(self):
        m = fixture()
        m["nodes"][0]["state"] = "unknown"
        m["nodes"][0]["evidence"] = []
        with self.assertRaises(ModelValidationError):
            validate_model(m)
        m["edges"][0]["state"] = "unknown"
        m["edges"][0]["evidence"] = []
        validate_model(m)

    def test_rejects_dangling_duplicate_and_stale(self):
        for change in ("dangling", "duplicate", "stale"):
            m = fixture()
            if change == "dangling":
                m["edges"][0]["to"] = "missing"
            elif change == "duplicate":
                m["nodes"].append(copy.deepcopy(m["nodes"][0]))
            else:
                m["edges"][0]["evidence"][0] = dict(m["edges"][0]["evidence"][0], revision="old")
            with self.subTest(change=change), self.assertRaises(ModelValidationError):
                validate_model(m)

    def test_no_unsupported_or_implicit_data(self):
        for key, val in (("type", "fabricated"), ("state", "certain")):
            m = fixture()
            m["edges"][0][key] = val
            with self.assertRaises(ModelValidationError):
                validate_model(m)
        m = fixture()
        m["edges"][0]["inferred"] = True
        with self.assertRaises(ModelValidationError):
            validate_model(m)

    def test_rejects_disallowed_uri_and_control_chars(self):
        m = fixture()
        m["nodes"][0]["evidence"][0] = {"uri": "javascript:alert(1)", "revision": "sha256:demo", "locator": "x"}
        with self.assertRaises(ModelValidationError):
            validate_model(m)
        m = fixture()
        m["nodes"][0]["label"] = "bad\nlabel"
        with self.assertRaises(ModelValidationError):
            validate_model(m)


if __name__ == "__main__":
    unittest.main()
