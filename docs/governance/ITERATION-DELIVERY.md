# Iteration delivery and quality gates

Status: operating policy submitted for review on 2026-10-12. Merge of this document adopts the policy; it does not start an iteration, authorize a merge/deployment, or prove runtime acceptance.

## Purpose and boundaries

Deliver one coherent increment at a time: freeze scope, develop on short-lived branches, integrate after offline checks, test the complete candidate in runtime, close with evidence, then start the next increment. `main` is an offline-verified integration line; `production` remains a separately authorized runtime snapshot. A green PR is not a closed iteration.

This policy refines [Development and release model](../DEVELOPMENT-RELEASE-MODEL.md) and [Testing](../TESTING.md). It governs delivery; the historical backlog and existing campaign receipts remain immutable provenance.

## What exists and what is missing

Inspection baseline: main `46a2f0e4157feb3b4e4db5c00b6959e4e57bb6cb`.

| Existing mechanism | Boundary / required refinement |
| --- | --- |
| Validate skills and Domain integrity on PRs | Offline validation and synthetic/unit tests; no external runtime execution. |
| Package candidate skill lab on main push | Exact-SHA Lab artifact, retained 90 days. Not an iteration acceptance verdict. |
| Eval isolation, campaign lock, smoke, receipts and promotion validator | Reuse these; add an iteration-level acceptance matrix and final candidate identity. |
| Project metadata sync | Dedicated `Project status:` and metadata labels sync; native Iteration and iteration gates do not. |
| 30 native Project iterations and ticket packages | Scheduling queue, not 30 active commitments. Calendar “Current” is not permission to start. |
| Governance docs / PR template | Need explicit scope lock, one active increment, merge-vs-Done semantics and close decision. |

There is currently no repository-wide automated check enforcing one active iteration, immutable scope, or complete case coverage at closure. Until that enforcement is implemented, the owner and reviewer apply the records and gates below. Do not describe this documentation as an automated control.

## Iteration record and single-active rule

Maintain one versioned record per increment at `docs/governance/iterations/<id>.md`, created from [the template](templates/ITERATION-RECORD.md). The corresponding GitHub tracking Issue links this record and all included Issues. The record is the authoritative commitment; native Project Iteration is its scheduling mirror.

Lifecycle: `PLANNED → ACTIVE → VALIDATING → CLOSED`. `BLOCKED` retains the active slot. `ABORTED` is a terminal outcome without acceptance. At most one record may be ACTIVE, VALIDATING or BLOCKED across the repository. The owner is accountable for the lock, candidate and close decision; a named reviewer verifies the evidence. If one person holds both roles, record that explicitly; never claim independent review.

A date boundary does not start or close anything. No development, Ready-to-In-progress pull, or implementation PR for the next iteration until the active increment is CLOSED or formally ABORTED. Discovery that changes future scope also waits by default; backlog capture is allowed, but must not become parallel development.

### Start gate

Start only when the previous increment is terminal, dependencies are accepted, scope fits one outcome, owner/reviewer are named, required runtime surfaces/tools are available or have an explicit booking, and every acceptance criterion has a planned test. Split L/XL work into bounded S/M slices before locking. Tracking umbrellas are not additional implementation scope.

Record the baseline main SHA, fixed Issue list, explicit inclusions/exclusions, acceptance criteria, case IDs and applicability per surface. Commit this record before the first implementation PR. Record the lock commit SHA in the tracking Issue; that commit provides an immutable comparison point. Then mark ACTIVE and move only the first actionable work to Ready/In progress. Maximum implementation WIP is 2; validation uses one coordinated lane, not a second iteration.

### Scope changes

| State | Allowed |
| --- | --- |
| PLANNED | Add/remove/reprioritize work and update tests/dependencies before start. |
| ACTIVE / VALIDATING / BLOCKED | No new capability commitment or acceptance relaxation. Defect intake is always allowed, separately from frozen capability scope. Clarifications may make existing intent explicit, with a logged diff and reviewer confirmation. |
| CLOSED / ABORTED | No rewriting history; use a new record. |

Report every discovered defect to the current iteration, including pre-existing or cross-framework failures. Use the bug form and `bug` label; record discovery iteration, candidate identity, severity, reproduction and violated contract. New ideas use the improvement form and a PLANNED iteration. A missing desired capability is an idea unless it violates an existing accepted contract.

Triage before closure: defects blocking frozen acceptance or critical regressions are fixed within the current iteration. Unrelated minor defects may be deferred only with impact assessment, named owner/reviewer acceptance and linked future delivery work; retain discovery attribution in the current record. Reporting does not automatically make a defect blocking, and deferral does not mean fixed.

A defect preventing an existing frozen criterion is corrective work within the same iteration: link a new defect Issue to the frozen parent and criterion, without increasing committed capability. The defect may use the same native iteration, but is identified as corrective rather than a new commitment. Strengthening a test for that defect is allowed; deleting a failed case, changing its expected result to permit the failure, or marking a required surface N/A is not.

New requests go to a PLANNED increment. If necessary, create 3A with its own fixed scope and tests after 3 closes and before 4 starts. A blocker to 3's acceptance cannot be deferred to 3A to falsely close 3. If scope becomes infeasible, formally ABORT 3, retain partial evidence and map every unresolved criterion to replacement work before starting 3A. ABORTED is never PASS or Done.

## Branches and candidate identity

Use `iter-<id>/issue-<number>-<topic>` branches from current main. One scoped PR per slice; no long-lived iteration integration branch. Evidence-only closure PRs may use `iter-<id>/closure`. PRs link the locked record, parent Issue, criterion and change class (NEW/ROUTING/BEHAVIOR/RESOURCE/DOCS).

Before each merge, validate the PR against current base, inspect the complete diff and required check results, and obtain review plus explicit merge authorization under repository policy. Offline CI may permit main integration with runtime NOT_RUN explicitly recorded. Use “Refs #…” rather than auto-closing syntax for work whose runtime acceptance is pending.

After the final implementation merge, select the exact main SHA and its Lab artifact. Record source SHA, release ID, payload digest, Actions run/artifact URL, build checks and observed installation identity. The Lab packaging workflow alone does not establish post-merge Validate skills PASS; verify both. Domain integrity is PR/workflow_dispatch, not automatic main-push validation; dispatch against the candidate ref when combined changes require that gate, and record the resolved SHA.

Freeze behavior changes on main during validation. Evidence-only documentation may follow without changing the tested package; explicitly distinguish evidence commit from candidate source. Any changed behavior, packaging, tool contract, dependency, fixture or rubric creates a new candidate and invalidates affected verdicts. Preserve old runs, supersede them, and rerun the affected matrix plus shared smoke. If impact cannot be bounded, rerun the entire required iteration matrix. Never silently combine PASS from different packages/surfaces.

Security emergencies interrupt normal delivery: stop validation, record the incident, integrate the fix through review, then repin and revalidate the active iteration or formally abort it. They do not authorize concurrent iteration work or bypassed acceptance.

## Test strategy and evidence ledger

Use [the acceptance matrix](templates/ACCEPTANCE-MATRIX.md) as one ledger for the complete iteration. Every committed Issue and criterion has rows; shared smoke/regression rows are mandatory too. Evidence from a task PR is preliminary until compatibility with the final candidate is established. Record `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, `REVIEW_REQUIRED`, or reviewed `N/A` per row; never infer execution from structural validation.

| Layer | Required coverage / gate |
| --- | --- |
| PR offline | Existing required CI; deterministic unit/integration tests for changed helpers; static contracts, security/capabilities, packaging and rubric isolation; meaningful regression fixtures for discovered defects. |
| Final main offline | Candidate SHA's checks and build; verify combined increment, generated artifacts, packaging identity and complete matrix. |
| Runtime smoke | Independently observe installed package/version/source/payload; correct catalog/tool selection, actual invocation and returned evidence on every required surface. Copied lock values are not observation. |
| Runtime scoped | Every changed behavioral criterion: positive, missing-input/negative, edge/adversarial, adjacent routing and dependent workflow scenarios as applicable. Helpers also need their observable workflow integration. |
| Cross-framework regression | Fixed sentinel set for routing, authorization/side effects, evidence integrity, output/delivery and unrelated critical existing capability. Expand by changed dependency/call graph; do not run only modified skills. |
| Recovery | Failure becomes fixture; fix, rebuild candidate, rerun failed cases, impacted cases and shared smoke. Flaky required cases remain blocked until investigated. |

A documentation-only acceptance criterion can be closed offline after review and link/static checks. Runtime may be N/A only when its applicability and rationale were declared at scope lock and confirmed against the actual diff. An iteration changing any skill behavior cannot use this exception for those rows.

For each runtime row retain case/input/rubric hashes, execution time, candidate identity, model/reasoning, channel/surface, tool availability, actual output/trace and reviewer verdict. Keep executor inputs isolated from evaluator rubrics, following [the eval protocol](../../scripts/eval/README.md). An assisted run does not qualify as PASS. Rendering/tool output and visible client display are separate assertions; test the latter when required.

Archive receipts and artifacts to existing durable evidence storage before Actions retention expires (current Lab artifacts: 90 days; runtime packs: 14 days). Record URLs and digests. A vanished artifact or narrative summary cannot substitute for evidence needed to reproduce acceptance.

### Existing tooling to reuse

Run from the pinned checkout with the repository's locked development dependencies. These are offline tools, not runtime execution:

```bash
python scripts/eval/local_preflight.py --output .tmp/offline-eval-preflight.json
python scripts/eval/validate_isolation.py
python scripts/eval/campaign.py validate
python scripts/eval/campaign.py prepare --output .tmp/runtime-campaign
python scripts/eval/campaign.py validate-lock --lock .tmp/runtime-campaign/lock.json
python scripts/eval/campaign.py validate-evidence
```

The campaign CLI currently selects R20 in code; it does not select an arbitrary iteration or automatically cover its scope. Map required iteration rows to existing campaign cases; add a separately reviewed campaign when missing. Behavior-pin changes require a new campaign baseline through the existing protocol. Do not rewrite historical pins to make a new candidate appear covered. `validate-evidence` validates available records; it does not prove that every required row executed or passed. The matrix completeness review is a separate close gate.

## Kanban transitions

| Status | Evidence required / next action |
| --- | --- |
| Backlog | Not started; future iteration assignment alone changes nothing. |
| Discovery | Existing uncertainty being analyzed; no implied implementation. |
| Ready | Frozen active scope, dependencies satisfied, owner and test plan explicit. |
| In progress | Actual implementation underway; WIP ≤2. |
| In review | PR is ready for review with offline results. |
| Validation | Integrated on main; final candidate runtime/integration acceptance pending. |
| Done | Criterion accepted with final evidence, including required runtime; Issue closure and Project status agree. |

A merged runtime-bearing Issue stays open in Validation until its required rows pass. Individual Issues may reach Done while the iteration is still validating; shared regressions and unresolved rows still block the iteration. A discovered regression reopens the relevant Issue, removes current acceptance and keeps historical verdicts intact. Use one current `Project status:` marker and canonical metadata labels; verify the asynchronous workflow and actual Project field after changes. Native Iteration is separately maintained. A tracking Issue records iteration state; do not create a new Project column per iteration state.

## Failure severity and close decisions

Severity here describes observed impact, independently of backlog priority P0–P3.

| Failure | Decision |
| --- | --- |
| Critical: unauthorized writes, secret exposure, destructive effects, evidence fabrication, broken permission boundary | Stop execution; contain/revert affected changes, retain evidence, fix and revalidate. No closure or new iteration. Production action requires explicit authorization. |
| Major: frozen criterion fails, wrong routing/workflow, broken output, required surface unusable, regression in an existing critical path | Block closure; corrective PRs within the active scope, new candidate and retest. |
| Evidence gap: required NOT_RUN/BLOCKED/REVIEW_REQUIRED, identity mismatch, missing traces or inconsistent package revisions | Block closure even with no known functional failure. Restore environment/evidence; expiry/date does not waive it. |
| Minor outside committed acceptance and critical regressions | Closure only after documented impact, named owner/reviewer acceptance and linked future PLANNED work. This is not a PASS for the failed row. |
| Required flaky test | Block closure; quarantine does not satisfy acceptance. Diagnose test/runtime, preserve every attempt, rerun under declared conditions. |

No pass-rate threshold overrides a failed required criterion. Zero unresolved critical/major defects, zero required missing verdicts and complete final-candidate coverage are mandatory. Non-blocking findings must not affect the frozen outcome or shared critical regressions; explicitly list them in the close decision.

### Closure checklist

1. Compare committed scope with lock commit; account for every Issue/criterion and corrective defect, with no silent removals or additions.
2. Confirm exact final candidate, post-merge offline gates and required runtime smoke/scoped/shared regressions.
3. Verify matrix has no unaccepted required row and evidence is retrievable, unassisted and version/surface compatible.
4. Reconcile open PRs/branches, Issue status/closure, native Iteration and tracking record. No acceptance work remains hidden under an umbrella.
5. Record limitations/non-blocking findings, outcome, owner/reviewer, decision time and evidence links in closure PR and tracking Issue. Owner proposes CLOSED; reviewer accepts. A self-review is explicit, never simulated independence.
6. Only after the closure record is accepted, release the active slot and start the next PLANNED increment (or 3A). Review actual throughput and readiness before changing future scope/dates.

Production promotion remains separate: a closed iteration is eligible for a promotion proposal, not permission to merge production or publish Cloud. Main and Sites are separate sources; follow the existing publishing runbook for any explicitly requested deployment.

## Adoption and remaining enforcement work

Adopt through this PR; link this policy from #233 and relevant governance Issues. The current calendar iteration is not deemed started by this PR. Before the first implementation, create its record and test matrix and verify all other records are PLANNED/terminal.

Minimum manual process is usable immediately after adoption. Recommended next bounded governance increment: a deterministic validator for unique active state, locked-scope diff and matrix completeness, connected to PR CI; Project reconciliation with readback; durable evidence retention checks. Implement and test those controls separately, without replacing the existing campaign/promotion validators or expanding credentials implicitly. They are not delivered by this documentation change.

## Minimum test inventory and run counts

These are planning floors, not proof that a fixed count is sufficient. Cover every frozen criterion and critical failure mode; add cases when a minimum case cannot cover them. Count distinct scenarios separately from repeated executions. Reuse applicable cases by stable ID rather than duplicating them to meet quotas.

| Change / risk | Minimum inventory |
| --- | --- |
| New skill or materially changed behavior | 6 scenarios per changed skill: happy path, missing input, ambiguity, adjacent non-trigger, adversarial/edge, conflicting/stale evidence. If inapplicable, justify at lock and replace with a relevant risk case. |
| Routing change | 4 per changed trigger: explicit positive, indirect positive, adjacent negative, competing-skill conflict; include affected competitors. May overlap the 6 behavior cases if both assertions are evaluated. |
| Deterministic helper / resource | Per changed contract: normal, invalid input, boundary, error/fallback; plus one integration case per distinct affected consumer contract. Avoid implementation-mirroring tests. |
| Authorization / persistent writes / security | At least 4: authorized action, missing authorization, stale/wrong authorization, unavailable permission/tool. Add injection and partial-write/recovery cases when relevant. Zero unauthorized side effects. |
| Multi-skill workflow | At least 3 E2E scenarios per changed workflow: successful handoff, prerequisite/evidence failure, downstream failure/recovery; assert routing and stop conditions. |
| Defect | At least 1 reproducible regression per root cause plus affected-consumer coverage. Preserve real runtime failures; add deterministic reproducers only when faithful. |
| Shared final-candidate baseline | At least 5 cases: routing, authorization, evidence integrity, output/delivery, unchanged critical capability. Plus 1 identity/invocation smoke per required surface and 2 rotating non-impacted capability probes. |

Run configured deterministic suites once per PR revision and in the applicable final-main gates. Ordinary runtime scenarios execute at least once per required surface on the final candidate. Critical stochastic routing, authorization and evidence-integrity scenarios execute at least 3 independent unassisted times per required surface with fixed declared model/settings. Every run must pass; retain failures and investigate rather than retrying until green. Three runs are an initial risk policy, not a statistical reliability guarantee. Increase repetitions based on observed instability.

Name supported model/surface configurations at lock; do not multiply by every available model. Separate observations are needed where tools/rendering differ. Runtime N/A follows the applicability rules above.

Example: one changed skill on one required surface starts with 6 scoped + 5 shared + 1 smoke + 2 rotating probe scenarios = 14 distinct scenarios, plus consumer/risk cases and repetitions. A scenario may serve several criteria only with explicit assertion mapping. Record counts by layer/surface in the matrix; acceptance requires every required row passing, never a percentage threshold.

## Regression selection without executing the full runtime catalog

Run all existing configured offline CI suites on each PR. Select external runtime cases by impact; reducing runtime scope is not permission to skip configured offline jobs.

Before implementation record changed paths/contracts and their consumers. Inspect workflow references, routing/catalog registrations, helper imports, schemas, permissions, packaging and campaigns. Follow direct consumers and transitive E2E paths until an unchanged contract boundary is demonstrated. Text searches help discover dependencies but do not prove their absence. Include negative routing neighbors and shared-state interactions.

Runtime selection is the union of:

1. Changed acceptance scenarios and applicable previously failing cases.
2. Direct consumer contracts and transitive E2E paths across the changed boundary.
3. Competing/adjacent routing and impacted security/output/evidence cases.
4. Fixed shared sentinels and smoke on every required surface.
5. At least 2 unchanged, non-impacted capability probes per iteration, chosen before execution from a recorded rotation list. Cover registered domains over successive iterations; expand if the catalog outgrows the rotation.

Record included case IDs, exclusions, dependency evidence and reviewer rationale before execution. Unjustified omissions are coverage gaps. Keep shared sentinels stable across iterations; review changes against the previous set. Defect fixtures join the persistent regression inventory rather than disappearing with an iteration.

| Impact | Required runtime regression breadth |
| --- | --- |
| Isolated skill change with unchanged interfaces | Scoped cases, routing neighbors, actual consumers, sentinels and rotating probes. |
| Shared helper, output/evidence schema or workflow handoff | All dependent consumer contracts and E2E paths, sentinels and probes. |
| Global router/catalog, authorization/persistence, infrastructure, packaging/dependencies/runtime adapter | Full affected channel/domain baseline; full supported runtime baseline if consumers cannot be reliably enumerated. |
| Unknown impact, failure in an “unaffected” probe, multiple cross-domain failures | Stop bounded acceptance and expand to affected domains; full supported baseline if cause/boundary remains uncertain. |

Also run a full supported runtime baseline before production promotion changing behavior/runtime artifacts, and after every 4 closed behavior-bearing iterations if no full baseline ran during that interval. Log the last full-baseline candidate and interval. This is an initial risk policy to revisit with observed defects/cost; it is not existing automation. Full means all registered supported cases/surfaces across applicable campaigns, not R20 alone. Incomplete inventory blocks a full-coverage claim.

Scoped regression cannot prove absence of distant defects. Sentinels detect shared drift, rotating probes challenge dependency assumptions, and periodic/promotion baselines limit accumulated blind spots. Record residual risk at closure.

## CI/CD gate map

| Stage | Existing mechanism | Acceptance evidence |
| --- | --- | --- |
| PR offline | `validate-skills.yml` (`validate`), `domain-integrity.yml` (`domain`), path-filtered `eval-integrity.yml` | Green applicable jobs at exact PR revision; unit/static/security/packaging reports linked to matrix. A filtered job that did not run is not PASS. |
| Final main candidate | Main push Validate skills + `package-main-lab-plugin.yml`; Domain integrity dispatch when needed | Matching source SHA, run IDs, artifact/release ID and digest. Failed checks/build block runtime acceptance. |
| Runtime | Existing external executor and campaign lock/smoke/receipt tooling | Scoped/shared/full matrix executed on observed candidate, all attempts preserved, evaluator isolated. This is not currently an Actions runtime job. |
| Closure | Evidence-only PR and completeness review | Compatible receipts, execution counts, locked scope, defect triage, no blocking rows. Ordinary green CI does not grant CLOSED. |
| Production | `package-production.yml` and promotion validator | Existing provenance/runtime gates plus applicable full baseline; explicit merge/publish authorization. Sites publishing and observed deployed identity remain separate. |

Required integration follow-up: add a deterministic `iteration-integrity` PR gate checking one active record, frozen commitment, bug-vs-idea classification, criterion-to-case completeness and planned counts. Closure checking must reconcile executed rows, final identity, severity and linked receipts, without equating receipt schema validity with behavioral PASS. Import existing runtime receipts rather than creating a competing format. Missing required rows must fail closed; retain artifacts durably. Configure a required branch-rule context only after this job is implemented and observed working. No workflow, permissions or branch protection change is delivered by this documentation PR; these controls remain explicit manual gates meanwhile.
