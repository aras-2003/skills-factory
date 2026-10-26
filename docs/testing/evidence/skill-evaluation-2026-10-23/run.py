import json,hashlib,pathlib,subprocess,urllib.request,datetime
root=pathlib.Path('/private/tmp/sf237-comparison-4b-20261023')
repo=pathlib.Path('/Users/arkadiuszkamrowski/Projects/skills-factory')
sha=lambda b:hashlib.sha256(b).hexdigest()
current=pathlib.Path('/Users/arkadiuszkamrowski/.codex/plugins/cache/skills-factory/skills-factory-lab/1.38.320/skills/skill-evaluation/SKILL.md').read_text()
previous=subprocess.check_output(['git','show','74922af7^:skills/meta/skill-evaluation/SKILL.md'],cwd=repo).decode()
revision=subprocess.check_output(['git','rev-parse','74922af7^'],cwd=repo).decode().strip()
cases=[]
for p in sorted((repo/'evals/meta/skill-evaluation').glob('*.input.md')):
 rubric=p.with_name(p.name.replace('.input.md','.rubric.yaml'))
 cases.append({'id':p.name.replace('.input.md',''),'prompt':p.read_text(),'input_sha256':sha(p.read_bytes()),'rubric_sha256':sha(rubric.read_bytes())})
variants={'no-skill':'','previous-0.3.3':previous,'current-0.3.4':current}
options={'temperature':0,'seed':237,'num_predict':2048,'num_ctx':8192}
plan={'ticket':237,'model':'qwen3:4b','expected_model_id':'359d7dd4bcda','surface':'local Ollama tool-free synthetic text evaluation','candidate_release':'1.38.320+111b10aa89d5','previous_revision':revision,'previous_status':'historical draft, not accepted production comparator','variants':{k:sha(v.encode()) for k,v in variants.items()},'cases':cases,'options':options,'repetitions':1,'executor_rubric_access':False,'evaluator':'separate fresh tool-free model sessions after outputs frozen; blind variant labels','decision_threshold':'all frozen rubric assertions required for case PASS; report baseline delta, no material regressions; no benefit implies ITERATE, not automatic promotion','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
plan_path=root/'plan.json'
if plan_path.exists():raise SystemExit('Existing plan; refusing overwrite/restart')
plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2))
(root/'plan.sha256').write_text(sha(plan_path.read_bytes()))
print('PLAN_FROZEN '+sha(plan_path.read_bytes()),flush=True)
for case in cases:
 for variant,skill in variants.items():
  system='Answer the user task concisely. You have no tools. Use only the supplied evidence.'
  if skill:system+='\nFollow these skill instructions:\n'+skill
  request={'model':'qwen3:4b','stream':False,'think':False,'options':options,'messages':[{'role':'system','content':system},{'role':'user','content':case['prompt']}]}
  target=root/(case['id']+'__'+variant+'.json')
  req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=600) as response:result=json.load(response)
  record={'case_id':case['id'],'variant':variant,'input_sha256':case['input_sha256'],'plan_sha256':sha(plan_path.read_bytes()),'request_sha256':sha(json.dumps(request,sort_keys=True).encode()),'model':result.get('model'),'done':result.get('done'),'done_reason':result.get('done_reason'),'response':result.get('message',{}).get('content'),'eval_count':result.get('eval_count'),'prompt_eval_count':result.get('prompt_eval_count'),'created_at':result.get('created_at')}
  target.write_text(json.dumps(record,ensure_ascii=False,indent=2))
  print('ARCHIVED '+target.name+' '+sha(target.read_bytes()),flush=True)
