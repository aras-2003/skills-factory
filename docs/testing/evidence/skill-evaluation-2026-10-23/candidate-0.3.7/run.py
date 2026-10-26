from pathlib import Path
import json,hashlib,urllib.request,subprocess,datetime
repo=Path(__file__).resolve().parent
out=repo/'docs/testing/evidence/skill-evaluation-2026-10-23/candidate-0.3.7'
out.mkdir(exist_ok=True)
sha=lambda data:hashlib.sha256(data).hexdigest()
prior=json.loads((out.parent/'candidate-0.3.5/plan.json').read_text())
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
skill=(repo/'skills/meta/skill-evaluation/SKILL.md').read_text()
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=10) as response:models=json.load(response)['models']
identity=next(m for m in models if m['name']==prior['model'])
assert identity['digest']==prior['model_identity']['digest']
for case in prior['cases']:
 assert sha(case['prompt'].encode())==case['input_sha256']
plan={'source_revision':source,'candidate_version':'0.3.7','instruction_sha256':sha(skill.encode()),'model':prior['model'],'model_identity':identity,'options':prior['options'],'cases':prior['cases'],'executor_rubric_access':False,'repetitions':1,'decision_threshold':prior['decision_threshold'],'scope':'Source-pinned local tool-free model; not installed Lab/Site behavior or general certification','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
plan_path=out/'plan.json'
with plan_path.open('x') as f:json.dump(plan,f,indent=2,ensure_ascii=False)
(out/'plan.sha256').write_text(sha(plan_path.read_bytes()))
(out/'instructions.md').write_text(skill)
print('PLAN_FROZEN',sha(plan_path.read_bytes()),flush=True)
for case in plan['cases']:
 request={'model':plan['model'],'stream':False,'think':False,'options':plan['options'],'messages':[{'role':'system','content':'Answer the user task concisely. You have no tools. Use only the supplied evidence.\nFollow these skill instructions:\n'+skill},{'role':'user','content':case['prompt']}]}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response:r=json.load(response)
 record={'case_id':case['id'],'variant':'current-0.3.7','source_revision':source,'input_sha256':case['input_sha256'],'plan_sha256':sha(plan_path.read_bytes()),'request_sha256':sha(json.dumps(request,sort_keys=True).encode()),'model':r.get('model'),'done':r.get('done'),'done_reason':r.get('done_reason'),'response':r.get('message',{}).get('content'),'eval_count':r.get('eval_count'),'prompt_eval_count':r.get('prompt_eval_count'),'created_at':r.get('created_at')}
 (out/(case['id']+'__current-0.3.7.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
 print('COMPLETED',case['id'],record['done_reason'],flush=True)
