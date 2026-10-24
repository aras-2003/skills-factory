import subprocess,pathlib,json,os,time,datetime,hashlib
root=pathlib.Path('/private/tmp/sf237-comparison-4b-20261023')
procs=subprocess.run(['pgrep','-f','/private/tmp/sf237-comparison-4b-20261023/[r]un.py'],capture_output=True,text=True)
pids=[int(x) for x in procs.stdout.split()]
if len(pids)!=1:raise SystemExit('Expected exactly one verified live executor, found '+str(pids))
pid=pids[0]
state=root/'supervisor-status.json'
if state.exists():raise SystemExit('Supervisor already exists; refusing duplicate')
def save(status):state.write_text(json.dumps({'status':status,'executor_pid':pid,'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
save('waiting_for_live_executor')
print('WAITING_FOR_EXECUTOR_PID '+str(pid),flush=True)
while True:
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(5)
files=list(root.glob('*__*.json'))
if len(files)!=9:
 save('blocked_incomplete_executor_results');raise SystemExit('Executor terminal without nine results')
for p in files:
 r=json.loads(p.read_text())
 if r.get('done') is not True or r.get('done_reason')!='stop':
  save('blocked_incomplete_response');raise SystemExit('Incomplete response '+p.name)
save('running_blind_evaluator')
print('EXECUTOR_COMPLETE_STARTING_BLIND_EVALUATOR',flush=True)
result=subprocess.run(['python3',str(root/'evaluate.py')])
save('evaluation_complete_review_required' if result.returncode==0 else 'evaluation_failed_review_required')
raise SystemExit(result.returncode)
