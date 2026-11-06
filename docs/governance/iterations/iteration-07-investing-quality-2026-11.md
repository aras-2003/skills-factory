# Iteration 07 — investing quality, peer comparison and thesis challenge

- State: ACTIVE after the owner-directed abort of Iteration 06 on 2026-11-06. The abort and unresolved carry-forward are recorded in [the closeout record](iteration-06-closeout-2026-11-06.md) and GitHub #483 (closed as `not_planned`, not accepted). Iteration 06's historical scope and results remain unchanged.
- Tracking issues: [#306](https://github.com/aras-2003/skills-factory/issues/306), [#307](https://github.com/aras-2003/skills-factory/issues/307), [#318](https://github.com/aras-2003/skills-factory/issues/318), [#231](https://github.com/aras-2003/skills-factory/issues/231); umbrella [#322](https://github.com/aras-2003/skills-factory/issues/322) remains coordination-only under its explicit scope exclusion.
- Baseline GitHub main/source SHA: `25ec22b69df33c519f21182178ae8dfbbfebfeb7`.
- Baseline Cloud Next Lab: `1.38.461`, source `25ec22b69df33c519f21182178ae8dfbbfebfeb7`; verified Site attestation observed 2026-11-06. This is the pre-change runtime and is not candidate evidence.
- Owner: Arkadiusz Kamrowski.
- Reviewer: Arkadiusz Kamrowski (self-review; not independent).

## Frozen scope

### Included implementation slices

- **#318 Financial Quality Audit:** evolve existing `security-underwriting`; implement source/as-of and unit gates, comparable 3–5 FY plus comparable YTD input, revision history, transparent FCF/FCF conversion/ROIC/growth/debt/dilution outputs, deterioration and cycle flags, NOT_APPLICABLE industry paths, and no-write behavior. The existing `fundamental-intelligence` package remains a reference/calculation foundation, not a new skill.
- **#306 Peer comparison:** evolve existing `valuation-scenario-review`; implement explicit peer inclusion/exclusion, compatible metric basis/period/horizon, N/M and look-ahead/freshness handling, optional PEG only from compatible positive forward P/E and EPS growth, non-ranking P/S/growth heuristic and same-snapshot plot, and separate peer evidence from recommendation. No market-data ingestion, issuer claims or source snapshots are fabricated.
- **#307 Thesis challenge:** evolve existing `thesis-challenge`; surface up to three materially plausible objections, ranked by impact and evidence, with causal and valuation/downside transmission, disconfirming evidence, challenge state and explicit revised-thesis state. No forced bearish claims, trade or sell action.
- **#231 Investing domain audit:** inventory the in-scope Investing skills/workflows and versions against the baseline package/runtime; inspect routing and calculation contracts, evidence/freshness and write boundaries; record an evidence-based update plan and unresolved runtime acceptance separately. This review does not promote maturity.

### Explicit exclusions

- #322 is an umbrella explicitly marked planning-only, with no implementation or PR in that issue. Do not broaden this increment to #308/#309/#319/#320/#321 or #525/#526; reflect their dependencies only.
- No new Investing skill, parallel data store, schema/migration, automated data ingestion, live portfolio read/write, trade, policy change, production promotion, Site deployment or publication.
- Preserve frozen R17/R18 and prior campaign results. Use a new versioned candidate campaign for this work.

## Acceptance and evidence plan

1. #318: synthetic deterministic fixtures cover profitable software with negative OCF, cyclical semiconductor peak margins, USD-thousands/millions normalization, GAAP/adjusted plus SBC distinction, bank/ETF N/A path, missing/revised periods and future filings. Decision-critical failures block dependent metrics. Every accepted fact retains source URL, publication date, period, currency, unit and basis. No portfolio write.
2. #306: synthetic AMD-like, MU-like and incompatible business-model fixtures exercise 3–5 peer selection, explicit exclusions, method/period/definition/currency compatibility, forward horizon, outliers, revisions gaps, N/M, negative or stale EPS, and PEG formula/PEG=1 reference semantics. Charts and tables must use the same snapshot if a chart is produced. No BUY ranking or cross-sector score.
3. #307: cases cover a strong plausible countercase, only two supported challenges, no evidence, absent baseline thesis, priced-in distinction, and downside-transmission trace. State must follow evidence; no fabricated bear case or transaction action.
4. #231: exact source versions, available Cloud Next inventory, PL/EN and adjacent routing boundaries, one-security vs multi-position portfolio routing, calculations/missingness, freshness and write boundaries are documented with observed evidence and residuals.
5. Offline: focused unit suites; new-candidate campaign validation and evaluator isolation; investing/source validators; full repository CI-equivalent validation and package integrity. Run all tests only after the full scoped development is complete, then fix failures in batches and rerun the complete impacted set.
6. Runtime: candidate Site behavior requires an exact-source candidate Lab/Site identity and actual invocation receipts. Until such a candidate is available and explicitly published through the documented Sites workflow, runtime behavior remains NOT_RUN; no source-only or baseline-runtime PASS claim.

## Candidate history

- Scope lock created before implementation. Lock commit is recorded after commit creation.
- Scope-lock commit: `32f0bdaa9cb48206fe3e1ba6cbdc28f0705e65b6`; the Iteration 06 abort record was committed before Iteration 07 implementation resumed.
- Candidate development is committed on the GitHub PR branch at `47c96cefb83d2ef2d4a38f751b1bd121bd064149`. Helpers are packaged under existing security-underwriting and valuation-scenario-review directories; no new skill is registered. Production readiness now points to the candidate versions while retaining `lab-candidate-pending-runtime-validation` for all changed components.
- The unexecuted `investment-quality-2026-10` manifest had a stale valuation skill hash, and the unexecuted Iteration 02 workflow manifest had a stale security-review version. Both candidate manifests were synchronized without changing `NOT_RUN`, release approval, or frozen R20 history.

### Iteration 07 local validation — 2026-11-06

- Calculation regression suites: financial quality 18/18, peer comparison and same-snapshot plot 14/14, existing fundamental-intelligence 13/13.
- Campaign coverage and workflow-version gates: 12/12. Full evaluation suite: 308 tests passed, 2 skipped. Package tests: 102 passed; runtime MCP tests: 28 passed.
- Repository validation: `validate_all.py`, investing architecture, routing fixtures, campaign definition and evidence isolation, source/capability/security contracts, readiness registry, and catalog determinism passed. Nonblocking legacy source-contract warnings remain recorded by the repository validator.
- Domain, governance, output, unit-economics, readiness and release suites passed. Local promptfoo routing smoke passed 4/4. Lab, production, skills-only, remote and ChatGPT ZIP artifacts built and validated; the Lab artifact passed rubric-isolation checks. Repeated ZIP builds were byte-for-byte reproducible.
- Full candidate runtime execution is still **NOT_RUN**: the artifact was built locally, but no exact-source candidate Lab invocation receipt exists. Production readiness remains pending; no production release, Site publish, canonical write, maturity promotion or trade occurred.
- Issue disposition: #231 source audit and regression suite are complete; #306 remains open pending dated real-issuer AMD/MU and distinct-model evidence plus candidate runtime execution. #307 source contract and tests are implemented but runtime behavior is unverified. #318 deterministic calculations pass synthetic fixtures; real source-backed financial facts and candidate runtime behavior remain unverified. #322 remains planning-only.
- The Iteration 07 closure gate is not met until exact-candidate Lab behavior is exercised and the remaining issue-specific evidence is reviewed. Do not close #306, #307, or #318 on source-only evidence.

## Closure gate

Close only after every included issue acceptance criterion has evidence on one exact candidate, failures are repaired and re-run, #231's audit plan is complete, and unresolved runtime criteria are either passed or explicitly recorded as still blocking Done. The umbrella remains open while out-of-scope program issues remain. Any runtime/publishing or merge action follows repository authorization and the current Sites runbook.
