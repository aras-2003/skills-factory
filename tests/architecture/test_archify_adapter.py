"""ARC-03 adapter tests: no upstream execution required for static path."""
import copy
import unittest
from unittest.mock import patch
from scripts.architecture.archify_adapter import archify_candidate,offline_svg_fallback,render,RenderError

REV="a"*40
REF={"uri":"repo://docs/example.md","revision":REV,"locator":"L1"}
def sample():
    def node(id_,kind,label):
        return {"id":id_,"type":kind,"label":label,"state":"observed","evidence":[REF]}
    return {"schema_version":1,"model_id":"arc3","source_revision":REV,
            "nodes":[node("a","skill","<script>alert(1)</script>"),node("b","tool","Tool")],
            "edges":[{"id":"ab","type":"calls","from":"a","to":"b",
                      "state":"observed","evidence":[REF]}]}

class AdapterTests(unittest.TestCase):
    def test_repeatable_adapter(self):
        obj=sample()
        a=archify_candidate(obj)
        self.assertEqual(a,archify_candidate(copy.deepcopy(obj)))
        self.assertEqual(a["diagram_type"],"architecture")
        self.assertEqual(len(a["connections"]),1)
        self.assertEqual(a["connections"][0]["from"],"n0")
        self.assertEqual(a["connections"][0]["to"],"n1")

    def test_safe_static_fallback_escapes_content(self):
        out=offline_svg_fallback(sample())
        self.assertIn("&lt;script&gt;",out)
        self.assertNotIn("<script>",out)
        self.assertNotIn("javascript:",out)
        self.assertNotIn("<foreignObject",out)
        self.assertIn("<svg",out)

    def test_unknown_edge_is_dashed(self):
        m=sample()
        m["edges"][0].update(type="unknown",state="unknown",evidence=[])
        self.assertEqual(archify_candidate(m)["connections"][0]["variant"],"dashed")

    def test_invalid_relation_fail_closed(self):
        m=sample()
        m["edges"][0]["to"]="ghost"
        with self.assertRaises(ValueError):
            archify_candidate(m)

    def test_render_requires_verified_canonical_sources(self):
        with patch("scripts.architecture.archify_adapter.verify_sources",side_effect=ValueError("unverified")):
            with self.assertRaises(ValueError):
                render(sample(),"/nonexistent","/nonexistent","/nonexistent")

if __name__=="__main__":
    unittest.main()
