from pathlib import Path
import hashlib,json,urllib.request,re,random,datetime
root=Path('/private/tmp/sf237-candidate036-20261023');out=root/'evaluation-8b';out.mkdir(exist_ok=True)
repo=Path('/Users/arkadiuszkamrowski/.codex/worktrees/eval237-comparison/skills-factory');prior=repo/'docs/testing/evidence/skill-evaluation-2026-10-23/responses';sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((root/'plan.json').read_text())
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=30) as r:tags=json.load(r)
identity=next(m for m in tags['models'] if m['name']=='qwen3:8b')
system='Evaluate each anonymous final answer against every supplied numbered assertion using only explicit final-answer evidence. Treat missing required information as false. Quote a short supporting or conflicting final-answer excerpt for each assessment; do not invent evidence. Do not repeat task/rubric as your answer. Do not infer identity or version. Return only the JSON schema assessment. You have no tools.'
config={'model':'qwen3:8b','model_identity':identity,'system':system,'options':{'temperature':0,'seed':237,'num_ctx':4096,'num_predict':3072},'executor_plan_sha256':sha((root/'plan.json').read_bytes()),'aggregate':'computed deterministically from assertion checks, not model-declared','reason':'Earlier 4B scorers invalid. Different evaluator model, no redundant aggregate field; all original assertions preserved. This is a separately frozen evaluation attempt, not a retry of executor outputs.','script_sha256':sha(Path(__file__).read_bytes()),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
f=out/'plan.json'
if f.exists():raise SystemExit('Existing evaluator plan; refuse implicit retry')
f.write_text(json.dumps(config,indent=2));print('EVALUATOR_PLAN_FROZEN '+sha(f.read_bytes()),flush=True)
for case in plan['cases']:
 rubric=(repo/'evals/meta/skill-evaluation'/(case['id']+'.rubric.yaml')).read_bytes();assert sha(rubric)==case['rubric_sha256'];assertions=re.findall(r'^    - (.+)$',rubric.decode(),re.M)
 records=[]
 for v in ['no-skill','current-0.3.4']:
  p=prior/(case['id']+'__'+v+'.json');r=json.loads(p.read_text());records.append((p,r['response_final']))
 p=root/(case['id']+'__current-0.3.6.json');r=json.loads(p.read_text());assert r['done_reason']=='stop';records.append((p,r['response'].rsplit('</think>',1)[-1].strip()))
 random.Random('036:'+case['id']).shuffle(records);answers={chr(65+i):v for i,(_,v) in enumerate(records)};mapping={chr(65+i):{'file':p.name,'original_record_sha256':sha(p.read_bytes())} for i,(p,_) in enumerate(records)}
 check={'type':'object','properties':{'assertion_index':{'type':'integer','minimum':1,'maximum':len(assertions)},'passed':{'type':'boolean'},'evidence':{'type':'string'}},'required':['assertion_index','passed','evidence'],'additionalProperties':False}
 a={'type':'array','items':check,'minItems':len(assertions),'maxItems':len(assertions)};schema={'type':'object','properties':{k:a for k in answers},'required':list(answers),'additionalProperties':False}
 prompt=json.dumps({'task':case['prompt'],'assertions':{str(i+1):v for i,v in enumerate(assertions)},'anonymous_final_answers':answers},ensure_ascii=False)
 request={'model':config['model'],'stream':False,'think':False,'format':schema,'options':config['options'],'messages':[{'role':'system','content':system},{'role':'user','content':prompt}]}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as res:result=json.load(res)
 raw=result.get('message',{}).get('content','');final=raw.rsplit('</think>',1)[-1].strip();rec={'case':case['id'],'blind_mapping':mapping,'rubric_sha256':sha(rubric),'request_sha256':sha(json.dumps(request,sort_keys=True).encode()),'done_reason':result.get('done_reason'),'raw_assessment_sha256':sha(raw.encode()),'assessment_final':final,'validated':False}
 p=out/(case['id']+'.json');p.write_text(json.dumps(rec,ensure_ascii=False,indent=2));assessment=json.loads(final);assert result.get('done_reason')=='stop';assert set(assessment)==set(answers)
 for checks in assessment.values():
  assert sorted(x['assertion_index'] for x in checks)==list(range(1,len(assertions)+1));assert all(isinstance(x['passed'],bool) and isinstance(x['evidence'],str) and x['evidence'].strip() for x in checks)
 rec['validated']=True;rec['case_pass']={k:all(c['passed'] for c in checks) for k,checks in assessment.items()};p.write_text(json.dumps(rec,ensure_ascii=False,indent=2));print('SCORED '+case['id']+' '+sha(p.read_bytes()),flush=True)
