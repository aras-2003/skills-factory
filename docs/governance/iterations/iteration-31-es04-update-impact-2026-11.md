# Iteration 31 — pinned external update impact review (ES-04 U1)

Follow [iteration delivery](../ITERATION-DELIVERY.md). This is a scope lock for the bounded U1 slice of #619, not acceptance of the parent issue.

- State: ACTIVE
- Owner / reviewer: arkadiusz-kamrowski / Codex delegated review (not independent)
- Tracking Issue / native Project iteration: #619 / `31 | External Skills Supply Chain U1` (created and assigned in Skills Factory - Product & Engineering; dates Nov 26–Dec 09, 2027; field readback completed 2026-11-15 UTC)
- Previous terminal iteration / closure link: Iteration 21, #704 accepted; [closeout record](iteration-21-xml-09a-grammar-validator-2026-11.md), [acceptance matrix](iteration-21-acceptance-matrix.md), merged closeout PR #707 and evidence reconciliation PR #708.
- Baseline main SHA: `ebb9a8d00780cc7116bf94a21a6f0c18ee8264e0`
- Lock commit SHA (record in tracking Issue): `48981677809419e7d014664cff1497d9af48ec1b`
- Started at / closed at (UTC): 2026-11-15T23:39:22Z / not closed
- Scope lock reviewed by / at: owner selected dedicated Iteration 31; exact scope diff is recorded in merged PR #709 (no independent review claimed)

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #619 | AC-01/U-T01, AC-02/U-T02, AC-02/U-T03 | Implement manual, read-only comparison of an accepted immutable external source and a proposed full-SHA GitHub candidate. Emit a deterministic source inventory diff and review-impact report covering license evidence/decision, declared tool permissions, added/removed/changed resources and executable mode, deprecation signals, and direct/transitive registered consumers. A changed candidate is `REVIEW_REQUIRED`/`NOT_READY`; failed retrieval, digest mismatch, absent accepted lineage or incomplete consumer lineage is `BLOCKED`/`UNKNOWN`, never “unchanged.” | U2 evaluation/report scoring; U3 rollback/channel restoration; scheduler; import, install, registry mutation, release/maturity/channel promotion; Site/Chat runtime changes; claims that current UNKNOWN registry records have no consumers. | #616 provenance schema and #617 pinned intake closed; #618 adaptation closed; #697 Evaluation Report Contract v1 closed. Verify their exact current interfaces at this baseline. Reuse the intake transport/archive safety and provenance registry; do not change existing intake receipt/manifest v1 schemas. #697 is a dependency of the parent workflow but U1 does not calculate behavioral scores. | S/M |

## Baseline facts and design constraints

- Current baseline: main `ebb9a8d00780cc7116bf94a21a6f0c18ee8264e0`.
- Reuse `scripts/security/external_skill_intake.py`, `scripts/validate/schemas/external-skill-intake.schema.json`, `provenance/registry.yaml`, `scripts/provenance/catalog.py`, and the secure archive limits/path checks. Do not create a second source registry, intake receipt contract, behavioral evaluator or score calculator.
- Current registry has 98 records, all `UNKNOWN`, with zero populated upstream, dependency or component links. The implementation must surface this as incomplete lineage and block an impact-completeness decision; it must not present an empty consumer list as proof that no consumers exist.
- Current intake inventory validates ZIP member type but drops regular-file mode bits from the receipt. Preserve receipt/manifest v1 byte/schema compatibility. If U1 compares executable mode, capture it only in the separate versioned update-impact report using the same bounded, no-extraction ZIP validation; an old mode that cannot be observed remains `UNKNOWN` and blocks a clean comparison.
- The report is a review artifact, not an authorization. It must bind both source identities, exact commits, content/inventory digests, and registry baseline; it must never mutate the accepted record, install candidate bytes, or imply approval.
- Deprecation detection is a review signal only. Report the exact changed paths/hashes and bounded marker deltas; do not claim semantic deprecation analysis from keyword matching.

## Test plan

Authoritative ledger: [Iteration 31 acceptance matrix](../../../evals/campaigns/iteration-31-es04-update-impact-2026-11/acceptance-matrix.md). Required surface is the deterministic local CLI/library plus mocked GitHub transport. Test inputs are synthetic fixtures; no live external repository fetch is required in CI. Keep candidate content inert and never execute it.

Expected coverage includes exact unchanged pins; changed candidate hashes; added/removed/modified files; license evidence and decisions; frontmatter tool declarations; executable/resource additions and removals; deprecation-marker signals; direct and transitive consumer closure; dependency cycles; unavailable or malformed upstream responses; accepted-baseline mismatch; missing lineage; deterministic output/schema; and proof that intake receipt/manifest v1 contracts and registry bytes remain unchanged.

Runtime N/A rationale: this tooling-only slice changes no skill instruction, workflow, routing, Site/MCP adapter, permission declaration, Lab content, or installed runtime behavior. Actual GitHub HTTP behavior is tested through the existing bounded transport with a controlled fake opener. Re-evaluate N/A against the final diff; any runtime-facing change invalidates this rationale. Build the normal Lab artifact after merge and verify the two frozen unchanged-skill package probes; this is package-integrity evidence, not runtime acceptance.

Required shared checks: targeted external-intake/update-impact tests; provenance and schema validation; security scan; eval isolation/campaign validation; full applicable repository CI and domain integrity; deterministic package build; `git diff --check`. Rotating unchanged source/package probes: `skills/web-design/accessibility-gate/SKILL.md` and `skills/investing/portfolio-state-review/SKILL.md`. The second probe replaces the absent original `fundamental-intelligence` path under the 2026-11-16 R02 evidence amendment below.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| C1 | `e9ad5349276a6b94c4ff0dc2e638e7e32475e665` | Lab `1.38.554+e9ad5349276a`; payload `e292b1dbb9025b2ba39c6ca7358ec7bf3f77fea220f734f2afb364ee4a7b2b3a`; artifact ZIP `0c08dd3d137c3bf274c6bab4d9810d71a107acc9aa0a467a24071377a073b494` | PASS — Validate run `43783250083` (12 jobs, incl. 78 security tests; 0 scanner findings), Domain `43783250103`, Lab build `43783250073` | reviewed N/A; no runtime behavior change | R01 PASS; R02 BLOCKED (frozen source path 404) |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: intake archive metadata, external update-impact report, provenance upstream identity and dependency closure. Current repository has no populated external lineage; synthetic registered consumers exercise the graph. Real consumer impact is `UNKNOWN` until lineage is populated.
- Included cases / exclusions: all U1 rows in the matrix; U2 behavioral evaluation, U3 rollback, production data, live Site/Chat execution, and unrelated skill behavior are excluded.
- Fixed sentinels / rotating unchanged-domain probes: intake receipt/manifest v1 compatibility; no-install/no-write security boundary; two unchanged probes named above.
- Last full runtime baseline candidate / behavior iterations since baseline: no runtime behavior changes in this slice; full runtime baseline is not applicable.
- Planned distinct scenarios / executions by layer and required surface: 10 U1 deterministic scenarios plus 2 shared offline sentinels and 2 rotating source/package probes; each required offline suite once per PR and final-main candidate.
- Critical stochastic scenarios repeated at least 3 times / instability history: N/A; no model or stochastic runtime behavior is changed.
- Scope-lock PR #709 CI: PASS (Evaluation CI, Domain integrity, Validate skills at exact lock SHA); implementation candidate PR/final-main checks and build: pending; runtime N/A per reviewed scope.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None recorded at scope lock | N/A | N/A | N/A | N/A | N/A |


## Validation reconciliation — 2026-11-16

- Final main candidate: `e9ad5349276a6b94c4ff0dc2e638e7e32475e665`.
- Security and capability job: 78 tests passed; skill security scan returned 0 findings. The update-impact suite contributed 13 tests.
- Full Validate skills workflow: 12 jobs green (`43783250083`); Domain integrity green (`43783250103`).
- Lab packaging job `43783250073` generated release `1.38.554+e9ad5349276a`, with payload digest `e292b1dbb9025b2ba39c6ca7358ec7bf3f77fea220f734f2afb364ee4a7b2b3a` and immutable artifact ZIP digest `0c08dd3d137c3bf274c6bab4d9810d71a107acc9aa0a467a24071377a073b494`. The tracked release manifest was stale before build; the workflow-generated candidate manifest correctly binds the exact main SHA.
- Rotating probe R01 passes: source and packaged `accessibility-gate` bodies match byte-for-byte after canonical YAML frontmatter normalization. Full-file hashes differ because packaging normalizes frontmatter.
- At the initial validation, rotating probe R02 was blocked because `skills/investing/fundamental-intelligence/SKILL.md` was absent (404) at the candidate SHA. The subsequent evidence amendment below records a replacement probe.
- Runtime row is reviewed N/A because the exact final diff is tool-only. This is not runtime acceptance.
- No closure or maturity promotion is claimed while R02 and owner acceptance remain unresolved.

## R02 probe amendment and revalidation — 2026-11-16

The original R02 target, `skills/investing/fundamental-intelligence/SKILL.md`, is absent at candidate `e9ad5349276a6b94c4ff0dc2e638e7e32475e665` (404). Applying the owner's instruction to supplement incomplete evidence, the coordinator selected the existing investment skill `skills/investing/portfolio-state-review/SKILL.md` to preserve the required unchanged investment-domain source/package probe.

- Candidate source full-file SHA-256: `3e0a1220ad70214d4e3fbe81ded0876eab11f158037f1bb727001b16ba869c8a`.
- Normalized source and generated Lab package body SHA-256: `bb9320335200e3f224d948f760eb92441d2147b1d0522a40e5765084e3789d45`.
- The exact Lab artifact remains bound to run `43783250073`, candidate `e9ad534...`, Lab release `1.38.554+e9ad5349276a`, ZIP SHA-256 `0c08dd3d137c3bf274c6bab4d9810d71a107acc9aa0a467a24071377a073b494`. The current live Site reports older Lab `1.38.531` / source `1d557675...`; it was not used as evidence for this candidate.
- The amended R02 row passes source/package identity. This is static package evidence, not runtime acceptance or production approval.

## Closure / abort decision

- Outcome: PENDING — required technical evidence is complete; independent reviewer acceptance remains outstanding.
- Final candidate / matrix and immutable evidence links: main `e9ad5349276a6b94c4ff0dc2e638e7e32475e665`; [Validate run 43783250083](https://github.com/aras-2003/skills-factory/actions/runs/43783250083), [Domain run 43783250103](https://github.com/aras-2003/skills-factory/actions/runs/43783250103), Lab build run `43783250073`; authoritative results in the acceptance matrix.
- Committed Issues accepted / unresolved: #619 U1 awaits independent reviewer acceptance; #619 U2/U3 remain open and out of scope.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: 14 PASS / 0 FAIL / 0 NOT_RUN / 0 BLOCKED / 0 REVIEW_REQUIRED / 1 reviewed N/A.
- Shared regression verdict: PASS — 78 security tests; security scan reports 0 findings; Validate and Domain workflows green.
- Non-blocking findings and accepted impact: consumer-lineage completeness remains UNKNOWN for the 98-record current registry and is correctly surfaced as BLOCKED by U1.
- Scope compared with lock commit: U1 remains tooling-only; final diff has no runtime-facing instruction, adapter, routing, permission or packaged-capability change. Later evidence/date-refresh commits do not alter the U1 behavior contract.
- Issue / Project / PR reconciliation: #619 remains open and In Progress; assigned to native Iteration 31 per prior Project readback; implementation evidence is published in this reconciliation PR.
- Owner proposal / reviewer acceptance / decision timestamp: owner instruction was to supplement gaps and close when complete; independent reviewer acceptance remains pending. Codex review is delegated and not independent.
- If ABORTED: N/A
- Next iteration eligibility: only after this increment is CLOSED or formally ABORTED. No automatic promotion or Site deployment.
