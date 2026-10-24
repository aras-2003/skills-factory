# Archify Iteration 3a acceptance matrix

Status: PLANNED. This matrix does not start or lock Iteration 3a. Start only after the current active iteration is terminal and an owner and reviewer accept the scope, baseline and tests.

Parent: #373. Baseline for planning: main `806b03842358c288dad4060beb3ed43aaa97090d`. Required sequence: #374 → #375 → #376 → (#377 and #378) → #379 → #380. Runtime acceptance is separate from source merge; production deployment is not implied.

| Issue | Acceptance | Required evidence and tests | Current candidate |
| --- | --- | --- | --- |
| #374 ARC-01 | Pinned Archify source/license/dependencies; synthetic-only deterministic PoC; reject unsafe input; render through upstream CLI and browser. | Exact upstream SHA and lock digest; npm audit disposition; positive finalize/browser check and negative invalid-input check; artifact SHA; screenshots with human review scope stated. | PR #385. Latest ARC-01 workflow 40086340844 PASS. Moderate `fast-uri` advisory disclosed; network isolation is not proven. |
| #375 ARC-02 | Typed canonical IR, semantic relation allowlist, immutable Git source/locator verification, deterministic digest; unknown stays explicit. | Valid and invalid schema fixtures; forbidden relation, stale SHA, missing file/line and traversal negatives; canonical digest reproducibility; exact-head CI. | PR #386. Latest ARC-02 workflow 40086340571 PASS. Source references do not establish truth; human/domain review remains required. |
| #376 ARC-03 | Deterministic IR-to-Archify adapter; pinned renderer; safe offline fallback; no publication or writeback. | Real adapter invocation on fixture; source verification; network-denied runner proof; output symlink/path traversal, timeout, active-content and renderer-failure tests; HTML/SVG digest and browser evidence. | PR #389 stacked on #386. Latest adapter workflow 40086340708 PASS; unit CI alone does not prove OS isolation. |
| #377 ARC-04 | Skills Explorer for 10–15 real skill/workflow metadata records; exact version/path provenance; execution and dependency lineage; missing/skipped gate and cycle display. | Representative catalog fixtures from canonical registry; exact source trace for every node/edge; missing/skipped gate, cycle and unresolved relation cases; rendered view reviewed. | No PR/evidence found. |
| #378 ARC-05 | OAF cross-layer view capability→process→application→data→owner only where source exists; AS-IS/TO-BE and unknowns preserved. | Source-derived OAF fixture; traceability for every element/relation; missing-data and impact exploration cases; no invented entities; render review. | No PR/evidence found. |
| #379 ARC-06 | Export matrix for interactive HTML, SVG/PNG, DOCX/PDF/PPTX; preserve semantics and provenance; native editable shapes only if actually supported. | Same fixture through each supported format; node/edge/title/data equivalence; accessibility text; output SHA and per-format visual inspection; unsupported format explicitly rejected. | No PR/evidence found. |
| #380 ARC-07 | Integrated source→IR→adapter→renderer acceptance, exact-version ledger, controlled failures and release gate. | Combined ARC-01–06 matrix on one candidate; stale revision, unknown evidence, invalid relation, timeout and renderer errors; exact CI artifact/runtime receipt; parent issue checklist. | No PR/evidence found. |

## Cross-cutting gates

- Treat all generated HTML and renderer inputs as untrusted. A hosted CI job is not an OS sandbox. Demonstrate network/filesystem restrictions in the runner boundary before processing non-synthetic data.
- No production or private data in the PoC. No active HTML embedded on a privileged origin. No model-authored fact is upgraded to observed without source and domain review.
- Every PR must be tested on its exact head. After each merge, rerun applicable checks on the resulting `main` SHA. At final close, run the complete shared acceptance matrix against one main candidate.
- Record verdicts PASS/FAIL/BLOCKED/NOT_RUN with artifact URLs, hashes and reviewer. Do not mark #373 Done while any required row is missing or unresolved.

## Merge and close order

1. Satisfy the repository iteration start gate and freeze this matrix with owner/reviewer and baseline.
2. Review and merge #385 and #386 independently after all checks pass; test each integrated `main` SHA.
3. Rebase/re-target #389 to `main`, complete network/security/runtime-boundary evidence, review and merge; test integrated `main`.
4. Implement and validate #377 and #378; then #379; finally integrate #380 and run full matrix.
5. Close each child issue only against its evidence, then close #373 when every acceptance row is PASS or an explicitly reviewed non-goal. NOT_RUN/BLOCKED is not Done.
