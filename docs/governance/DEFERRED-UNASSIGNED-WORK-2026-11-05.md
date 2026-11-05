# Deferred unassigned work — 2026-11-05

## Decision and status semantics

At the owner's request, close the 15 issues that were open and had no native Project iteration on 2026-11-05. Close them with GitHub state reason `not_planned` and a per-issue comment explaining the specific deferral trigger.

**This is backlog deferral, not acceptance.** It does not mean the work was fully developed, tested, verified, or marked Done. Any unchecked acceptance criterion remains incomplete; historic failures and NOT_RUN rows remain evidence and must not be rewritten as passes. Reopen the relevant issue if the needed resource becomes available or the user asks to resume.

Issues in scope: #335, #360, #382, #383, #423, #425, #426, #464, #474, #483, #504, #505, #506, #526, and #556.

## Deferral register

| Issue | Work/evidence preserved | Reason to defer now | Reopen when |
| --- | --- | --- | --- |
| #335 | Layered local instrumentation and CI changes | Shared host correlation/Phoenix trajectory and full current-host red-team evidence are unavailable | A host-provided correlation trajectory and authorized full red-team run can be captured |
| #360 | Opportunity scoring source and deterministic checks | Historical calibration/backtest and source-backed comparability evidence are missing | Dated, comparable historical inputs and an allowed evaluation dataset are available |
| #382 | Systemic-risk signal and fail-closed source behavior | Historical vintages, market evidence, and cross-fund look-through needed for runtime acceptance are incomplete | Suitable dated source series and constituent evidence can be used for the pinned campaign |
| #383 | Replay engine; current unit tests pass 13/13 | Authentic pre-event archives, representative walk-forward history, and required execution receipt are missing | The source archives and allowed execution environment are supplied |
| #423 | `interface-design` source, tests, and current-Site observations; isolated host probes are recorded in PR #585 | Full frozen ordinary-Chat campaign, repetitions, sentinels, and exact runtime/source reconciliation are not complete | Resume the campaign with the exact current-Site ordinary-Chat fixture below and then complete every remaining frozen row |
| #425 | `implementation-brief`, `visual-regression-review`, and `accessibility-gate` contracts/tests; PASS/FAIL/NOT_RUN/BLOCKED boundaries | No approved target application/design was identified for real screenshot, keyboard, responsive, or visual-regression acceptance | An approved design and target application/runtime are identified |
| #426 | Selective experience-design routing contracts and partial Cloud Chat observations | Required verified routing receipts and portability across Chat-Mobile, Cloud, and Codex are incomplete | The required host surfaces and invocation-receipt evidence are available |
| #464 | Technical-structure engine and current unit tests pass 15/15 | Sourced historical instrument prices and out-of-sample evidence are missing | Reliable dated price histories for the required instruments and evaluation window are available |
| #474 | Placeholder-only correction and regression test; historical fabrication failure is preserved | A single corrected observation does not satisfy the repeated locked runtime retest | Complete the required pinned ordinary-Chat repeats and preserve the historic FAIL |
| #483 | Iteration 06 matrix and current evidence | The full locked matrix, critical-case repetitions, sentinels, unchanged probes, and final candidate reconciliation remain incomplete | Resume with the frozen campaign and record every required row on one verified candidate |
| #504 | Thin OpenSEO adapter, allowlist, mock/security tests, and CI | No connected OpenSEO account/API credential, actual bounded-cost operation, or external E2E evidence | A test account and explicit cost-bounded E2E environment are available |
| #505 | Local-only creative-generation candidate, runbook, license review, and tests | The inspected machine has 8 GB unified memory; supported local video E2E and measured workload cost/quality are unavailable | Supported local hardware is available for image and video runs and measurement |
| #506 | Source audit and disposition of the six named products | The unnamed product cannot be identified because its screenshot/source was not supplied | The screenshot or its source URL is provided |
| #526 | Screener design and existing implementation checks | Historical valuation/outcome data, benchmark comparison, and no-lookahead backtest evidence are unavailable | An authorized dated ranking/history dataset with benchmark outcomes is available |
| #556 | Deterministic caller-supplied look-through calculator and synthetic tests; no private portfolio details are included here | Real primary-source fund constituents and persistent product integration are not validated; the authorized read did not provide sufficient weights | Dated primary-source constituents and an approved integration path are available |

## User-run ordinary-Chat probe for #423/#474/#483

In a fresh ordinary Chat, select **Skills Factory Cloud Next** (if available) and send this frozen fixture verbatim, with no extra context:

> Design an account dashboard screen for a customer who needs to check a recent order and find the next action. Target responsive web on desktop and mobile. Use the existing product tokens and include loading, empty and error states. Return a design brief; do not implement it.

Return the Chat link and answer for evaluation. This one probe can add one current-candidate observation; it does **not** by itself complete the frozen matrix or make any of these issues Done. The required assistant opening sentence, navigation-boundary rule, unknown-data handling, states, responsive behavior, and accessibility assertions are defined in `skills/web-design/interface-design/tests/cases.yaml`.

## Evidence boundary

- PR #585 records seven blinded isolated host-agent checks for current Site packages. Those checks are not ordinary-Chat or Chat-Mobile runs; unsigned/incomplete per-call receipts do not establish cryptographic answer-to-load linkage.
- The current-Site direct-positive and onboarding observations, older failures, and NOT_OBSERVABLE rows remain as recorded in the Iteration 06 matrix.
- The #383/#464 unit tests and #556 synthetic fixtures prove only the tested deterministic code paths. They do not provide the missing historic datasets or live external data integration.
- No credentials, paid service calls, production writes, or private portfolio identifiers/values are included in this document.
