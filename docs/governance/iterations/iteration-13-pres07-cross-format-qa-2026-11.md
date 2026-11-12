# Iteration 13 — cross-format presentation QA (PRES-07)

- State: ACTIVE; implementation slice #646 is merged, but closure gates remain pending manual/editability evidence, per-slide visual review, and completion of all 23 matrix rows.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #613 / assign the current native Project iteration separately after lock; do not infer from the issue.
- Previous terminal iteration: Iteration 12 CLOSED / ACCEPTED, tracking issue #612; closeout PR #644, merge SHA `56a28aff02897de103f2e7b6b9825caa6222a19a`.
- Baseline main SHA: `56a28aff02897de103f2e7b6b9825caa6222a19a`.
- Lock commit SHA: `0ced426fc15833a39694632a30cd3dbe0485a09d`.
- Started at / closed at (UTC): 2026-11-11 23:42 UTC / pending.
- Scope lock reviewed by / at: owner self-review / 2026-11-11 23:42 UTC; not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #613 | 613-A1–A8 | Build one synthetic 10–15-slide reference deck and a cross-format evidence harness for HTML, PDF, flattened Marp PPTX, experimental Marp editable PPTX (LibreOffice), and a native editable PPTX baseline. Inspect actual outputs for content/data fidelity, dimensions, visual defects, links, notes, accessibility basics, and object-level editability. Bind receipts to exact source/output hashes. | Parent #283 completion; PRES-08 pilot/route decision (#614); external-skill supply-chain work (#615–623); real/customer data; Cloud Next runtime or production release; claiming flattened images are editable; claiming CI proves manual PowerPoint editing. | #608–#612 are closed and accepted on/before baseline. Reuse canonical DeckSpec, Marp adapter, receipts, theme registry, exhibit pipeline, existing CI and image comparison. Microsoft PowerPoint is installed on the host; CI has pinned Marp/LibreOffice/Chromium. | M |

## Design and ownership boundary

DeckSpec and its provenance/data references remain canonical. The benchmark has 12 synthetic slides spanning executive, technical and training layouts, including charts/tables/diagram, notes, hyperlinks, dense text and wrapped labels. Every render is derived from the same versioned source. The native PPTX baseline contains actual PowerPoint text/shape/chart objects and matched content; it is a comparative output, not evidence that Marp flattened output is editable. No network fetch, external provider, real data, or new renderer is allowed unless a scoped finding proves existing paths insufficient.

Results remain separate for content fidelity, visual fidelity, editability, and runtime/manual inspection. Explicitly report format limitations, unsupported inputs and NOT_RUN states. Flattened Marp PPTX must be classified non-editable at slide-element level. Editable PASS requires selecting and modifying actual objects in PowerPoint/Impress, saving, reopening and retaining before/after evidence. The experimental Marp editable mode’s missing notes and fidelity limitations must be recorded.

## Frozen acceptance criteria

- **613-A1 Reference fixture:** 10–15 synthetic slides; stable source and rubric hashes; required content and provenance are machine-checkable.
- **613-A2 Format coverage:** Generate and reopen HTML, PDF, flattened Marp PPTX, experimental editable Marp PPTX, and native PPTX from the locked content; record dimensions, slide counts, format/runtime versions, output hashes and unsupported/not-run states.
- **613-A3 Content/data fidelity:** Extract and compare titles, claims, labels, values, units, categories, sources, links and notes to the canonical fixture. No silent omission, reordering, unit/value mutation, or collapsing a source category into “Other”.
- **613-A4 Visual/accessibility inspection:** Capture comparable slide images; detect and review clipping, overflow, missing glyphs/font fallback, line-wrap drift, contrast and link affordances. Record per-format and per-slide findings. No aggregate PASS can hide a required failure.
- **613-A5 Object editability:** In PowerPoint/Impress, inspect and modify a text object and a shape/chart where present; save and reopen the actual PPTX and retain object-level before/after evidence. Flattened output is explicitly non-editable at slide-element level; no CLI-only editable PASS.
- **613-A6 Reproducibility:** Rebuild Markdown outputs twice from identical locked inputs/dependencies; compare source/render content and visual output separately from PPTX conversion fidelity. Record tolerances and hashes.
- **613-A7 Fail-closed/reporting:** Missing browser/LibreOffice, unsupported complex CSS and conversion failures must be explicit BLOCKED/FAIL; never silently downgrade format or editability. CI may assert offline artifacts/receipts but cannot set manual/runtime acceptance to PASS.
- **613-A8 Regression:** Retain fixed Marp/export security and no-silent-downgrade sentinels (#609/#610 contracts), plus report-composer and visual-output-design unchanged-domain probes; add regression cases for any defect found here.

## Test plan

See `evals/campaigns/iteration-13-pres07-cross-format-qa-2026-11/acceptance-matrix.md`. Required surfaces: pinned CI renderer (Chromium, Marp, LibreOffice), output-file reopen/inspection, and desktop Microsoft PowerPoint for actual object edits. Inputs and expected values are synthetic and separate from evaluator assertions. CI artifacts retain 90 days; archive final exact-candidate outputs and manual before/after evidence at closure. No Cloud Next runtime row: this is export QA only, not a skill/runtime behavior change.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| C1 implementation slice | PR head `906b4805d861c1c1b5da60cab5b63fcbb2d7a1de`; exact main merge `3c3f9c14c37bde744002c15de4e767f87fe27174` | N/A; no skill/runtime release in this export-QA scope | PR: Marp 43205228628, Validate 43205228700, Domain 43205228634 all PASS; exact main: Marp 43207105745, Validate 43207106024, Domain 43207105558 all PASS; Pages deployment 43207104377 success | LibreOffice 7.4.7.2; 12-slide native baseline reopened; 12 slides/notes, 1 external link; manual edit NOT_RUN | No scope change; acceptance remains pending |
| C0 baseline | `56a28aff02897de103f2e7b6b9825caa6222a19a` | N/A | Validate skills, Domain integrity, Lab packaging and Pages completed successfully; see runs 43120872583, 43120872357, 43120872430, 43120871697 | N/A for export-QA baseline | None |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: presentation output artifact inspection, receipts and existing Marp export; canonical DeckSpec itself is unchanged.
- Included cases / exclusions: all five locked formats, fixture semantics and receipts; detailed rows in the matrix. Parent #283 and pilot decision #614 are excluded.
- Fixed sentinels / rotating probes: Marp security/export contract; #610 no-silent-downgrade; report-composer and visual-output-design.
- Last full renderer baseline: exact-main source SHA `7013fe254a967182ccda3ec380b1539b5a8688a7`, run 43116579244; its artifacts predate this new 12-slide comparative fixture and are not acceptance evidence for #613.
- Planned inventory: at least 12 fixture slides; 5 format outputs; per-format content/open/visual checks; 3 PPTX editability classifications; 2 deterministic builds; required failure-mode tests; 2 fixed and 2 rotating regression probes. Exact distinct scenarios and executions are itemized in the matrix.
- Critical stochastic scenarios: none; outputs under test must be deterministic.
- PR CI / final-main checks: required Validate, Domain, Marp workflow, plus artifact and matrix review. Post-merge checks must be verified on exact main candidate.

## Defect intake and clarifications

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| PDF claim matcher case normalization produced false missing-claim reports for capitalized words | 613-A3-content-pdf; assertion reliability defect, fixed and verified | P2; assertion false negative; resolved by PR #646 and verified on exact main | PR #646 / exact main `3c3f9c14c37bde744002c15de4e767f87fe27174` | A3-content-pdf on PR and main | owner self-review |
| None at lock; prior 3-slide ZIP is pre-fix historical evidence, not a candidate verdict | Existing screenshot transition defect was addressed in Iteration 12; attachment is not reused as current acceptance evidence | No open defect inferred | N/A | N/A | Owner |

## Closure / abort decision

- Outcome: PENDING; Iteration 13 remains ACTIVE.
- Candidate / immutable evidence: PR #646 merged at `3c3f9c14c37bde744002c15de4e767f87fe27174`; exact-main artifact is [run 43207105745](https://github.com/aras-2003/skills-factory/actions/runs/43207105745) (artifact ID 13940391644, SHA-256 `bea445d8ad345e2644bcffb4f89d8122e59ad23bd6a20f3fbfbbd758da1e23c2`).
- Committed Issues accepted / unresolved: #613 pending; #283 remains open and out of scope.
- Matrix totals: 30 PASS executions, 0 FAIL, 12 REVIEW_REQUIRED, 3 NOT_RUN, 0 reviewed N/A; see the updated matrix.
- Shared regression verdict: selected routing/security and report/visual probes PASS on PR and exact main.
- Remaining closure gates: A3 PPTX coverage review; A4 per-slide visual review; A5 manual desktop text/shape edit, save/reopen and before/after evidence; A6 exact repeat-build comparison; A7 dedicated complex-CSS case.
- Scope compared with lock commit: unchanged.
- Issue / Project / PR reconciliation: #646 merged; #613 stays open/ACTIVE. No later iteration is started.
- Owner proposal / reviewer acceptance / decision timestamp: owner self-review only; acceptance decision pending.
- If ABORTED: not applicable.
- Next iteration eligibility: Iteration 13 must be terminal before PRES-08 #614 or any later iteration starts.