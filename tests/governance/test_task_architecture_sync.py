"""No-network verification of native Project Architecture Impact synchronization."""
import importlib.util
import hashlib
import pathlib
import tempfile
import json
import unittest
from unittest.mock import patch

PATH=pathlib.Path(__file__).resolve().parents[2]/"scripts/governance/sync_task_architecture.py"
spec=importlib.util.spec_from_file_location("sync_task_architecture", PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
OPTIONS=[{"id":level.lower(),"name":level} for level in ("A0","A1","A2","A3","A4")]

class ArchitectureSyncTest(unittest.TestCase):
    def test_manifest_valid_and_issue_specific(self):
        data=mod.load_manifest()
        self.assertEqual(len(data),110)
        self.assertNotEqual(data["163"]["change_description"],data["297"]["change_description"])
        self.assertTrue(all(x["level"] in mod.VALID for x in data.values()))

    def test_option_exact_not_inferred(self):
        fields=[{"id":"f","name":"Architecture Impact","options":OPTIONS+[ {"id":"medium","name":"Medium"}]}]
        self.assertEqual(mod.option_id(fields,"A2"),("f","a2"))
        with self.assertRaises(RuntimeError): mod.option_id(fields,"Medium")

    def test_all_canonical_options_are_required(self):
        fields=[{"id":"f","name":"Architecture Impact","options":[{"id":value.lower(),"name":value} for value in ["A0","A1","A2","A3"]]}]
        with self.assertRaisesRegex(RuntimeError,"options missing or ambiguous.*A4"):
            mod.option_id(fields,"A2")

    def test_text_field_contains_issue_specific_change(self):
        fields=[{"id":"text-field","name":"Architecture Impact","dataType":"TEXT"}]
        row={"level":"A3","change_description":"Replace X interface with backward compatible typed API.","architecture_reason":"A3 cross-component schema change requiring review."}
        self.assertEqual(mod.field_target(fields,row)[0:2],("text-field","text"))
        value=mod.field_target(fields,row)[2]
        self.assertIn("A3",value)
        self.assertIn("Replace X interface",value)
        self.assertLessEqual(len(value),1000)

    def test_text_field_readback(self):
        data={"node":{"fieldValues":{"nodes":[{"text":"A2 — impact description","field":{"name":"Architecture Impact"}}]}}}
        self.assertEqual(mod.field_values(data),["A2 — impact description"])

    def test_duplicate_field_refused(self):
        f={"id":"f","name":"Architecture Impact","options":OPTIONS}
        with self.assertRaises(RuntimeError): mod.option_id([f,f],"A2")

    def test_dry_run_has_no_mutation(self):
        item={"id":"item","project":{"id":"project"}}
        data={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[item]}}}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",return_value=data) as gql:
            self.assertEqual(mod.sync_one(42,{"title":"Example","level":"A2","review":"PROPOSED"},False),"DRY_RUN")
            self.assertEqual(gql.call_count,1)

    def test_changed_title_refused(self):
        data={"user":{"projectV2":{"id":"project","fields":{"nodes":[]}},"repository":{"issue":{"title":"Different","state":"OPEN","projectItems":{"nodes":[]}}}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",return_value=data):
            with self.assertRaisesRegex(RuntimeError,"title changed"):
                mod.sync_one(42,{"title":"Example","level":"A2"},False)

    def test_missing_project_membership_refused(self):
        data={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[]}}}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",return_value=data):
            with self.assertRaisesRegex(RuntimeError,"expected exactly one existing project item"):
                mod.sync_one(42,{"title":"Example","level":"A2","review":"PROPOSED"},False)

    def test_apply_requires_explicit_approved_assessment(self):
        with patch.object(mod.sync,"gql") as gql:
            with self.assertRaisesRegex(RuntimeError,"not approved"):
                mod.sync_one(42,{"title":"Example","level":"A2","review":"PROPOSED"},True)
            gql.assert_not_called()

    def test_apply_readback(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        third={"node":{"fieldValues":{"nodes":[{"name":"A2","field":{"name":"Architecture Impact"}}]}}}
        before={"node":{"fieldValues":{"nodes":[]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,before,{},third]) as gql:
            self.assertEqual(mod.sync_one(42,{"title":"Example","level":"A2","review":"APPROVED"},True),"VERIFIED")
            self.assertEqual(gql.call_count,4)

    def test_does_not_overwrite_manual_value(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        previous={"node":{"fieldValues":{"nodes":[{"name":"A3","field":{"name":"Architecture Impact"}}]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,previous]) as gql:
            with self.assertRaisesRegex(RuntimeError,"refusing overwrite"):
                mod.sync_one(42,{"title":"Example","level":"A2","review":"APPROVED"},True)
            self.assertEqual(gql.call_count,2)

    def test_existing_equal_value_does_not_write(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        previous={"node":{"fieldValues":{"nodes":[{"name":"A2","field":{"name":"Architecture Impact"}}]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,previous]) as gql:
            self.assertEqual(mod.sync_one(42,{"title":"Example","level":"A2","review":"APPROVED"},True),"ALREADY_VERIFIED")
            self.assertEqual(gql.call_count,2)

    def test_closed_issue_without_matching_value_is_not_written(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"CLOSED","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        empty={"node":{"fieldValues":{"nodes":[]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,empty]) as gql:
            with self.assertRaisesRegex(RuntimeError,"closed after manifest capture"):
                mod.sync_one(42,{"title":"Example","level":"A2","review":"APPROVED"},True)
            self.assertEqual(gql.call_count,2)

    def test_manifest_refuses_ambiguity(self):
        invalid={"schema":"tdc-architecture-batch-v1","repository":"aras-2003/skills-factory","expected_issue_count":1,"expected_issue_ids_sha256":hashlib.sha256(b"42\n").hexdigest(),"issues":{"42":{"title":"Example item has enough words","level":"UNKNOWN","review":"PROPOSED","change_description":"A concrete change detailed here more than enough","architecture_reason":"Some architecture reasoning here longer than 25 characters","acceptance_summary":"Acceptance details with evidence requirements"}}}
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"data.json";p.write_text(json.dumps(invalid))
            with self.assertRaisesRegex(ValueError,"Invalid architecture impact"):
                mod.load_manifest(p)

    def test_manifest_refuses_truncated_issue_set(self):
        data=json.loads(mod.MANIFEST.read_text(encoding="utf-8"))
        data["issues"].pop(next(iter(data["issues"])))
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"data.json";p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"count mismatch"):
                mod.load_manifest(p)

    def test_manifest_refuses_issue_id_lock_mismatch(self):
        data=json.loads(mod.MANIFEST.read_text(encoding="utf-8"))
        data["expected_issue_ids_sha256"]="0"*64
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"data.json";p.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"Issue ID lock mismatch"):
                mod.load_manifest(p)

    def test_apply_readback_mismatch_fails(self):
        first={"user":{"projectV2":{"id":"project","fields":{"nodes":[{"id":"f","name":"Architecture Impact","options":OPTIONS}]}},"repository":{"issue":{"title":"Example","state":"OPEN","projectItems":{"nodes":[{"id":"item","project":{"id":"project"}}]}}}}}
        before={"node":{"fieldValues":{"nodes":[]}}}
        wrong={"node":{"fieldValues":{"nodes":[{"name":"A3","field":{"name":"Architecture Impact"}}]}}}
        with patch.dict(mod.os.environ,{"GH_REPOSITORY":"aras-2003/skills-factory"}),patch.object(mod.sync,"gql",side_effect=[first,before,{},wrong]):
            with self.assertRaisesRegex(RuntimeError,"readback mismatch"):
                mod.sync_one(42,{"title":"Example","level":"A2","review":"APPROVED"},True)

if __name__=="__main__": unittest.main()
