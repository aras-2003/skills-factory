# Iteration 2 — Main merge, Site candidate, and runtime QA handoff

Status: **SOURCE CANDIDATE; NO MERGE OR SITE DEPLOYMENT PERFORMED**.

## 1. Source and dependency lock

- Integration PR: [#342](https://github.com/aras-2003/skills-factory/pull/342).
- Candidate merge baseline: `main@f88f7d2a898c1ef1baf44e5264c653697ed60b0c`.
- Merge commit at initial checkpoint: `835c561b61721797827f4075a03da624aed8fffe`.
- Source ancestor PRs: #338 (runtime/QA) and #339 (MCP/chart/errors),
  combined QA PR #340; their changes are represented in #342's tree.
- #342 is *ahead* of current main with no commits behind as checked by GitHub
  compare. Repeat exact compare immediately before merge; any new main commit
  invalidates this statement.
- #341 (already on main) changed Investment OS routing to load child workflow
  after routing. Candidate tree retains that change and adds identity guards.
- 18 original Issues have a **single source-owner PR link** (#338 or #339);
  #342 carries no duplicate `Closes #...` relations.

## 2. Merge preconditions (not equivalent to CI)

- [ ] On **exact final PR #342 HEAD**, Validate skills / Domain integrity /
  Eval integrity must all be PASS; any further change invalidates old CI.
- [ ] Confirm no conflicts, required domain review and all relevant open
  review comments addressed. Review original scoped PRs #338/#339 as needed.
- [ ] Repository owner/admin verifies `main` and `production` branch protection
  / rulesets and required approval count. Integration currently receives
  `HTTP 403 Resource not accessible by integration`: this is **UNVERIFIED**.
- [ ] Confirm compliance with Iteration 1 source-governance dependencies;
  source CI does not prove broader release/production acceptance.
- [ ] Merge #342 to `main` only after explicit approval. Do not merge #338,
  #339 or #340 separately afterwards; reconcile/close as superseded when
  their exact source changes are confirmed represented.

## 3. Lab release artifact after merge

`main` triggers `.github/workflows/package-main-lab-plugin.yml` for the
exact resulting commit. This workflow builds and uploads
`skills-factory-lab-<MAIN_MERGE_SHA>` with `release-manifest.json` and
`docs/lab-release.json` (90-day retention). Treat the **actual post-merge
main SHA** as the candidate identity, NOT #342's premerge SHA and NOT an
older Site/CI artifact. If the package workflow does not run or fails, STOP.

Verify from the artifact that all these refer to one build:
`channel: lab`, 40-hex `source_revision`, `release_id`,
64-hex `payload_content_sha256`, catalog/tool contract, skill/workflow count,
and expected source files. Compare observed source to exact main SHA.
Do not copy a stale tracked `docs/lab-release.json` as a new build proof.

## 4. Existing Site identity (read-only receipt; 2026-10-13)

Observed from Skills Factory Cloud Next MCP `runtime_info`:

- Site runtime code source/release: `83ba12a435cbc59455747cac9231381f3e9f7709`.
- Site embedded Lab: version **0.35.0**, source
  `f88f7d2a898c1ef1baf44e5264c653697ed60b0c`, catalog digest
  `57daeffba3021f276dc0ee65bc3f8852228235e36d272083e3cbc17d459613d7`.
- Embedded ZIP artifact SHA-256:
  `5ef6fafdc99133301b80ad116059ff4235ad78e2bb02cd816014c4d0c0f91783`.
- Site schema digest:
  `sha256:d0a9033873c4cce8a2644465091d71d77b71050a782b07f38faea4ecff87a798`.
- Site runtime reported `attestation_status: verified`, based on Site
  environment metadata; the tool receipt is **unsigned** and is not
  independent proof of deployment authenticity.
- Site `runtime_info` does **not** include prior decoded Lab
  `payload_content_sha256` or an immutable, independently retrievable
  rollback package reference. A ZIP artifact hash cannot replace the payload
  digest. **Site publisher preflight remains BLOCKED pending those receipts.**

## 5. Site version staging and rollback (no unattended publish)

GitHub and the private ChatGPT Site have separate source repositories.
Merging main does not deploy Site or refresh its embedded Lab. After exact
main artifact validation, use the native **Sites publisher** only through
the approved hosting workflow described in `docs/SITES-PUBLISHING.md`.
Required native methods include `get_site`, verified site credentials,
`save_version_and_deploy_private`, `get_deployment_status`, and
version/rollback lookup. Such publisher tools were **not exposed** to the
present ChatGPT tool environment; do not invent uploads, Git pushes or versions.

- [ ] Obtain authorized owner/publisher, current private version and a
  **retrievable immutable rollback package** for currently installed Lab.
- [ ] Capture the old Lab decoded payload digest and verify independent
  immutable ZIP hash against Site's installed artifact; preserve old Site
  version and source SHA separately.
- [ ] Build candidate Site source from **postmerge** Lab artifact; pin its
  digest and runtime code SHA. Confirm intended catalog and tool schema.
- [ ] Run offline read-only preflight:

```sh
python scripts/eval/iteration02_site_release_readiness.py \
  --candidate /path/to/new-lab/release-manifest.json \
  --site-runtime-info /path/to/fresh-verified-site-runtime-info.json \
  --rollback /path/to/immutable-prior-lab-rollback-manifest.json \
  --output /path/to/review/site-readiness.json
```

`BLOCKED_EVIDENCE` means STOP. `INPUTS_CONSISTENT_APPROVAL_REQUIRED`
proves input-field consistency **only**, not provider authenticity, deployment
authority, preview/client behavior, or release approval. This script never
publishes and never performs rollback.

- [ ] Use native publisher with explicitly scoped owner authorization;
  perform private/canary smoke first, collect Site version ID returned by
  service (never invent its number).
- [ ] Independently re-read Site MCP `runtime_info` and embedded Lab identity
  after publish. Verify tool schema/catalog, source SHA and complete artifact.
- [ ] If mismatch or regression, stop and revert via the approved native
  rollback. Independently verify the restored version and retain receipts.

## 6. Runtime testing sequence (after updated Site, not before)

1. Exact-source QA suite: 18 synthetic scenarios, 34 planned attempts,
   11 Lab and 7 separately gated Site/browser/Desktop/Production. Retrieve
   new postmerge packs; PR artifacts are useful rehearsal but NOT matching
   exact postmerge/main identity.
2. Dispatch Lab only with pinned TEST controller, separately authorized
   Desktop/browser/Site executors. Never run Production cases without
   explicit case-specific production authorization.
3. Collect execution tool traces and signed/source-identified receipts;
   inspect Browser/Chat client display, renderer data and actual screenshots.
   Source-level structural checks do not authenticate pixels or provenance.
4. Independently evaluate each case against isolated frozen rubrics,
   preserve prior append-only event history; never treat queued/no-steps
   executions or synthetic stubs as behavioral PASS.
5. R17 historical 36 PASS / 9 FAIL needs **nine actual exact-version retests**.
   #287/#289 broad semantic campaigns (64 skills, 19 workflows) also require
   their separate execution; the 18-case triage is not a substitute.
6. Record per-Issue acceptance; then and only then move Issues to Done.
   Site deployment and production promotion remain distinct approvals.

## Stop / rollback triggers

Any red CI on exact source; new intervening main commit; source/release/digest
mismatch; missing protected-branch admin evidence; unavailable publisher;
stale/absent immutable rollback; provider/site identity unverifiable;
zero-step runtime jobs; unapproved external writes; missing reviewer;
client chart or routing evidence missing. Do not mark VERIFIED by declaration.

**State of this document:** reproducible plan and handoff, not a record that
merge, Site staging, runtime test campaign, or rollback rehearsal occurred.
