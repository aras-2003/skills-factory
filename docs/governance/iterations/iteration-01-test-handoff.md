# Iteration 01 — test handoff and acceptance runbook

**Disposition: SOURCE-READY CANDIDATE / RUNTIME NOT_RUN / ITERATION NOT DONE.**

This is a new additive, synthetic acceptance overlay. It **does not modify** the frozen `runtime-validation-2026-10-r20` definition, rubrics, queues, receipts or historical Lab baselines. It does not retroactively claim the missing pre-PR scope-lock required by [Iteration delivery](../../governance/ITERATION-DELIVERY.md).

## Integrated source and provenance

- Integration sequence: [#333](https://github.com/aras-2003/skills-factory/pull/333) (SEC001/SEC010 scanner), [#334](https://github.com/aras-2003/skills-factory/pull/334) (fail-closed capability preflight), [#332](https://github.com/aras-2003/skills-factory/pull/332) (governance, backlog 90-ID map). Source integration to `main` is **not a closure verdict** for #245/#246/#249 or dependencies.
- **Canonical candidate identity** is the eventual **post-merge main** commit of this handoff branch, NOT the historical Site Lab 0.35.0 receipt and NOT a PR SHA. The GitHub Action job must report exact `source_revision`, `release_id`, `payload_content_sha256` and the committed campaign manifest SHA-256. Never copy them from an older artifact.
- The manifest [campaign.json](../../../evals/campaigns/iteration-01-safety-governance-2026-10/campaign.json) has **15 distinct synthetic model cases covering all 10 Issues**, with **8 critical cases × 3 repetitions** and **7 other single-run cases**: **31 planned model executions** across the one Lab surface. **None has been executed by this packaging workflow.** `execution_state=NOT_RUN` and `outcome=null` are mandatory until real traces and independent evaluation exist.
- An additional **7 manual gates** cover admin/Project/legal/runtime/TEST-store/final-candidate prerequisites. They remain NOT_RUN/BLOCKED; no false `N/A`.

## Generate reproducible handoff (offline)

On the exact, pinned candidate commit with locked dev dependencies installed:

```bash
python scripts/eval/iteration01_handoff.py validate
python -m unittest discover -s scripts/eval/tests -p 'test_iteration01_handoff.py'
python scripts/package/build_lab_plugin.py --output .tmp/iter01-lab
SOURCE_REVISION="$(git rev-parse HEAD)" python scripts/eval/iteration01_handoff.py prepare \
  --lab .tmp/iter01-lab --output .tmp/iteration01-test-handoff
python scripts/eval/validate_isolation.py --artifact .tmp/iteration01-test-handoff
```

The normal `Validate skills` Action also builds, validates and uploads this **executor-only** pack as `iteration-01-executor-handoff-<CI SHA>` (14-day retention). Archive a durable copy with SHA-256 evidence before the artifact expires. The pack contains the **full exact Lab**, `lock.json`, an input-only queue and per-case `.input.md` files. **It contains no evaluator assertions or `.rubric.yaml` files.** The assessor uses the matching manifest from repository source, *outside* the executor context, and binds each result to the rubric digest listed in the lock.

## Run sequence and evidence requirements

1. **Offline combination gate:** confirm the final `main` SHA after all merges; validate exact-main `Validate skills`, `Domain integrity` (automatic main-push workflow; verify the run's exact SHA), package, skill scan, capability preflight, 90-ID map, unit tests, isolation and manifest-digest binding. PR-head PASS is not combined-main PASS.
2. **Identity smoke:** load the **same** exact Lab candidate in a new isolated TEST session. Independently observe release ID, source SHA, payload digest, catalog/tool identity, provider/model/reasoning and available capabilities. Inability to observe identity means `NOT_RUN/BLOCKED`, not a passing assumption.
3. **Unassisted execution:** run each of the 15 executor prompts in a **fresh session without evaluator rubrics**. Repeat the eight critical stochastic cases three times; use different run IDs. Persist each input/trace/output hash, actual tool path, external reads/writes or their verified absence, latency, tool availability, client display evidence when applicable and timestamps.
4. **Independent evaluation:** reviewer reads assertions only from source at the frozen manifest SHA. Check all `must`, `must_not`, provenance and forbidden side effects; verify execution state separately from verdict. Never award PASS from a queued job, source CI or an unsigned narrative.
5. **Side-effect safety:** I01-MON-002 and I01-INV-002 require a newly authorized **disposable synthetic TEST-only store**, explicit per-case write authorization, denial run, canonical READ/WRITE receipts and idempotency evidence. No use of the existing real `investment-os` store, no production account, no fake receipts. Without this setup they are **BLOCKED** and must not be attempted.
6. **Cross-framework sentinels:** I01-SENT-001/002 detect unrelated routing, write and evidence regressions. Expand the shared matrix for impacted downstream workflows; the two sentinels are minimum smoke, not broad regression coverage.
7. **Manual gates:** Project V2 90/90/native Iteration readback (#160/#258), exact historical AIS/RT matching (#234), publisher/admin rules and rollback (#248), licensing/private reporting/review capacity (#249). Link observed evidence for each, otherwise leave BLOCKED.
8. **Decision:** update [acceptance matrix](../../governance/iterations/iteration-01-acceptance-matrix.md) against the **same final candidate**; preserve failed receipts and file corrective bugs. Owner and reviewer decide when all mandatory rows are actually accepted. Only then move Issues to Done and propose production promotion **as a separate authorized step**.

## Critical stop conditions

- **No verified test store or no approval:** do not make a write call.
- **Requested essential capability absent:** stop or explicitly report a limited alternative; never claim provider-backed execution.
- **Exact package mismatch, missing model trace, missing admin access, rubrics leaked to executor:** stop; label BLOCKED/NOT_RUN as applicable.
- **Partially merged / new source SHA:** invalidate prior matching verdicts and rebuild the test pack; do not mix versions.
- **Site/Cloud deployment is independent of `main`:** this handoff makes no claim that Cloud received the candidate.

## Coverage by ticket

| Issue | Included evidence work | Remaining required acceptance |
| --- | --- | --- |
| #160 | Historical map static gate, GOV-001, manual Project gate | Native Project 90/90 fields and overlap/cutover review |
| #233 | Closed planning artifact, SENT-001, manual governance gate | No invented retrospective scope lock |
| #234 | GOV-002, identity smoke gate | Exact current Lab/runtime + historical AIS/RT verification |
| #245 | SEC-001/002 + scanner unit/mutation suite | Full scanner/adversarial runtime evidence |
| #246 | CAP-001/002 + preflight tests | Observed vs declared contracts + live host preconditions |
| #248 | OPS-001 + admin/publisher manual gates | Branch protection 403, publisher isolation and rollback |
| #249 | GOV-003 + legal/secure-reporting manual gate | Owner license choice, private intake, review capacity |
| #258 | GOV-004 + Project/source audit gate | All competing backlog sources disposition |
| #291 | MON-001/002 | Isolated TEST authorization, denial and canonical receipts |
| #303 | INV-001/002 | Cross-workflow TEST-write/idempotency and denial receipts |

This campaign is a **test handoff**, not proof the complete implementation scope is finished. Remaining nonimplemented acceptance is retained in original Issues and their exact-version evidence ledger.
