"""python3 -m unittest discover -s tests/architecture -p 'test_visualization_ir.py'"""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from scripts.architecture.visualization_ir import (
    ModelValidationError, canonical_json, model_digest, validate_model, verify_sources,
)
SHA="a"*40
SOURCE={"uri":"repo://docs/example.md","revision":SHA,"locator":"L1-L2"}
def fixture():
    def node(id_,type_):
        return {"id":id_,"type":type_,"label":id_,"state":"observed","evidence":[copy.deepcopy(SOURCE)]}
    return {"schema_version":1,"model_id":"sample","source_revision":SHA,
            "nodes":[node("b","tool"),node("a","skill")],
            "edges":[{"id":"edge","type":"calls","from":"a","to":"b","state":"observed",
                      "evidence":[copy.deepcopy(SOURCE)]}]}

class VisualizationIRTests(unittest.TestCase):
    def test_stable_output_and_digest(self):
        one=fixture()
        two=copy.deepcopy(one)
        two["nodes"].reverse()
        self.assertEqual(canonical_json(one),canonical_json(two))
        self.assertEqual(model_digest(one),model_digest(two))
        self.assertEqual([x["id"] for x in validate_model(one)["nodes"]],["a","b"])

    def test_workflow_can_depend_on_an_explicit_process_gate(self):
        obj=fixture()
        obj["nodes"][1]["type"]="workflow"
        obj["nodes"].append({
            "id":"gate","type":"process","label":"Documented failure gate",
            "state":"observed","evidence":[copy.deepcopy(SOURCE)],
        })
        obj["edges"].append({
            "id":"workflow-gate","type":"depends_on","from":"a","to":"gate",
            "state":"observed","evidence":[copy.deepcopy(SOURCE)],
        })
        validate_model(obj)

    def test_workflow_can_call_another_workflow(self):
        obj=fixture()
        obj["nodes"][0]["type"]="workflow"
        obj["nodes"][1]["type"]="workflow"
        validate_model(obj)

    def test_skill_and_workflow_can_depend_on_documented_data(self):
        for source_type in ("skill", "workflow"):
            obj=fixture()
            next(node for node in obj["nodes"] if node["id"]=="a")["type"]=source_type
            obj["nodes"].append({
                "id":"data","type":"data","label":"Documented data source",
                "state":"observed","evidence":[copy.deepcopy(SOURCE)],
            })
            obj["edges"].append({
                "id":"data-dependency","type":"depends_on","from":"a","to":"data",
                "state":"observed","evidence":[copy.deepcopy(SOURCE)],
            })
            with self.subTest(source_type=source_type):
                validate_model(obj)

    def test_invalid_types_duplicate_dangling_implicit_edge(self):
        changes=[
            lambda x:x["nodes"].append(copy.deepcopy(x["nodes"][0])),
            lambda x:x["edges"][0].update({"to":"missing"}),
            lambda x:x["edges"][0].update({"type":"owns"}),
            lambda x:x["edges"][0].update({"type":[]}),
            lambda x:x["nodes"][0].update({"state":{}}),
            lambda x:x["edges"][0].update({"inferred":True}),
            lambda x:x.update({"schema_version":True}),
        ]
        for change in changes:
            obj=fixture()
            change(obj)
            with self.subTest(obj=obj),self.assertRaises(ModelValidationError):
                validate_model(obj)

    def test_unknown_is_explicit_and_unsubstantiated(self):
        obj=fixture()
        obj["nodes"][0].update({"state":"unknown","evidence":[]})
        with self.assertRaises(ModelValidationError):
            validate_model(obj)
        obj["edges"][0].update({"state":"unknown","type":"unknown","evidence":[]})
        validate_model(obj)
        obj["edges"][0]["evidence"]=[copy.deepcopy(SOURCE)]
        with self.assertRaises(ModelValidationError):
            validate_model(obj)

    def test_rejects_mismatched_revision_and_unsafe_sources(self):
        bad=[
            {"uri":"repo://../secret","revision":SHA,"locator":"L1"},
            {"uri":"repo:///etc/passwd","revision":SHA,"locator":"L1"},
            {"uri":"repo://docs\\bad","revision":SHA,"locator":"L1"},
            {"uri":"https://attacker.invalid/a","revision":SHA,"locator":"L1"},
            {"uri":"repo://docs/example.md","revision":"b"*40,"locator":"L1"},
            {"uri":"repo://docs/example.md","revision":SHA,"locator":"L0"},
            {"uri":"repo://docs/example.md","revision":SHA,"locator":"L2-L1"},
        ]
        for ref in bad:
            obj=fixture()
            obj["edges"][0]["evidence"]=[ref]
            with self.subTest(ref=ref),self.assertRaises(ModelValidationError):
                validate_model(obj)

    def test_verified_exact_git_commit_and_line_range(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def git(*args):
                return subprocess.check_output(["git","-C",directory,*args],stderr=subprocess.DEVNULL).decode().strip()
            git("init","-q")
            git("config","user.name","Fixture")
            git("config","user.email","fixture@example.invalid")
            (root/"docs").mkdir()
            (root/"docs/example.md").write_text("line one\nline two\n",encoding="utf-8")
            git("add",".")
            git("commit","-qm","fixture")
            rev=git("rev-parse","HEAD")
            obj=fixture()
            obj["source_revision"]=rev
            for record in obj["nodes"]+obj["edges"]:
                for source in record["evidence"]:
                    source["revision"]=rev
            self.assertEqual(verify_sources(obj,root)["source_revision"],rev)
            (root/"docs/example.md").write_text("UNCOMMITTED REPLACEMENT\n",encoding="utf-8")
            verify_sources(obj,root)  # immutable commit object, not mutable checkout
            obj["edges"][0]["evidence"][0]["locator"]="L3"
            with self.assertRaises(ModelValidationError):
                verify_sources(obj,root)
            obj["edges"][0]["evidence"][0].update({"locator":"L1","uri":"repo://docs/missing.md"})
            with self.assertRaises(ModelValidationError):
                verify_sources(obj,root)

if __name__=="__main__":
    unittest.main()
