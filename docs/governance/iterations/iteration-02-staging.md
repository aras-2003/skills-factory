# Iteration 02 — staged development and acceptance register

**Status: STAGED / NOT ACTIVE / NOT MERGED.** Prepared on 2026-10-13 at user's explicit direction while Iteration 01 remains **not formally CLOSED**. This is a documented scheduling exception to [Iteration delivery](../ITERATION-DELIVERY.md), not a retroactive lock, not production approval, and not permission to change historical acceptance evidence.

- Baseline for initial PRs: `main@3554f12fbe2f0a51c00ce739f757e537ba7576d7`; do not assume this will remain the post-Iteration-01 final baseline.
- Two *draft*, unmerged implementation lanes: [#338](https://github.com/aras-2003/skills-factory/pull/338) runtime/registry/identity parity and [#339](https://github.com/aras-2003/skills-factory/pull/339) fault injection/chart hardening. **No pull request may merge to main until Iteration 01 closure, scope-lock decision, exact-head CI and explicit authorization.**
- Audit intake is all **18 historical Iteration 2 Issues**, across `02-runtime` and `02-runtime-followup`. Native Project Iteration items/status must be verified separately; this GitHub search/issue-text inventory is not Project V2 readback.
- Test manifest: [campaign.json](../../../evals/campaigns/iteration-02-runtime-2026-10/campaign.json), **18 synthetic cases and 34 planned runs**, plus 6 external/manual gate groups. **11 Lab cases** enter the executor-only artifact; **7 cases** (Site/browser/Desktop/Production) remain outside Lab until separately authorized and attested. No real execution evidence exists by generating this pack.

## Coverage and residual implementation

| Issue | Original intent | Source/development path | Required after PRs | Disposition |
| --- | --- | --- | --- | --- |
| [#149](https://github.com/aras-2003/skills-factory/issues/149) | Cloud MCP parity & chart | PR #338 (parity) + #339 (failure / chart); merged historical improvements | Approved Site/client smoke & deployment | PARTIAL |
| [#240](https://github.com/aras-2003/skills-factory/issues/240) | Local Desktop/browser runner | PR #338: isolated Lab-only adapter controller, optional one-command pinned-pack preparation, atomic evidence archiving and 14+ synthetic adapter integration/negative tests | Approved Desktop/Work executor, actual independent model/tool/OS-isolated receipts; Lab controller deliberately refuses Desktop channel | PARTIAL |
| [#242](https://github.com/aras-2003/skills-factory/issues/242) | Flow visibility | Generated catalog existing; PR #338 parity source audit | Installed/declared channel comparison & owner review | PARTIAL |
| [#243](https://github.com/aras-2003/skills-factory/issues/243) | AIS/RT historical gaps | Source/result inventory and planned I02 case | Per-finding historical→candidate exact-version disposition | NOT_RUN |
| [#247](https://github.com/aras-2003/skills-factory/issues/247) | Generated registry | Existing runtime-registry and catalog; PR #338 avoids duplicate registry | Catalog/package/live tool parity for all entries | PARTIAL |
| [#250](https://github.com/aras-2003/skills-factory/issues/250) | Runtime attestation | Existing MCP runtime_info + PR #338 cross-channel comparison | Installed exact candidate Work and Site observation | PARTIAL |
| [#251](https://github.com/aras-2003/skills-factory/issues/251) | Browser MCP E2E | Existing MCP fixtures and I02 browser slot; no simulated browser PASS | Fresh independent UI/tool/child traces | BLOCKED |
| [#252](https://github.com/aras-2003/skills-factory/issues/252) | Controlled failure paths | PR #339 simulated failures + actual MCP wrapper negative tests | TEST-only provider failure execution and receipts | PARTIAL |
| [#253](https://github.com/aras-2003/skills-factory/issues/253) | Work Lab ↔ Site parity | PR #338 exact source/manifest/schema/flow comparator | Actual Work + Site sessions on same candidate | PARTIAL |
| [#254](https://github.com/aras-2003/skills-factory/issues/254) | Bar/line client rendering | PR #339 Python renderer hardening and source tests | Real Chat screenshot + accessible chart values | PARTIAL |
| [#256](https://github.com/aras-2003/skills-factory/issues/256) | Nine R17 Lab failures | Historical R17 unchanged; I02 re-test definition | Nine identity-bound reruns, comparisons/independent eval | NOT_RUN |
| [#257](https://github.com/aras-2003/skills-factory/issues/257) | Production-only fallback | Explicitly external lane; not in Lab executor pack | Approved Production channel exact-version tests | BLOCKED |
| [#259](https://github.com/aras-2003/skills-factory/issues/259) | Site publication/regression | No publish triggered; I02 publication gate | Approved Site deployment/rollback and attested rerun | BLOCKED |
| [#286](https://github.com/aras-2003/skills-factory/issues/286) | All-skills lifecycle | Existing source lifecycle validator and historical 54-result | Exact-current 64+ scope and non-static quality evidence | PARTIAL |
| [#287](https://github.com/aras-2003/skills-factory/issues/287) | Per-domain routing semantics | I02 near-miss fixture; prior source router tests | Domain-by-domain independent model and tool traces | NOT_RUN |
| [#289](https://github.com/aras-2003/skills-factory/issues/289) | 54-skill behavioral campaign | Existing historical source audit, I02 coverage starter | Risk-based broad model campaign with observed receipts | BLOCKED |
| [#290](https://github.com/aras-2003/skills-factory/issues/290) | Workflow lifecycle | Existing validator; historical 16-workflow read | Exact-current 19-workflow audit and behavior receipts | PARTIAL |
| [#311](https://github.com/aras-2003/skills-factory/issues/311) | Campaign remediation | Prior R20/source work and immutable historical receipts | Source-locked reruns of affected FAIL/BLOCKED cases | BLOCKED |

`PARTIAL` means a real source/test increment exists but full acceptance is **not** established. `NOT_RUN` means missing real runtime evidence, not a PASS/FAIL. `BLOCKED` means a required tool, provider, permission, or independent trace is unavailable; it is not an instruction to deploy or bypass controls.

## Exact-revision TEST handoff envelopes

- Source CI builds a Lab executor-only pack with 11 Lab cases, locked prompts,
  prompt/rubric digest separation and release/source identity. Lab execution is NOT_RUN.
- The separate **iteration-02-external-handoff-<SOURCE_REVISION>** artifact contains
  seven synthetic input-only cases across Site, browser, Desktop and Production.
  No evaluator rubrics or provider credentials are sent; every external case
  is BLOCKED_PENDING_APPROVAL_AND_INSTALLED_IDENTITY. A generated prompt is
  **not** permission to invoke Production or a client.
- Source-only Site promotion/rollback preflight is at
  docs/testing/ITERATION-02-SITE-PROMOTION.md; it cannot publish or attest a deploy.
- This validation package can be used to plan the whole 18-case campaign;
  independent per-provider execution, traces, rubric assessment and human
  acceptance are *separate* prerequisites. Use PR #340 for combined source
  checks across PR #338 and PR #339. No merge to main has occurred.
## Development checkpoint — Desktop adapter controller and full source coverage

- #240: `iteration02_desktop_runner.py` now has a separate, approval-gated
  Desktop TEST adapter protocol using the seven-case **external** handoff;
  it validates fresh installed source/release/payload metadata, a pinned
  executable, exact Desktop scenario, controlled subprocess response and
  immutable receipt. Stub-subprocess tests demonstrate the controller,
  NOT an actual Desktop/Work model binding, sandbox or behavioral PASS.
  See `docs/testing/ITERATION-02-DESKTOP-RUNNER.md`.
- #286/#287/#289/#290: `iteration02_semantic_coverage.py` inventories all
  **64 current SKILL.md and 19 registered workflows** from the existing
  source lifecycle audits. The CI artifact lists observed fixture counts,
  missing negative/edge signals and missing local/central suites. It never
  replaces the 54-skill behavior campaign or its independent evaluator;
  all model verdicts are `NOT_RUN`.
- PR #340 remains the **combined integration/validation lane** for #338 +
  #339; `main` remains unchanged. A green CI run proves source compatibility
  and deterministic fixtures only, not user-visible/runtime acceptance.
## TEST acceptance sequence

1. Freeze the **prospective** issue/case scope and named owner/reviewer once Iteration 01 has been formally closed or explicitly ABORTED. Do not reconstruct a prior lock date.
2. Resolve exact main baseline drift. Rebase each draft branch; inspect merge conflicts and all dependency surfaces.
3. Run `Validate skills`, `Domain integrity`, and `Eval integrity` on each exact head; correct failures on the branch. The generated Iteration 2 pack is **source-only** and must include no evaluator rubrics.
4. After explicit permission to merge, run integrated main checks on the merged SHA and verify exact Lab package/release/payload.
5. Execute the **11 Lab cases** on the observed candidate in fresh unassisted sessions; hold rubrics with a different assessor and preserve per-case trace/source SHA and all fail/blocked outcomes.
6. Execute the **7 provider-specific cases** only in the intended approved, disposable/synthetic channel. Site, browser and client-visible chart evidence require real correlated provider/client observations. Production fallback cases require separate explicit authorization.
7. Reconcile R17/R18/R20 and the 2026-10-10 campaign without rewriting historical receipts. Re-run failed items only with comparable exact-revision inputs and independent evaluation.
8. Complete admin/source review and every original Issue's acceptance criteria; maintain linked PR relationships and statuses. Mark Done **only** after confirmed complete criteria. Production release/publishing remains a separate authorized action.

## Stop conditions

- Iteration 1 still open → keep PR #338/#339 draft and unmerged unless the owner explicitly changes iteration policy.
- No Work Lab/Site identical release digest → `MISMATCH/BLOCKED`, not parity PASS.
- No browser/client trace → chart `PAYLOAD_RENDERED` may be true but `CLIENT_RENDERED` is unverified.
- Model job queued, source CI PASS, synthetic injected failure, or QA ZIP generated → **not** a real execution receipt.
- No approved Site/Production permission or disposable TEST fixture → do not call live failure/deploy/write tools.

## Runtime receipt intake — evidence integrity

`scripts/eval/iteration02_result_intake.py` is a **read-only validator** of per-attempt receipts against the exact `lock.json` emitted by the campaign pack. It does not run the model, MCP, browser, publisher, or evaluator. It refuses duplicate attempt numbers, false PASS from queued/no-step jobs, stale release/prompt/rubric hashes, missing tool/output/evaluator receipts, assisted PASS and self-evaluation. Site/browser cases with mandatory chart evidence also require observed client display.

Run after a **separate, authorized executor** has submitted a JSON array of attempted executions (not during the source CI run):

```bash
python scripts/eval/iteration02_result_intake.py \
  --lock .tmp/iteration02-test-handoff/lock.json \
  --records .tmp/iteration02-results/observations.json \
  --output .tmp/iteration02-results/receipt-structure-review.json
```

The intake returns `NO_EXECUTION_RECEIPTS`, `INCOMPLETE`, `INVALID_RECEIPTS`, or `EVIDENCE_STRUCTURALLY_COMPLETE_REVIEW_REQUIRED`. Even the structurally complete state does **not** independently authenticate observation origins, evaluate rubric semantics, close manual gates or approve a release. Reviewer checks immutable raw outputs, real provider identity, tool-call traces, client-visible artifacts, input/rubric isolation and historical comparisons. Preserve results append-only, never overwrite pinned R17/R18/R20 evidence.

