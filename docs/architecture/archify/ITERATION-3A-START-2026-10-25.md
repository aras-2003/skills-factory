# Archify Iteration 3a — start and acceptance lock

Status: ACTIVE — owner-authorized on 2026-10-25.
Owner: repository owner (user authorization in the coordinating task).
Reviewer: Codex self-review; this is not an independent reviewer.
Baseline: `main` at `b4440555bae81abaacaac2da113ae0ccd25a1074`; all 17 commit checks completed successfully.
Scope: parent #373 and child issues #374–#380, in the fixed order below. The user authorized completion of all Archify tasks and future merges/deployments in scope. Production deployment is not implied by source acceptance.

This record starts the previously planned 3a work against the verified current main. It supersedes the stale planning baseline in PR #416. Do not call a child Done until its listed acceptance evidence exists on the integrated main revision. Record PASS/FAIL/BLOCKED/NOT_RUN with source revision and durable artifact links. An explicit limitation may narrow an acceptance criterion only through a reviewed, documented scope change; missing evidence alone is not a pass.

## Acceptance matrix

| Issue | Acceptance | Required evidence |
| --- | --- | --- |
| #374 ARC-01 | Pinned Archify source/license/dependencies; synthetic-only deterministic PoC; reject unsafe input; exercise upstream CLI and browser. | Exact upstream SHA and lock digest; dependency/advisory disposition; positive finalize/browser check and negative invalid-input check; artifact SHA; screenshots and stated human-review scope. |
| #375 ARC-02 | Typed canonical IR, semantic relation allowlist, immutable Git source/locator verification, deterministic digest; unknown remains explicit. | Valid/invalid schema fixtures; forbidden relation, stale SHA, missing file/line and traversal negatives; reproducible digest; exact-head CI and review. |
| #376 ARC-03 | Deterministic IR-to-Archify adapter; pinned renderer; safe offline fallback; no publication or writeback. | Real adapter fixture; source verification; independently evidenced network/filesystem boundary; symlink/path traversal, timeout, active-content and renderer-failure negatives; HTML/SVG digest and browser evidence. |
| #377 ARC-04 | Skills Explorer for 10–15 real skill/workflow metadata records; exact version/path provenance; execution/dependency lineage; missing/skipped gate and cycle display. | Canonical registry fixtures; source trace for each node/edge; missing/skipped gate, cycle and unresolved-relation cases; rendered view review. |
| #378 ARC-05 | OAF cross-layer view capability→process→application→data→owner only where source exists; preserve AS-IS/TO-BE and unknowns. | Source-derived OAF fixture; traceability for each element/relation; missing-data and impact-exploration cases; no invented entities; render review. |
| #379 ARC-06 | Export matrix for interactive HTML, SVG/PNG, DOCX/PDF/PPTX; preserve semantics and provenance. Claim native editable shapes only if implemented and tested. | Same fixture across each supported format; node/edge/title/data equivalence; accessible text; output hashes and per-format visual checks; unsupported formats rejected explicitly. |
| #380 ARC-07 | Integrated source→IR→adapter→renderer acceptance, exact-version ledger, controlled failures and release gate. | Combined #374–#379 matrix on one candidate; stale revision, unknown evidence, invalid relation, timeout and renderer-failure cases; exact CI artifact/runtime receipt; parent checklist. |

## Fixed execution order

1. #374 → #375 → #376 → (#377 and #378) → #379 → #380.
2. The old PR #385/#386 candidates predate this lock. Re-review and rebase them to the locked baseline before merge; exact-head CI and post-merge main checks are required.
3. PR #389 is stacked on #386. Rebase it after #375 merges and complete the renderer/network-boundary evidence before merge.
4. Implement #377 and #378 after the shared IR/adapter are on main; implement #379 after those models are available; finish with #380 integration.
5. Close each child issue only when its acceptance row is evidenced on main. Close #373 only after all child rows are resolved and the integrated release gate passes.

## Cross-cutting safety and evidence

- All renderer inputs and generated HTML are untrusted. A hosted CI job is not proof of OS network or filesystem isolation. Until that boundary is demonstrated, use synthetic fixtures only.
- Do not process private or production data in the PoC; do not place active HTML on a privileged origin; do not elevate model-authored claims to observed facts without source and domain review.
- Source existence proves provenance, not semantic truth. Unknown facts and unsupported formats remain explicit.
- Test every PR at its exact head and re-run applicable checks on the resulting main SHA after each merge. Finish with the full shared acceptance matrix on one integrated main candidate.
- The owner authorization applies to in-scope merges/deployment, subject to repository checks and platform review. It does not waive evidence or safety gates.
