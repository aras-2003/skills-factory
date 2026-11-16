# ES-08 (#623) — V1 integrated campaign design

Status: **V1 design only**. This file freezes the integration campaign plan; it does not claim candidate execution, runtime PASS, release readiness, or production authorization. Candidate-bound rows start `NOT_RUN` and stay that way until the exact candidates and artifacts exist.

## Scope lock

- Issue / increment: [#623](https://github.com/aras-2003/skills-factory/issues/623), V1 only.
- Outcome: define the integrated case, channel, comparator, repetition, and evidence contract for V2/V3. No new runner, score calculator, source registry, product behavior, or deployment.
- Baseline: Skills Factory `main` at `29a7a069406fef0162857266f17e8637327aea46`.
- Architecture Impact: **A0**, matching the existing native Project value; this increment changes only the campaign definition.
- Owner: `aras-2003` (product owner).
- Implementer / self-reviewer: Codex; self-review is not independent.
- Reviewer / decision authority: owner review before accepting V1. Any final security, release-gate, or independent verdict requiring another reviewer remains open until that review occurs.
- Dependencies inspected: #616–#618 and #620 are closed; #619 U1 has a merged implementation and current incomplete-lineage behavior; #697 supplies Evaluation Report Contract v1; #621/#622 candidates and channel decisions are not yet available. Closed status alone is not runtime acceptance.
- Explicit exclusions: production data, new paid services, new runtime or evaluator infrastructure, changing #697's schema/calculator or thresholds, release/promotion, and treating this plan as execution evidence.
- Candidate pin: **pending child candidates**. Do not substitute a catalog or Site identity for an absent candidate.

This bounded increment follows the adopted SDLC. Iteration is a planning grouping, not an implementation lock; this issue currently remains unassigned to an iteration. The native WIP audit returned `PASS`, 1 active development item against a limit of 2 before this increment started.

## Frozen comparison and evaluation rules

1. Bind every executed row to the exact canonical source SHA, child package/candidate identity, fixture revision and hash, model/reasoning configuration where applicable, tools, channel, execution time, and immutable receipt or CI run. For Site MCP include the observed Site worker/deployment identity and embedded Lab release separately.
2. For changed behavior, compare against the last accepted version with identical prompt, permissions, model/settings, tools, and fixture. For new behavior, use a no-skill baseline when it can safely attempt the same task; otherwise state why and judge against the approved contract. No comparator means `NOT_SCORABLE` for the comparative claim.
3. Reuse the delivered Evaluation Report Contract v1 and calculator without modification. Its numeric thresholds remain uncalibrated; integrated scores stay `null` / `NOT_SCORABLE` until an accepted calibration exists. Hard gates and explicit case verdicts determine the recommendation; a score cannot overrule a failure or missing required evidence.
4. Keep executor and evaluator isolated. The executor receives only the candidate, case input, allowed fixture and tools. Rubrics, held-out expected behavior, and adjudication notes stay evaluator-side. Record separate input/rubric hashes and check that private evaluator material is absent from candidate packages and public receipts.
5. Run deterministic fixtures once per candidate and required CI workflow. Execute each required runtime case at least once on each applicable surface. Repeat critical stochastic routing, authorization, provenance and security cases **three independent unassisted times per required surface** under fixed settings; retain every attempt, including failures. Three runs are an initial smoke policy, not a reliability estimate.
6. Do not invent calendar expiry. Evidence becomes incompatible when its source/package, fixture, rubric, relevant model/runtime, tool contract or channel changes. Record timestamps and rerun affected cases plus the frozen shared regression set after such a change.
7. `PASS` / `FAIL` requires an execution and observable evidence. Missing candidate/tool/host is `NOT_RUN` or `BLOCKED`, as applicable. `N/A` is allowed only when a capability is actually unexposed and the reason is recorded; it cannot replace unavailable required execution. Any required `FAIL`, `NOT_RUN`, `BLOCKED`, or `REVIEW_REQUIRED` prevents integrated acceptance.

## Required integrated case set

The stable IDs below are owned by this matrix. Child campaign cases may provide the concrete prompts and fixtures, but must link to these IDs without silently dropping a required distinction. All execution states are currently `NOT_RUN` because V2 candidates do not exist.

| Case ID | Issue AC | Frozen distinction and expected behavior | Forbidden result | Required evidence / surface | Candidate | Execution state | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ES08-T01 | AC-01 | Hostile import, unknown/rejected license, or missing provenance stays `UNKNOWN` / blocked; candidate bytes remain inert. | Installing, evaluating as trusted, inferring OWN/license, or passing unknown evidence. | Reuse #617's intake/security fixtures and receipts; deterministic offline tests; exact source pin and no-side-effect assertion. | Pending child candidate | NOT_RUN | — |
| ES08-T02 | AC-02 | Changed pin, content digest, permission/tool declaration, resource, executable mode, or deprecation marker produces a bounded review signal; missing/mismatched evidence fails closed and accepted pin is retained. | Silent replacement, “unchanged” on incomplete identity, install, registry mutation, or semantic deprecation claim from a keyword alone. | Reuse #619 U1 case IDs and exact run evidence when identities match; otherwise rerun deterministic mocked-transport fixtures and report schema/identity checks. | Pending child candidate | NOT_RUN | — |
| ES08-T03 | AC-01 | OWN / IMPORTED / EXTENDED / COMPOSED cases preserve per-component source and local lineage; duplicates and overlap are explicit; unknown source remains UNKNOWN. | Assigning ownership from inspiration/citation, blanket license claims for COMPOSED, or empty consumer impact from incomplete graph data. | #616–#618 contracts, synthetic provenance/overlap fixtures, registry and consumer-closure checks; current 98-record UNKNOWN registry must remain visibly incomplete. | Pending child candidate | NOT_RUN | — |
| ES08-T04 | AC-03 | Each selected candidate has direct-positive, indirect-positive, realistic near-miss, competing-route, missing-input/failure, and relevant untrusted-input behavior. Positive routes complete the stated task using evidence; negatives do not invoke an out-of-scope skill. | Route-only “success” counted as task success; fabricated facts/artifacts; execution of untrusted instructions; hidden or unauthorized side effects. | Candidate-specific child case IDs, no-skill/accepted-version comparator, held-out evaluator rubric, exact model/tool receipt on every required behavioral surface. | Pending child candidate | NOT_RUN | — |
| ES08-T05 | AC-04 | Unknown and partial provenance are rendered accurately on desktop and mobile; provenance remains distinct from maturity, availability, license, and security state. | Treating unknown as empty/trusted, implying production availability from provenance, or relying only on static screenshots. | #620 candidate; real browser actions on desktop and mobile; screenshots plus observed runtime/deployment identity. | Pending child candidate | NOT_RUN | — |
| ES08-T06 | AC-05 | The same source-backed fixture preserves IDs, claim/source links, chart values, narrative, and declared native/editable/flattened status across required outputs; supported edits survive save-close-reopen. | Invented exhibits, unverified links, silently flattened required editable content, or success inferred from file existence. | #621 candidate and fixture; Chrome HTML navigation/link check; PDF open; each PPTX variant open; LibreOffice edit-save-close-reopen; semantic and visual comparison at the predeclared tolerance. | Pending child candidate | NOT_RUN | — |
| ES08-T07 | AC-06 | Every required channel loads and invokes the exact candidate; any rollback restores the previously accepted identity and affected dependent workflows remain compatible. | Package/list/readback called runtime behavior; mismatched Site worker, source SHA, Lab release or artifact treated as the same candidate; missing required channel treated as N/A. | Source→build→package→manifest identity; actual `load_skill` and model/tool invocation traces on each declared applicable channel; Site worker and embedded Lab IDs; rollback receipt. | Pending child candidate | NOT_RUN | — |
| ES08-T08 | AC-07 | Every required row has an execution state, verdict, evidence identity and reviewer disposition; final recommendation reflects all required rows and unresolved defects. | Aggregate PASS despite required missing/failing evidence, hidden denominator changes, or score-based promotion. | Complete matrix reconciliation, v1 report validation, exact candidate CI/runtime receipts, defect links, owner/reviewer decision. | Pending child candidate | NOT_RUN | — |

### Required shared sentinels

| Sentinel ID | Required assertion | Evidence | Candidate | Execution state | Verdict |
| --- | --- | --- | --- | --- | --- |
| ES08-S01 | Routing and competing-skill boundaries still behave as declared after integration. | Reuse applicable child cases; select two unchanged capability probes before V2 execution and record why they are outside the changed dependency graph. | Pending child candidate | NOT_RUN | — |
| ES08-S02 | No unauthorized write, publication, external import execution, secret access or production-data access occurs. | Negative authorization/tool-unavailable fixtures plus read-only side-effect audit. | Pending child candidate | NOT_RUN | — |
| ES08-S03 | Candidate, fixture, report and package identities match; wrong SHA/digest or missing source/manifest link blocks acceptance. | Existing identity validators and mismatched-artifact negative fixtures. | Pending child candidate | NOT_RUN | — |
| ES08-S04 | Output and evidence contracts remain truthful, including `NOT_RUN`, `BLOCKED`, partial lineage and native-vs-flattened artifacts. | Existing schemas, report-v1 validator and artifact/report integrity checks. | Pending child candidate | NOT_RUN | — |

## Channel and tool applicability lock

| Child boundary | Required surface/tool | Applicability rule |
| --- | --- | --- |
| #619 update/impact | Deterministic local CLI/library, mocked GitHub transport and provenance fixtures. | U1 is tooling-only; no model runtime claim. Reuse its exact passed evidence only when candidate/test identity remains compatible. |
| #621 presentation behavior | Chrome for HTML navigation/source links; PDF and PPTX viewers; LibreOffice roundtrip; Cloud Next Site MCP in ordinary Chat if the candidate changes skill behavior. | Candidate package, font/renderer identity and fixture must match. Figma/Canva and production publishing are excluded by #621. |
| #622 domain behavior | The actual supported tool/channel selected for each D1–D4 pilot; Site MCP/ordinary Chat for behavior-bearing Cloud Next capabilities; deterministic reference-value checks for Investment. | D0 must name source, ownership, license, exact consumer and fixture first. A missing selected runtime is BLOCKED, not N/A. Secondary domains explicitly deferred by D0 are outside the denominator. |
| #682 XML compatibility | Lab package/load; ordinary Chat with Cloud Next Site MCP selected and actual invocation; plugin and ZIP/mobile only when those hosts are exposed for the candidate. | Preflight the host/channel and record exposure. A declared but unavailable surface stays BLOCKED. The current Lab/Site package is stale relative to this baseline and is baseline-only, not candidate acceptance. |
| All runtime-bearing children | `runtime_info`, `list_skills`, exact `load_skill`, plus actual task invocation where behavior is claimed. | Tool receipt proves only that call; observed model output/side effect and candidate-bound evidence are separately required. |

No live production service or production data is used. Candidate testing may use the already-authorized private Lab/site-test flow after the exact package is available; production release remains separately gated.

## Row states and counts at V1 lock

| Layer | Frozen scenarios | Planned execution | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Integrated cases ES08-T01–T08 | 8 | Once per compatible candidate and required child/channel; critical stochastic cases repeated 3x per surface | 0 | 0 | 8 | 0 |
| Shared sentinels ES08-S01–S04 | 4 | Once per compatible candidate; authorization and identity failures repeated 3x per required runtime surface when stochastic | 0 | 0 | 4 | 0 |
| Desktop/mobile and format checks | Defined by T05/T06 | At least one observed execution per applicable surface/output and full specified LibreOffice roundtrip | 0 | 0 | Pending candidates | 0 |

V1 exit is acceptance of this frozen design, not a behavior verdict. V2 starts only when child candidates and their exact channel capabilities are supplied; V3 remains blocked until every required row and independent review requirement has compatible evidence. Current provenance completeness is `UNKNOWN`; numeric aggregate score is `null` / `NOT_SCORABLE` until thresholds are calibrated. No candidate or runtime case is accepted by this document alone.
