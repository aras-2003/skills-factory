from pathlib import Path
import subprocess,json,hashlib,urllib.request,datetime
root=Path('/private/tmp/sf237-candidate036-20261023');prior=Path('/private/tmp/sf237-comparison-4b-20261023');repo=Path('/Users/arkadiuszkamrowski/.codex/worktrees/eval237-comparison/skills-factory')
sha=lambda b:hashlib.sha256(b).hexdigest();oldplan=json.loads((prior/'plan.json').read_text())
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo).decode().strip()
assert source.startswith('19d4edc6')
skill=subprocess.check_output(['git','show',source+':skills/meta/skill-evaluation/SKILL.md'],cwd=repo).decode()
comparators=[]
for p in sorted(prior.glob('*__*.json')):
 r=json.loads(p.read_text())
 if r['variant'] in ['no-skill','current-0.3.4']:
  assert r['done_reason']=='stop';comparators.append({'case':r['case_id'],'variant':'previous-0.3.4' if r['variant']=='current-0.3.4' else 'no-skill','original_file':p.name,'record_sha256':sha(p.read_bytes())})
assert len(comparators)==6
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=30) as response:tags=json.load(response)
identity=next(m for m in tags['models'] if m['name']=='qwen3:4b');assert identity['digest']=='359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7'
plan={'source_revision':source,'candidate_version':'0.3.6','instruction_sha256':sha(skill.encode()),'model':oldplan['model'],'model_identity':identity,'options':oldplan['options'],'cases':oldplan['cases'],'reused_comparators':comparators,'original_comparator_plan_sha256':sha((prior/'plan.json').read_bytes()),'repetitions':1,'rubric_access':False,'scope':'Source-pinned skill instructions executed by local model; not an installed Lab package or Site host test','decision_threshold':oldplan['decision_threshold'],'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
p=root/'plan.json'
if p.exists():raise SystemExit('Existing plan, refusing implicit retry')
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2));(root/'plan.sha256').write_text(sha(p.read_bytes()));(root/'instructions.md').write_text(skill)
print('PLAN_FROZEN '+sha(p.read_bytes())+' SOURCE '+source,flush=True)
for case in plan['cases']:
 system='Answer the user task concisely. You have no tools. Use only the supplied evidence.\nFollow these skill instructions:\n'+skill
 request={'model':plan['model'],'stream':False,'think':False,'options':plan['options'],'messages':[{'role':'system','content':system},{'role':'user','content':case['prompt']}]}
 req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(request).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=600) as response:result=json.load(response)
 record={'case_id':case['id'],'variant':'current-0.3.6','source_revision':source,'input_sha256':case['input_sha256'],'plan_sha256':sha(p.read_bytes()),'request_sha256':sha(json.dumps(request,sort_keys=True).encode()),'model':result.get('model'),'done':result.get('done'),'done_reason':result.get('done_reason'),'response':result.get('message',{}).get('content'),'eval_count':result.get('eval_count'),'prompt_eval_count':result.get('prompt_eval_count'),'created_at':result.get('created_at')}
 target=root/(case['id']+'__current-0.3.6.json');target.write_text(json.dumps(record,ensure_ascii=False,indent=2));print('ARCHIVED '+target.name+' '+sha(target.read_bytes()),flush=True)
