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

Required shared checks: targeted external-intake/update-impact tests; provenance and schema validation; security scan; eval isolation/campaign validation; full applicable repository CI and domain integrity; deterministic package build; `git diff --check`. Rotating unchanged source/package probes: `skills/web-design/accessibility-gate/SKILL.md` and `skills/investing/fundamental-intelligence/SKILL.md`. Their source/package bodies must remain unchanged.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| C1 | pending | pending; tooling-only payload expected unchanged | NOT_RUN | reviewed N/A per rationale above | none |

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

## Closure / abort decision

- Outcome: PENDING
- Final candidate / matrix and immutable evidence links: pending
- Committed Issues accepted / unresolved: #619 U1 pending; #619 U2/U3 remain open and out of scope.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: pending
- Shared regression verdict: pending
- Non-blocking findings and accepted impact: current repository lineage is incomplete (98 UNKNOWN records); U1 must report this gap explicitly.
- Scope compared with lock commit: pending
- Issue / Project / PR reconciliation: #619 remains open and In Progress; assigned to native Iteration 31; scope lock PR #709 merged as `a2833043c4422ed69593524b9639f1779faa4766`; implementation evidence pending.
- Owner proposal / reviewer acceptance / decision timestamp: pending; Codex review is not independent.
- If ABORTED: N/A
- Next iteration eligibility: only after this increment is CLOSED or formally ABORTED. No automatic promotion or Site deployment.
