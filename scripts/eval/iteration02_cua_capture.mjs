// Host-side adapter for documented cua_repl Tab/App handles, not page JS.
// The operator selects the actual tab/app/provider before calling this module.
import { createHash } from 'node:crypto';
import { mkdir, writeFile, lstat } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';

const sha = value => createHash('sha256').update(value).digest('hex');
const hex = (value, length) => typeof value === 'string' && new RegExp(`^[0-9a-f]{${length}}$`).test(value);

export function verifyRequest(request, installed, approval) {
  if (approval?.approved !== true || typeof approval.reference !== 'string' || !approval.reference.trim() || !['browser', 'desktop', 'work'].includes(request.channel)) throw new Error('Explicit scoped host TEST approval required');
  if (request.environment !== 'TEST' || !/^I02-[0-9]{3}-[a-z0-9-]+$/.test(request.case_id) || !Number.isSafeInteger(request.attempt) || request.attempt < 1) throw new Error('Invalid frozen TEST case');
  if (typeof request.prompt !== 'string' || !request.prompt || Buffer.byteLength(request.prompt) > 256000 || sha(request.prompt) !== request.input_sha256) throw new Error('Frozen input digest mismatch');
  for (const [key, size] of [['source_revision', 40], ['payload_content_sha256', 64]]) {
    if (!hex(request[key], size) || installed[key] !== request[key]) throw new Error(`Installed ${key} mismatch`);
  }
  if (!request.release_id || installed.release_id !== request.release_id || installed.attestation_status !== 'verified') throw new Error('Installed release unavailable');
  // The caller must export an actually observed identity, never synthesize it.
  if (!installed.observation_source || !installed.observed_at || !Number.isFinite(Date.parse(installed.observed_at)) || !/(Z|[+-]\d\d:\d\d)$/.test(installed.observed_at)) throw new Error('Observed installed identity required');
  const age = Date.now() - Date.parse(installed.observed_at);
  if (age < 0 || age > 48 * 3600000) throw new Error('Installed observation stale');
}

export async function captureClient(target, channel) {
  if (channel === 'browser' || channel === 'work') {
    if (!target?.playwright?.domSnapshot || !target?.screenshot || !target?.url) throw new Error('Documented browser observation interface unavailable');
    return { accessible_text: await target.playwright.domSnapshot(), screenshot: await target.screenshot({fullPage:false}), client_reference: await target.url(), captured_at: new Date().toISOString() };
  }
  if (channel === 'desktop') {
    if (!target?.getAXState || !target?.getScreenshot) throw new Error('Documented native observation interface unavailable');
    return { accessible_text: await target.getAXState({emit:false,disableDiffing:true}), screenshot: await target.getScreenshot({emit:false}), client_reference: 'native-app-handle', captured_at: new Date().toISOString() };
  }
  throw new Error('Unsupported host channel');
}

export async function chatgptBrowserControls(target, {language='pl',timeoutMs=45000}={}) {
  const labels = language === 'pl'
    ? {input:'Zapytaj ChatGPT',answer:'ChatGPT powiedział:',copy:'Kopiuj',ready:'Odpowiedź jest gotowa'}
    : {input:'Ask anything',answer:'ChatGPT said:',copy:'Copy',ready:'Response is ready'};
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs<1 || timeoutMs>45000) throw new Error('Bounded completion timeout required');
  const main=target.playwright.getByRole('main');
  const answers=main.getByRole('heading',{name:labels.answer,exact:true});
  const baseline=await answers.count();
  const copies=await main.getByRole('button',{name:labels.copy,exact:true}).count();
  const input=target.playwright.getByRole('textbox',{name:labels.input,exact:true});
  if(await input.count()!==1) throw new Error('Observed ChatGPT prompt interface unavailable');
  return {input,observeCompletion:async()=>{
    const deadline=Date.now()+timeoutMs;
    while(Date.now()<deadline) {
      await target.playwright.domSnapshot();
      const statuses=await target.playwright.getByRole('status').allTextContents({timeoutMs:1000});
      if(await answers.count()>baseline && await main.getByRole('button',{name:labels.copy,exact:true}).count()>copies && statuses.some(x=>x.includes(labels.ready))) {
        const text=await main.innerText({timeoutMs:1000});
        const start=text.lastIndexOf(labels.answer);
        const response=text.slice(start+labels.answer.length).split('\n'+labels.copy)[0].trim();
        if(start>=0 && response) return {state:'complete',response};
      }
    }
    throw new Error('Completion unobserved before timeout; recover existing session, never resubmit automatically');
  }};
}

async function executeHostTest(target, request, installed, approval, controls) {
  verifyRequest(request, installed, approval);
  if (typeof controls?.observeCompletion !== 'function') throw new Error('Provider-specific observed completion check required');
  // Locators/AX indices must come from a fresh observed UI. No selector guessing,
  // external endpoints, credential reads, native shell input or hidden app APIs.
  const before = await captureClient(target, request.channel);
  if (request.channel === 'desktop') {
    if (!target.paste || !target.pressKey) throw new Error('Native input unavailable');
    await target.paste(request.prompt, {format:'text'});
    await target.pressKey('Return');
    await target.getAXState({emit:false});
  } else {
    if (!controls.input?.fill || !controls.input?.press) throw new Error('Fresh observed prompt locator required');
    await controls.input.fill(request.prompt);
    await controls.input.press('Enter');
    await target.playwright.domSnapshot();
  }
  const completion = await controls.observeCompletion(target);
  if (completion?.state !== 'complete' || typeof completion.response !== 'string' || !completion.response.trim()) throw new Error('Provider response not observed complete; do not resubmit');
  const after = await captureClient(target, request.channel);
  return {schema_version:'1.0', kind:'cua_host_capture', case_id:request.case_id, attempt:request.attempt, channel:request.channel, source_revision:request.source_revision, release_id:request.release_id, payload_content_sha256:request.payload_content_sha256, input_sha256:request.input_sha256, installed_observation_source:installed.observation_source, approval_reference:approval.reference, execution_state:'executed', response:completion.response, steps:[{tool:'cua_host_submission',status:'submitted'},{tool:'cua_client_observation',status:'captured'}], before, after, provider_authenticity:'REQUIRES_INDEPENDENT_REVIEW', client_display_state:'CAPTURED_NOT_VISUALLY_EVALUATED', model_behavior_verdict:'NOT_EVALUATED'};
}

async function safeRoot(root) {
  for (let p=resolve(root); ; p=dirname(p)) {
    try { if ((await lstat(p)).isSymbolicLink()) throw new Error('Symlink archive component'); }
    catch (e) { if(e.code !== 'ENOENT') throw e; }
    if(dirname(p)===p) break;
  }
}

export async function executeAndArchive(root,target,request,installed,approval,controls) {
  verifyRequest(request,installed,approval);
  await safeRoot(root);
  const dir=resolve(root,request.case_id,String(request.attempt).padStart(3,'0'));
  await safeRoot(dir);
  await mkdir(dirname(dir),{recursive:true,mode:0o700});
  await mkdir(dir,{mode:0o700}); // reserve BEFORE submission; existing = no retry
  try {
    const record=await executeHostTest(target,request,installed,approval,controls);
    return await archiveCapture(root,record,dir);
  } catch(e) {
    await writeFile(resolve(dir,'blocked.json'),JSON.stringify({case_id:request.case_id,attempt:request.attempt,status:'BLOCKED_CAPTURE_NO_AUTOMATIC_RETRY',failure:e.message})+'\n',{flag:'wx',mode:0o600});
    throw e;
  }
}

export async function archiveCapture(root, record, reservedDirectory) {
  // Atomic new directory reserves the attempt. A crash never triggers a retry.
  if (!/^I02-[0-9]{3}-[a-z0-9-]+$/.test(record.case_id) || !Number.isSafeInteger(record.attempt) || record.attempt < 1) throw new Error('Invalid archive identity');
  const dir = resolve(root, record.case_id, String(record.attempt).padStart(3,'0'));
  await safeRoot(dir);
  if (reservedDirectory !== dir) {
    await mkdir(resolve(root, record.case_id), {recursive:true,mode:0o700});
    await mkdir(dir, {mode:0o700});
  }
  const artifacts = {};
  for (const stage of ['before','after']) {
    const capture = record[stage];
    if (!(capture?.screenshot instanceof Uint8Array) || !capture.screenshot.length) throw new Error('Raw screenshot required');
    const png = Buffer.from(capture.screenshot).subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
    const jpeg = capture.screenshot[0] === 255 && capture.screenshot[1] === 216;
    if (!png && !jpeg) throw new Error('Unsupported screenshot bytes');
    const imageName = `${stage}.${png?'png':'jpg'}`, textName = `${stage}.txt`;
    await writeFile(resolve(dir,imageName),capture.screenshot,{flag:'wx',mode:0o600});
    await writeFile(resolve(dir,textName),capture.accessible_text,{flag:'wx',mode:0o600});
    artifacts[stage] = {screenshot_path:imageName,screenshot_sha256:sha(capture.screenshot),accessible_path:textName,accessible_sha256:sha(capture.accessible_text),captured_at:capture.captured_at,client_reference:capture.client_reference};
  }
  const {before,after,...metadata}=record;
  const saved={...metadata,artifacts};
  await writeFile(resolve(dir,'capture.json'),JSON.stringify(saved,null,2)+'\n',{flag:'wx',mode:0o600});
  return {directory:dir,record:saved};
}
