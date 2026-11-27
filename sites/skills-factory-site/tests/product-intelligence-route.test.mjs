import test from 'node:test';
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
register('./product-intelligence-loader.mjs', import.meta.url);
const RealDate = Date, realFetch = globalThis.fetch;
let now = RealDate.parse('2026-11-27T12:00:00Z');
class Clock extends RealDate { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } }
let serial = 0;
const issue = n => ({ id:n, number:n, title:`Issue ${n}`, html_url:`https://github.com/aras-2003/skills-factory/issues/${n}`, state:'open', state_reason:null, labels:[], created_at:'2026-11-26T12:00:00Z', closed_at:null, body:'SECRET' });
const pull = n => ({ id:n, number:n, title:`Pull ${n}`, html_url:`https://github.com/aras-2003/skills-factory/pull/${n}`, state:'closed', created_at:'2026-11-26T12:00:00Z', merged_at:'2026-11-27T10:00:00Z' });
function fixture() {
  const entries = new Map(), calls = [], cacheCalls = [], toolCalls = [];
  const cache = {
    async match(key) { cacheCalls.push(['match', key.url]); const item = entries.get(key.url); return item && item.expires > now ? item.response.clone() : undefined; },
    async put(key, response) { cacheCalls.push(['put', key.url]); const seconds = Number(response.headers.get('cache-control').match(/max-age=(\d+)/)[1]); entries.set(key.url, { expires: now + seconds * 1000, response:response.clone() }); },
  };
  globalThis.__pic = { user:{userId:'owner'}, source:{github_main_revision:'a'.repeat(40)}, env:{CF_VERSION_METADATA:{id:'release-a',tag:'tag-a'}}, callTool:async (...args) => { toolCalls.push(args); return args[0] === 'list_skills' ? {skills:[]} : {attestation_status:'verified'}; } };
  globalThis.caches = {default:cache}; globalThis.Date = Clock;
  globalThis.fetch = async input => { const u = new URL(input); const resource = u.pathname.endsWith('/issues') ? 'issues' : 'pulls'; const page = Number(u.searchParams.get('page')); calls.push([resource,page]); return fixture.handler(resource,page); };
  return { entries, calls, cacheCalls, toolCalls };
}
fixture.handler = async () => Response.json([]);
async function route() { return import(`${pathToFileURL(resolve('app/api/intelligence/route.ts')).href}?isolate=${serial++}`); }
async function get(module) { const response = await module.GET(new Request('https://site.test/api/intelligence')); return {response, body:await response.json()}; }
test.afterEach(() => { globalThis.Date = RealDate; globalThis.fetch = realFetch; delete globalThis.caches; delete globalThis.__pic; now = RealDate.parse('2026-11-27T12:00:00Z'); });
test('unauthenticated route rejects before reads and sets no-store', async () => {
  const {calls,entries,cacheCalls} = fixture(); globalThis.__pic.user = null;
  globalThis.__pic.callTool = () => { throw Error('unexpected call'); };
  const {response} = await get(await route());
  assert.equal(response.status,401); assert.equal(response.headers.get('cache-control'),'no-store, max-age=0');
  assert.equal(response.headers.get('x-content-type-options'),'nosniff'); assert.deepEqual(calls,[]); assert.deepEqual(cacheCalls,[]); assert.equal(entries.size,0);
});
test('partial 429 retains data until reset across cold isolates, while pulls refresh', async () => {
  const {calls,entries,toolCalls} = fixture(); const start = now, resetAt = start + 20*60_000;
  fixture.handler = async (resource,page) => resource === 'pulls' ? Response.json([pull(201)]) : page === 1 ? Response.json(Array.from({length:100},(_,i)=>issue(i+1))) : new Response('',{status:429,headers:{'x-ratelimit-reset':String(resetAt/1000)}});
  let result = await get(await route());
  assert.equal(result.response.status,200); assert.equal(result.response.headers.get('cache-control'),'no-store, max-age=0');
  assert.deepEqual(toolCalls.find(([name])=>name==='runtime_info')[2], {id:'release-a',tag:'tag-a',timestamp:undefined,source:'cloudflare_version_metadata'}); assert.ok(toolCalls.some(([name])=>name==='list_skills'));
  assert.equal(result.body.sources.github.issues.state,'PARTIAL'); assert.equal(result.body.sources.github.issues.count,100); assert.equal(result.body.sources.github.pulls.state,'VERIFIED');
  assert.equal(result.body.sources.github.issues.asOf,new RealDate(start).toISOString()); assert.equal(result.body.roadmap.length,100); assert.ok(!JSON.stringify(result.body).includes('SECRET'));
  assert.deepEqual(calls,[['issues',1],['pulls',1],['issues',2]]);
  assert.ok([...entries.entries()].some(([key,value])=>key.includes('resource=issues') && key.includes('layer=current') && value.expires===resetAt));
  now = start + 11*60_000; calls.length=0; result = await get(await route());
  assert.deepEqual(calls,[['pulls',1]]); assert.equal(result.body.sources.github.issues.asOf,new RealDate(start).toISOString()); assert.equal(result.body.sources.github.issues.count,100); assert.equal(result.body.sources.github.pulls.asOf,new RealDate(now).toISOString());
  now=resetAt; calls.length=0; fixture.handler = async resource => Response.json(resource === 'issues' ? [issue(101)] : [pull(202)]);
  result=await get(await route()); assert.ok(calls.some(([resource])=>resource==='issues')); assert.equal(result.body.sources.github.issues.state,'VERIFIED'); assert.equal(result.body.sources.github.issues.count,1);
});
test('verified LKG is source-specific and expires after 24 hours', async () => {
  fixture(); const start=now; fixture.handler=async resource=>Response.json(resource==='issues'?[issue(11)]:[pull(21)]);
  let result=await get(await route()); assert.equal(result.body.sources.github.issues.state,'VERIFIED');
  now=start+11*60_000; fixture.handler=async resource=>resource==='issues'?new Response('',{status:500}):Response.json([pull(22)]);
  result=await get(await route()); assert.equal(result.body.sources.github.issues.state,'STALE'); assert.equal(result.body.sources.github.issues.asOf,new RealDate(start).toISOString());
  assert.equal(result.body.roadmap[0].number,11); assert.equal(result.body.sources.github.pulls.state,'VERIFIED'); assert.equal(result.body.sources.github.pulls.asOf,new RealDate(now).toISOString()); assert.ok(result.body.events.some(e=>e.sourceId===22));
  now=start+24*60*60_000+1; result=await get(await route()); assert.equal(result.body.sources.github.issues.state,'UNAVAILABLE'); assert.equal(result.body.roadmap,null); assert.equal(result.body.sources.github.pulls.state,'VERIFIED');
});
test('partial collection is never promoted to verified LKG', async () => {
  fixture(); const start=now;
  fixture.handler=async (resource,page)=>resource==='pulls' ? Response.json([]) : page===1 ? Response.json(Array.from({length:100},(_,i)=>issue(i+1))) : new Response('',{status:500});
  let result=await get(await route()); assert.equal(result.body.sources.github.issues.state,'PARTIAL');
  now=start+11*60_000; fixture.handler=async resource=>resource==='issues'?new Response('',{status:500}):Response.json([]);
  result=await get(await route()); assert.equal(result.body.sources.github.issues.state,'UNAVAILABLE'); assert.equal(result.body.roadmap,null); assert.equal(result.body.sources.github.pulls.state,'VERIFIED');
});
test('cache identity isolates canonical source, tag and deployment independently', async () => {
  const {calls} = fixture(); fixture.handler=async resource=>Response.json(resource==='issues'?[issue(11)]:[pull(21)]);
  await get(await route()); assert.equal(calls.length,2); calls.length=0;
  await get(await route()); assert.equal(calls.length,0);
  globalThis.__pic.source.github_main_revision='b'.repeat(40); await get(await route()); assert.equal(calls.length,2); calls.length=0;
  globalThis.__pic.env.CF_VERSION_METADATA.tag='tag-b'; await get(await route()); assert.equal(calls.length,2); calls.length=0;
  globalThis.__pic.env.CF_VERSION_METADATA.id='release-b'; await get(await route()); assert.equal(calls.length,2);
});
