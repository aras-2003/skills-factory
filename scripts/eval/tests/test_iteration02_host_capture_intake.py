import hashlib
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from iteration02_host_capture_intake import ingest


class CaptureIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.pack=self.root/'pack';(self.pack/'desktop').mkdir(parents=True)
        self.case='I02-240-local-runner';prompt=b'Synthetic task.\n';self.digest=hashlib.sha256(prompt).hexdigest()
        (self.pack/'desktop'/f'{self.case}.input.md').write_bytes(prompt)
        identity={'source_revision':'a'*40,'release_id':'fixture','payload_content_sha256':'b'*64}
        item={**identity,'case_id':self.case,'channel':'desktop','repetitions':1,'input_path':f'desktop/{self.case}.input.md','input_sha256':self.digest,'rubric_sha256':'c'*64,'execution_state':'NOT_RUN','provider_dispatch':'BLOCKED_PENDING_APPROVAL_AND_INSTALLED_IDENTITY'}
        (self.pack/'external-lock.json').write_text(json.dumps({**identity,'kind':'external_test_inputs_only','runtime_evidence':'NOT_RUN','provider_calls_executed':False,'release_approved':False,'cases':[item]}))
        self.capture={**identity,'case_id':self.case,'attempt':1,'channel':'desktop','kind':'cua_host_capture','execution_state':'executed','input_sha256':self.digest,'approval_reference':'fixture approval','installed_observation_source':'fixture identity','response':'Synthetic result','model_behavior_verdict':'NOT_EVALUATED','artifacts':{}}
        for stage in ('before','after'):
            image=self.root/f'{stage}.png';image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
            ax=self.root/f'{stage}.txt';ax.write_text('Synthetic AX')
            self.capture['artifacts'][stage]={'screenshot_path':image.name,'screenshot_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'accessible_path':ax.name,'accessible_sha256':hashlib.sha256(ax.read_bytes()).hexdigest(),'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'client_reference':'fixture://native'}
        self.path=self.root/'capture.json';self.save()

    def save(self):self.path.write_text(json.dumps(self.capture))
    def test_source_capture_is_review_required_not_model_pass(self):
        r=ingest(self.pack,self.path);self.assertEqual('HOST_CAPTURE_BOUND_REVIEW_REQUIRED',r['status']);self.assertFalse(r['release_approved'])
    def test_input_tamper_and_missing_approval_block(self):
        self.capture['input_sha256']='f'*64;self.save()
        with self.assertRaises(ValueError):ingest(self.pack,self.path)
        self.capture['input_sha256']=self.digest;self.capture['approval_reference']='';self.save()
        with self.assertRaises(ValueError):ingest(self.pack,self.path)
    def test_image_tamper_and_escape_block(self):
        self.capture['artifacts']['after']['screenshot_sha256']='f'*64;self.save()
        with self.assertRaises(ValueError):ingest(self.pack,self.path)
        self.capture['artifacts']['after']['screenshot_path']='../private.png';self.save()
        with self.assertRaises(ValueError):ingest(self.pack,self.path)
