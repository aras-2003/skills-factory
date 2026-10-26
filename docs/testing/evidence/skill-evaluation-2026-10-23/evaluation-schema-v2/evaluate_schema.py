import pathlib,json,hashlib,urllib.request,random,re,datetime
root=pathlib.Path('/private/tmp/sf237-comparison-4b-20261023');out=root/'evaluation-schema-v2';out.mkdir(exist_ok=True)
repo=pathlib.Path('/Users/arkadiuszkamrowski/.codex/worktrees/eval237-comparison/skills-factory')
sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((root/'plan.json').read_text())
assert sha((root/'plan.json').read_bytes())==(root/'plan.sha256').read_text()
files=list(root.glob('*__*.json'));assert len(files)==9
system='You are an independent blind evaluator. Grade the provided anonymous final answers against each numbered rubric assertion. Quote short evidence. An answer fails if any assertion is not met. Do not rewrite or echo the inputs. Return ONLY the assessment required by the JSON schema. Never guess the answer identities.'
config={'model':'qwen3:4b','options':{'temperature':0,'seed':237,'num_predict':4096,'num_ctx':8192},'system':system,'executor_plan_sha256':sha((root/'plan.json').read_bytes()),'reason':'First evaluator returned input echo, invalid scoring output. Enforce scoring schema; criteria and executor outputs unchanged.','script_sha256':sha(pathlib.Path(__file__).read_bytes()),'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
p=out/'evaluation-plan.json'
if p.exists():raise SystemExit('Evaluation plan already exists; no implicit retry')
p.write_text(json.dumps(config,indent=2));print('EVALUATION_PLAN_FROZEN '+sha(p.read_bytes()),flush=True)
for case in plan['cases']:
 rubric=(repo/'evals/meta/skill-evaluation'/(case['id']+'.rubric.yaml')).read_bytes();assert sha(rubric)==case['rubric_sha256']
 assertions=re.findall(r'^    - (.+)$',rubric.decode(),re.M);assert assertions
 records=[(p,json.loads(p.read_text())) for p in sorted(files) if p.name.startswith(case['id']+'__')]
 random.Random('237:'+case['id']).shuffle(records);answers={};mapping={}
 for i,(p,r) in enumerate(records):
  assert r['done'] and r['done_reason']=='stop'
  label=chr(65+i);answers[label]=r['response'].rsplit('</think>',1)[-1].strip();mapping[label]={'file':p.name,'sha256':sha(p.read_bytes())}
 check={'type':'object','properties':{'assertion_index':{'type':'integer','minimum':1,'maximum':len(assertions)},'passed':{'type':'boolean'},'evidence':{'type':'string'}},'required':['assertion_index','passed','evidence'],'additionalProperties':False}
 answer={'type':'object','properties':{'assertion_checks':{'type':'array','items':check,'minItems':len(assertions),'maxItems':len(assertions)},'case_pass':{'type':'boolean'},'failure_summary':{'type':'string'}},'required':['assertion_checks','case_pass','failure_summary'],'additionalProperties':False}
 schema={'type':'object','properties':{'answers':{'type':'object','properties':{k:answer for k in answers},'required':list(answers),'additionalProperties':False}},'required':['answers'],'additionalProperties':False}
 payload={'task':case['prompt'],'numbered_rubric_assertions':{str(i+1):s for i,s in enumerate(assertions)},'anonymous_final_answers':answers}
 prompt='Grade ALL three anonymous answers against ALL numbered assertions. Do not repeat this input. Produce the assessment schema below.\nINPUT:\n'+json.dumps(payload,ensure_ascii=False)+'\nREQUIRED OUTPUT SCHEMA:\n'+json.dumps(schema)
 reqbody={'model':config['model'],'stream':False,'think':False,'format':schema,'options':config['options'],'messages':[{'role':'system','content':system},{'role':'user','content':prompt}]}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(reqbody).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response:result=json.load(response)
 raw=result.get('message',{}).get('content','');final=raw.rsplit('</think>',1)[-1].strip()
 record={'case':case['id'],'blind_mapping':mapping,'rubric_sha256':sha(rubric),'request_sha256':sha(json.dumps(reqbody,sort_keys=True).encode()),'model':result.get('model'),'done_reason':result.get('done_reason'),'raw_assessment_sha256':sha(raw.encode()),'assessment':final,'schema_validated':False}
 target=out/(case['id']+'.evaluation.json');assert not target.exists();target.write_text(json.dumps(record,ensure_ascii=False,indent=2))
 assessment=json.loads(final);assert result.get('done_reason')=='stop'
 assert set(assessment['answers'])==set(answers)
 for a in assessment['answers'].values():
  checks=a['assertion_checks'];assert sorted(x['assertion_index'] for x in checks)==list(range(1,len(assertions)+1))
  assert a['case_pass']==all(x['passed'] is True for x in checks)
 record['schema_validated']=True;target.write_text(json.dumps(record,ensure_ascii=False,indent=2))
 print('SCORED '+case['id']+' '+sha(target.read_bytes()),flush=True)
