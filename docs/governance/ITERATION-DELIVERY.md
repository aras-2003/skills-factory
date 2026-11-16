# Iteration delivery and quality gates

Status: adopted; updated 2026-11-16 under owner-approved D1–D8. [SDLC operating process](SDLC-OPERATING-PROCESS.md) supersedes the global serial iteration rule and administrative expiry coupling. Historical acceptance requirements remain unchanged.

## Purpose and boundaries

Deliver bounded coherent packages: freeze scope, develop on short-lived branches, integrate after offline checks, test the complete candidate in runtime, close with evidence; independent work may proceed within the approved WIP limit. `main` is an offline-verified integration line; `production` remains a separately authorized runtime snapshot. A green PR is not a closed iteration.

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
| Governance docs / PR template | Existing scope and acceptance are preserved; adopted SDLC controls use bounded packages and merge-vs-Done semantics. |

The current automated controls and remaining manual boundaries are documented in
[SDLC operating process](SDLC-OPERATING-PROCESS.md). Do not describe a planning report
as runtime execution or a native Project transaction lock.

## Iteration records and bounded work

Keep existing versioned records and frozen acceptance for historical work. New task
scope and acceptance live in the Issue; link a versioned design only when architecture
or risk requires it. Do not create a duplicate record solely to obtain an active slot.
Iterations group planned work; they do not globally prohibit independent development.
Lifecycle labels PLANNED/ACTIVE/VALIDATING/CLOSED/ABORTED remain meaningful per record.
Blocked work records cause, owner and resumption condition and can be parked.

### Start gate

Use the native Ready stage only when outcome, scope, dependencies, owner, Architecture
Impact and acceptance-to-test mapping are explicit. Check actual dependency readiness,
not whether every other iteration is terminal. Split L/XL work into bounded packages.
Maximum development WIP is 2 across In progress and In review; one shared Lab candidate
is coordinated separately. Scope on a shared interface/migration requires integration
ordering. Project synchronization enforces the active-stage WIP check and readback;
manual Project edits require the same coordinator audit.

### Scope changes

| State | Allowed |
| --- | --- |
| PLANNED | Add/remove/reprioritize work and update tests/dependencies before start. |
| ACTIVE / VALIDATING / BLOCKED | No new capability commitment or acceptance relaxation. Defect intake is always allowed, separately from frozen capability scope. Clarifications may make existing intent explicit, with a logged diff and reviewer confirmation. |
| CLOSED / ABORTED | No rewriting history; use a new record. |

Report every discovered defect to the current iteration, including pre-existing or cross-framework failures. Use the bug form and `bug` label; record discovery iteration, candidate identity, severity, reproduction and violated contract. New ideas use the improvement form and a PLANNED iteration. A missing desired capability is an idea unless it violates an existing accepted contract.

Triage before closure: defects blocking frozen acceptance or critical regressions are fixed within the current iteration. Unrelated minor defects may be deferred only with impact assessment, named owner/reviewer acceptance and linked future delivery work; retain discovery attribution in the current record. Reporting does not automatically make a defect blocking, and deferral does not mean fixed.

A defect preventing an existing frozen criterion is corrective work within the same iteration: link a new defect Issue to the frozen parent and criterion, without increasing committed capability. The defect may use the same native iteration, but is identified as corrective rather than a new commitment. Strengthening a test for that defect is allowed; deleting a failed case, changing its expected result to permit the failure, or marking a required surface N/A is not.

New requests go to a PLANNED increment. If necessary, create a dependent corrective package with its own fixed scope and tests. A blocker to 3's acceptance cannot be deferred to 3A to falsely close 3. If scope becomes infeasible, formally ABORT 3, retain partial evidence and map every unresolved criterion to replacement work before claiming acceptance for replacement work. ABORTED is never PASS or Done.

## Branches and candidate identity

Use `iter-<id>/issue-<number>-<topic>` branches from current main. One scoped PR per slice; no long-lived iteration integration branch. Evidence-only closure PRs may use `iter-<id>/closure`. PRs link the parent Issue, any existing locked record, Architecture Impact, criterion and change class (NEW/ROUTING/BEHAVIOR/RESOURCE/DOCS).

Before each merge, validate the PR against current base, inspect the complete diff and required check results, and obtain review plus explicit merge authorization under repository policy. Offline CI may permit main integration with runtime NOT_RUN explicitly recorded. Use “Refs #…” rather than auto-closing syntax for work whose runtime acceptance is pending.

After the final implementation merge, select the exact main SHA and its Lab artifact. Record source SHA, release ID, payload digest, Actions run/artifact URL, build checks and observed installation identity. The Lab packaging workflow alone does not establish post-merge Validate skills PASS; verify both. Domain integrity runs on pull requests, explicit workflow_dispatch and main pushes; verify the completed check on the exact integrated main SHA and record the run URL. PR-head checks alone are not post-merge evidence.

Freeze the selected candidate during validation, not unrelated changes on main. Evidence-only documentation may follow without changing the tested package; explicitly distinguish evidence commit from candidate source. Any changed behavior, packaging, tool contract, dependency, fixture or rubric creates a new candidate and invalidates affected verdicts. Preserve old runs, supersede them, and rerun the affected matrix plus shared smoke. If impact cannot be bounded, rerun the entire required iteration matrix. Never silently combine PASS from different packages/surfaces.

Security emergencies interrupt normal delivery: stop validation, record the incident, integrate the fix through review, then repin and revalidate the active iteration or formally abort it. They do not authorize bypassed acceptance; independent safe work remains subject to the development WIP limit.

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

A documentation-only acceptance criterion can be closed offline after review and link/static checks. Runtime may be N/A only when its applicability and rationale were declared at scope lock and confirmed against the actual diff. An iteration changing any skill behavior cannot use this exception for those rows. Production deployment is not a prerequisite for Issue or iteration Done. A test that specifically requires production data or production-only behavior must be redesigned as a safe equivalent runtime test where possible; otherwise that criterion remains blocked and cannot be declared Done by skipping runtime.

### Runtime surface policy

For behavior delivered through Skills Factory Cloud Next, ordinary Chat with the **Site MCP** explicitly selected is the primary semantic acceptance surface. The test must invoke the actual MCP capability and evaluate the resulting host behavior against the scoped assertions; a tool receipt alone proves invocation, not completion of a skill/workflow or correctness of its answer. Bind the result to the observed Site deployment, canonical source revision, embedded package identity and receipt.

The installed Skills Factory Lab is a supplemental consistency check when available. Record its observed version, source and package integrity, and compare the same relevant behavior when practical. Lab may lag Site: an unavailable or older Lab does not invalidate otherwise complete Site MCP acceptance, and no parity claim may be made from unequal identities. Record meaningful differences as follow-up compatibility findings. Lab remains required when an Issue specifically accepts Lab installation/host behavior or explicitly makes Lab/Site parity part of its frozen acceptance; such a requirement cannot be waived after scope lock. This policy applies to future scope locks and does not retroactively alter a frozen iteration.

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
| Ready | Bounded scope, dependencies satisfied, owner, Architecture Impact and test plan explicit; capacity available. |
| In progress | Actual implementation underway; WIP ≤2. |
| In review | PR is ready for review with offline results. |
| Verification | Required runtime/integration acceptance is being performed on the final candidate; an evidence gap remains open. |
| Done | Acceptance criteria pass with final evidence, including required runtime tests on the primary surface selected by the scope. For Cloud Next behavior, that is the observed Site MCP in ordinary Chat; Lab is supplemental unless Lab-specific behavior or parity is explicitly in scope. Production deployment is not required. Issue closure and Project status agree. |

A merged runtime-bearing Issue stays open in Verification until its required rows pass. Individual Issues may reach Done while the iteration is still validating; shared regressions and unresolved rows still block the iteration. A discovered regression reopens the relevant Issue, removes current acceptance and keeps historical verdicts intact. Production promotion/publication is a separate release decision and does not gate Done; source CI or a merge alone still cannot satisfy required runtime acceptance. Use one current `Project status:` marker and canonical metadata labels; verify the asynchronous workflow and actual Project field after changes. Native Iteration is separately maintained. A tracking Issue records iteration state; do not create a new Project column per iteration state.

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
6. Release this package after accepted closure; independent packages need not wait for it. Review actual throughput, dependencies and WIP before pulling more work.

Production promotion remains separate: a closed iteration is eligible for a promotion proposal, not permission to merge production or publish Cloud. Main and Sites are separate sources; follow the existing publishing runbook for any explicitly requested deployment.

## Adoption and enforcement

Follow the adopted [SDLC operating process](SDLC-OPERATING-PROCESS.md) for native task
states, bounded parallelism, architecture-informed test planning, derived evidence,
integration-vs-production readiness and five-change pilot. Existing complete-coverage,
security and production promotion requirements below remain applicable. Historical
campaign support is checked at its immutable pre-adoption anchor, not rewritten when
current administrative metadata changes.

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

During the SDLC pilot, run all configured offline CI suites on each PR. Select external runtime cases by Architecture Impact A0–A4, reviewed direct/transitive consumers, risk and channel. Reducing runtime scope is not permission to skip configured offline jobs.

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
| PR offline | `ci-validate.yml` (`validate`), `ci-domain-integrity.yml` (`domain`), path-filtered `ci-eval-integrity.yml` | Green applicable jobs at exact PR revision; unit/static/security/packaging reports linked to matrix. A filtered job that did not run is not PASS. |
| Final main candidate | Main push Validate skills + `release-lab-plugin.yml`; Domain integrity dispatch when needed | Matching source SHA, run IDs, artifact/release ID and digest. Failed checks/build block runtime acceptance. |
| Runtime | Existing external executor and campaign lock/smoke/receipt tooling | Scoped/shared/full matrix executed on observed candidate, all attempts preserved, evaluator isolated. This is not currently an Actions runtime job. |
| Closure | Evidence-only PR and completeness review | Compatible receipts, execution counts, locked scope, defect triage, no blocking rows. Ordinary green CI does not grant CLOSED. |
| Production | `release-production-plugin.yml` and promotion validator | Existing provenance/runtime gates plus applicable full baseline; explicit merge/publish authorization. Sites publishing and observed deployed identity remain separate. |

Enforcement boundary: the approved SDLC controls audit native WIP and Project writes,
validate architecture-informed plans, preserve historical support pins and separate
integration integrity from production eligibility. Runtime completeness, architectural
approval, Lab-lane coordination and independent review remain explicit acceptance work;
a generated index or green CI does not implement those observations automatically.
