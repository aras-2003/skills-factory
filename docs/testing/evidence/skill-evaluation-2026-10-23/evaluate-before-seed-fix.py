import json,hashlib,pathlib,urllib.request,random
root=pathlib.Path('/private/tmp/sf237-comparison-4b-20261023')
repo=pathlib.Path('/Users/arkadiuszkamrowski/Projects/skills-factory')
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((root/'plan.json').read_text())
if sha((root/'plan.json').read_bytes())!=(root/'plan.sha256').read_text():raise SystemExit('Plan drift')
files=list(root.glob('*__*.json'))
if len(files)!=9:raise SystemExit('Need exactly nine completed frozen responses')
for case in plan['cases']:
 rubric=(repo/'evals/meta/skill-evaluation'/(case['id']+'.rubric.yaml')).read_bytes()
 if sha(rubric)!=case['rubric_sha256']:raise SystemExit('Rubric drift')
 records=[(p,json.loads(p.read_text())) for p in sorted(files) if p.name.startswith(case['id']+'__')]
 random.Random(237+case['id']).shuffle(records)
 answers={};mapping={}
 for idx,(p,r) in enumerate(records):
  if r['done'] is not True or r['done_reason']!='stop':raise SystemExit('Incomplete response '+p.name)
  label=chr(65+idx);answers[label]=r['response'].rsplit('</think>',1)[-1].strip();mapping[label]={'file':p.name,'sha256':sha(p.read_bytes())}
 payload={'task':case['prompt'],'rubric':rubric.decode(),'anonymous_answers':answers}
 system='You are an independent evaluator. Evaluate each anonymous answer against EVERY manual assertion in the supplied frozen rubric. Do not infer missing claims. Quote short observed evidence for each judgment. Return JSON with answers mapping labels to assertion_checks (criterion, passed boolean, evidence), case_pass (all assertions passed), and failure_summary. Never reward fluent prose over adherence. Do not guess identities.'
 request={'model':'qwen3:4b','stream':False,'think':False,'format':'json','options':{'temperature':0,'seed':237,'num_predict':4096,'num_ctx':8192},'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response: result=json.load(response)
 target=root/(case['id']+'.evaluation.json')
 if target.exists():raise SystemExit('Refusing overwrite evaluator result')
 target.write_text(json.dumps({'case':case['id'],'blind_mapping':mapping,'rubric_sha256':sha(rubric),'request_sha256':sha(json.dumps(request,sort_keys=True).encode()),'model':result.get('model'),'done_reason':result.get('done_reason'),'raw_assessment_sha256':sha(result.get('message',{}).get('content','').encode()),'assessment':result.get('message',{}).get('content','').rsplit('</think>',1)[-1].strip()},ensure_ascii=False,indent=2))
 print('EVALUATED '+target.name+' '+sha(target.read_bytes()),flush=True)
