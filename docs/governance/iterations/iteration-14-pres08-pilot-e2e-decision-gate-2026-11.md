# Iteration 14 — presentation pilot E2E and route decision (PRES-08)

- State: VALIDATED; scope locked by merged PR #654 (`cf6c183bd10e4821224a4a22d405b19c1b5e9d83`); all acceptance evidence passes, with evidence closeout publication and issue reconciliation pending.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #614 / No Iteration; leave unassigned unless separately changed after lock.
- Previous terminal iteration: Iteration 13 CLOSED / ACCEPTED, issue #613; implementation PR #651 and evidence PR #652 merged, governance closeout PR #653 merged as `565d814fed8c31504fefac58ed4752c2833b649e`.
- Baseline main SHA: `565d814fed8c31504fefac58ed4752c2833b649e`.
- Lock PR / commit SHA: PR #654; record its immutable head SHA here and in #614 before implementation.
- Started at / closed at (UTC): 2026-11-12T17:49:51Z / pending.
- Scope lock reviewed by / at: owner self-review / 2026-11-12; not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #614 | 614-A1–A9 | Run an evidence-bound 12-slide synthetic presentation pilot through the existing Marp HTML/PDF/flattened-PPTX/experimental-editable-PPTX routes and a native editable PPTX baseline. Compare repeatability, build time, content and visual fidelity, editability, notes, usability, security and maintenance burden. Produce a comparison report, slide screenshots/contact sheets and a route recommendation for executive, technical and training use cases. | New renderer or authoring adapter; Figma/Canva/Google Slides account/runtime work; real/customer data; network assets; Site/Cloud Next behavior, plugin release or production deployment; unsupported claims that editable implies faithful. | #608–#613 are closed; #613 closeout PR #653 is merged. Reuse its canonical 12-slide fixture, route implementation, cross-format evidence, exact-candidate edit receipt and shared regression sentinels. | M |

## Design and ownership boundary

The pilot input is the exact 12-slide synthetic fixture `adapters/presentation-marp/fixtures/pres07-cross-format-v1.json` (SHA-256 `fedb33a0fa2d62c59641d291a7340eb68828a822ca3fa5d71d3275f98954e75e`) and the locked rubric `b3e8f204c9c9e8b277c7576c333bfe5f3f0de96bfb9a9d2634a01e09acf48a22`. It covers executive, technical and training slides, charts, tables, a diagram, notes, hyperlinks and dense layouts. All routes use the same source content.

The comparison lanes are:
1. Marp HTML viewed in a browser (the existing web-view output; the repository has no separate web-native slide renderer).
2. Marp PDF.
3. Marp flattened PPTX.
4. Experimental editable Marp PPTX backed by LibreOffice.
5. Native editable PPTX baseline.

Do not count Marp HTML as a second independent implementation lane. Report the absent standalone web renderer as a limitation and route decision; creating one is outside the frozen scope. No Figma, Canva, Google Slides or cloud runtime calls are needed for this export-only decision. Local desktop application receipts are required where the matrix says so. Do not promote the experimental editable route unless its evidence meets the frozen per-case gate. Keep notes support, editability and visual fidelity as separate dimensions.

## Frozen acceptance criteria

- **614-A1 Input identity:** Bind every comparison to the 12-slide fixture and locked rubric hashes; verify slide IDs, order, claims, figures, source links and notes before export.
- **614-A2 Cross-format coverage:** Generate or reuse the exact-candidate Marp HTML, PDF, flattened PPTX and experimental editable PPTX plus the native PPTX baseline. Reopen every artifact and bind format/runtime versions, slide count, dimensions and output hashes.
- **614-A3 Content parity:** Compare titles, claims, categories, values, units, chart labels, source links and notes to the shared fixture. Keep format losses explicit; no missing values, source-category collapse, silent fallback or unsupported output may pass.
- **614-A4 Visual fidelity and accessibility:** Review all 12 slides per applicable route using comparable screenshots. Record clipping, overflow, wrapping, missing glyphs, contrast/link affordance, notes and per-slide image-diff metrics. Threshold is MAE ≤0.20; visual review remains mandatory.
- **614-A5 Object-level usability:** In LibreOffice Impress, perform the same bounded title-text and shape-move task on disposable copies of the experimental editable and native PPTX baselines; save, close and reopen, then verify persisted object changes. Verify the HTML browser navigation and link behavior. Record notes and hyperlinks independently.
- **614-A6 Repeatability and build time:** Run two builds from identical pinned inputs/dependencies; record per-route elapsed times, output hashes and screenshot hashes. Separate source determinism from format-conversion drift.
- **614-A7 Failure and security:** Verify missing-browser/LibreOffice and unsupported-theme behavior fails closed, no route silently downgrades, and renderer runs without network access. Reuse #609/#610 regression contracts.
- **614-A8 Maintenance and usability comparison:** Inventory the pinned dependencies, conversion steps, operator actions and limitations for each lane. Make only evidence-backed relative cost statements; do not invent monetary costs or unmeasured runtime claims.
- **614-A9 Decision/report:** Publish a comparison report with source/artifact identities, screenshots/contact sheets, measured results and explicit routing recommendations for executive, technical and training use cases. State that no standalone web-native renderer is available. Report Cloud Next runtime as N/A because this scope changes no Site behavior.

## Test plan

The detailed ledger is `evals/campaigns/iteration-14-pres08-pilot-e2e-decision-gate-2026-11/acceptance-matrix.md`. All required rows start NOT_RUN. Candidate results from #613 may be reused only when exact source, fixture, rubric, output hash and test surface match; otherwise regenerate and rerun on the locked candidate. Test local outputs in Impress and a browser, and require PR offline CI plus exact-main validation on the final candidate. The user-provided `28c7…` ZIP is an earlier source artifact and is excluded; use the c0/ae8dd evidence identities instead.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Artifact / payload digest | Build + offline CI | Observed desktop/runtime identity | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| Baseline source for reuse | Code candidate `c0cf0d45c7b290a0297380a0f8ab327b58c3d162`; exact main implementation merge `ae8dd753ed8980aa9dd6b188fd4cb1d3feaf27db`; docs-only descendant baseline `565d814fed8c31504fefac58ed4752c2833b649e` | Marp artifact `sf-presentation-marp-ae8dd753ed8980aa9dd6b188fd4cb1d3feaf27db`, SHA-256 `de00e9de2d1221dcce1363933aeeb306ffe9682bf29dfa0576fff2c316173fd5` | PR #651 and exact-main required checks passed; references are in the PRES-07 matrix. | Impress 26.8.2.2 title/shape edit receipt exists for exact c0 editable output; native-baseline manual task remains to be executed for #614. | Reuse only with matching hashes; #614-A5/A6/A8/A9 still require pilot-specific evidence. |
| PRES-08 pilot / diagram corrective candidate | PR source `bbc775a52fd58f3e7cf34e819f65c5135ec9373e`; exact main merge `fd45e13d63dde99108b2129a1a2eacd5cabc7617`; identical tree `68787f0f7b61d870290a8935ba4a5e6ad4fa8ca7` | PR artifact SHA-256 `a53f17236a90b0db5e48e8bf8c6b5e704ddf2f4e0035d8bd0c3f613f3aba24b0`; exact-main artifact `sha256:183ca74633b02f8201b4af4a2ab241760ed9a70f6a14cfe13b25ccabd7ef4bb8` | PR CI passed for head; exact-main required workflows passed: Marp [43303844082](https://github.com/aras-2003/skills-factory/actions/runs/43303844082), Validate Skills 43303844043, Domain Integrity 43303843816, Lab packaging 43303843798, Pages 43303842947. | PR artifact visually inspected across all 12 slides and five lanes; contact sheets committed to the campaign. Impress edit persistence confirmed on disposable outputs. | Diagram relationship overlap fixed in #658. Matrix rows 14-01–10, 14-12–13 and sentinels have evidence; 14-11 and 14-14 remain NOT_RUN pending manual browser interaction. |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: no code changes are planned; the pilot exercises the existing Marp export adapter, DeckSpec input, native PPTX baseline and shared evidence checks.
- Included cases / exclusions: all five frozen routes, 12-slide synthetic source, desktop edit tasks, browser navigation, timing/determinism, failure handling and decision report. No external platform runtime is included.
- Fixed sentinels: #609 local-asset/network/security contract; #610 no-silent-downgrade routing; report-composer and visual-output-design unchanged-domain probes.
- Planned inventory: 9 frozen criteria, 14 matrix rows, two repeated generation runs per output route, 12 slides, 5 output routes and two desktop object-edit tasks; see the matrix for case-level repetitions.
- Critical stochastic scenarios: none; outputs and task receipts must bind to exact source/runtime identity.
- PR CI / final-main checks: Validate Skills, Domain Integrity, Evaluation CI and Marp adapter CI as applicable; final artifact and every report citation must match the candidate SHA.

## Defect intake and clarifications

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None at scope lock | Existing #613 artifacts are reused only with matching hashes; missing standalone web renderer is an explicit route limitation, not a silent PASS | No defect inferred at lock | N/A | N/A | Owner |
| #657 discovered during #614 visual validation | 614-A4 native diagram relationship text overlapped alternative text | Corrective defect fixed by merged PR #658; no Site/Cloud Next change | #658 | 14-06, 14-08, 14-09 | Owner |

## Closure / abort decision

- Outcome: ACCEPTED pending publication of evidence closeout and GitHub issue reconciliation.
- Candidate / immutable evidence: merge SHA `fd45e13d63dde99108b2129a1a2eacd5cabc7617`, exact-main artifact digest `sha256:183ca74633b02f8201b4af4a2ab241760ed9a70f6a14cfe13b25ccabd7ef4bb8`, and campaign report `evals/campaigns/iteration-14-pres08-pilot-e2e-decision-gate-2026-11/decision-report.md`.
- Committed Issues accepted / unresolved: #614 pending; #283 remains an open tracking umbrella and is not added to this increment.
- Matrix totals: 14 PASS, 0 FAIL, 0 NOT_RUN; three shared regression sentinels PASS. See the candidate results in the acceptance matrix.
- Shared regression verdict: PASS on exact-main SHA `fd45e13d63dde99108b2129a1a2eacd5cabc7617`.
- Scope compared with lock: any new renderer, cloud authoring platform, Site behavior or production release requires a new planned scope.
- Issue / Project / PR reconciliation: #614 closure and native Project status update remain pending evidence closeout publication; native Project iteration remains unassigned. No Site/Cloud Next behavior changed.
- Owner proposal / reviewer acceptance / decision timestamp: owner self-review; record exact lock SHA after PR merge.
- If ABORTED: not applicable.
- Next iteration eligibility: complete or formally abort Iteration 14 before any later iteration starts.
