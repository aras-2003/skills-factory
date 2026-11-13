"""No-network verification of native Project Architecture Impact synchronization."""
import importlib.util
import pathlib
import tempfile
import json
import unittest
from unittest.mock import patch

PATH=pathlib.Path(__file__).resolve().parents[2]/"scripts/governance/sync_task_architecture.py"
spec=importlib.util.spec_from_file_location("sync_task_architecture", PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ArchitectureSyncTest(unittest.TestCase):
    def test_manifest_valid_and_issue_specific(self):
        data=mod.load_manifest()
        self.assertEqual(len(data),110)
        self.assertNotEqual(data["163"]["change_description"],data["297"]["change_description"])
        self.assertTrue(all(x["level"] in mod.VALID for x in data.values()))

    def test_option_exact_not_inferred(self):
        fields=[{"id":"f","name":"Architecture Impact","options":[{"id":"a","name":"A2"},{"id":"b","name":"A3"}]}]
        self.assertEqual(mod.option_id(fields,"A2"),("f","a"))
        with self.assertRaises(RuntimeError): mod.option_id(fields,"Medium")

    def test_duplicate_field_refused(self):
        f={"id":"f","name":"Architecture Impact","options":[{"id":"a","name":"A2"}]}
        with self.assertRaises(RuntimeError): mod.option_id([f,f],"A2")

    def test_dry_run_has_no_mutation(self):
        item={"id":"item","project":{"id":"project"}}
        data={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":[{"id":"a","name":"A2"}]}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[item]}}}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",return_value=data) as gql:
            self.assertEqual(mod.sync_one(42,{"title":"Example","level":"A2","review":"PROPOSED"},False),"DRY_RUN")
            self.assertEqual(gql.call_count,1)

    def test_changed_title_refused(self):
        data={"user":{"projectV2":{"id":"project","fields":{"nodes":[]}},"repository":{"issue":{"title":"Different","state":"OPEN","projectItems":{"nodes":[]}}}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",return_value=data):
            with self.assertRaisesRegex(RuntimeError,"title changed"):
                mod.sync_one(42,{"title":"Example","level":"A2"},False)

    def test_apply_readback(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":[{"id":"a","name":"A2"}]}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        third={"node":{"fieldValues":{"nodes":[{"name":"A2","field":{"name":"Architecture Impact"}}]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,{},third]) as gql:
            self.assertEqual(mod.sync_one(42,{"title":"Example","level":"A2"},True),"VERIFIED")
            self.assertEqual(gql.call_count,3)

    def test_manifest_refuses_ambiguity(self):
        invalid={"schema":"tdc-architecture-batch-v1","repository":"aras-2003/skills-factory","issues":{"42":{"title":"Example item has enough words","level":"UNKNOWN","review":"PROPOSED","change_description":"A concrete change detailed here more than enough","architecture_reason":"Some architecture reasoning here longer than 25 characters","acceptance_summary":"Acceptance details with evidence requirements"}}}
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"data.json";p.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):mod.load_manifest(p)

if __name__=="__main__": unittest.main()
