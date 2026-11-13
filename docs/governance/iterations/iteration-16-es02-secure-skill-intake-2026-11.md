# Iteration 16 — secure external skill intake and immutable authorization (ES-02)

The scope lock is preserved by merged PR #665. This record and its matrix define the entire increment; changes to frozen criteria require a separately reviewed clarification and must not expand acceptance. Follow [iteration delivery](../../../docs/governance/ITERATION-DELIVERY.md).

- State: CLOSED (ACCEPTED); all 16 acceptance rows PASS on the exact implementation source candidate.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #617 / not assigned; native Project iteration is a scheduling mirror.
- Previous terminal iteration / closure link: Iteration 15 / #616 CLOSED / ACCEPTED; [record](../iterations/iteration-15-es01-provenance-schema-2026-11.md); exact accepted main SHA `0c193d6982c8f18255cc33c31356f95078f2e882`.
- Baseline main SHA: `0c193d6982c8f18255cc33c31356f95078f2e882`.
- Lock commit SHA: `1e53068c24470353fa1cb58fe619018033785519`; recorded in #617.
- Started at / closed at (UTC): 2026-11-13T10:27:57Z / 2026-11-13T11:12:47Z.
- Scope lock reviewed by / at: owner self-review / 2026-11-13; not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #617 | 617-A1–A7 | Provide a reusable, deterministic intake library/CLI for local directories/bundles and remote GitHub repositories pinned to a full immutable commit. Inventory safe relative paths and bytes, hash every file, retain author/source/license evidence as claims with verification state, classify license decision as APPROVED/REVIEW_REQUIRED/REJECTED/UNKNOWN, identify exact duplicates, quarantine all content, create reproducible receipt/manifest, and bind any explicit human review/authorization to exact repository/commit/inventory digest so any upstream drift invalidates it. Discovery is static-only; imported instructions/scripts/resources are never executed. | Production imports, package promotion, Site/UI or MCP changes, automatic license approval, trust/security/maturity/channel elevation, capability overlap matching/adaptation (#618), update automation/rollback (#619), domain pilots (#621/#622), and arbitrary URL fetching. Remote intake is restricted to the reviewed provider transport contract and full immutable commit pins. | #616 accepted on exact main SHA above. Reuse canonical provenance schema, `scripts/security/scan_skills.py`, `scripts/strategy/verify_source_corpus.py` (read-in-place archive pattern), `scripts/package/tests/test_packaging.py` (unsafe ZIP defenses), STR-22 #450, and SECURITY.md. Extend existing contracts rather than duplicate them. | M |

## Design and security boundary

Intake is a quarantine and evidence operation, never an installation or promotion operation. It must not import, source, eval, execute, or invoke any file from the candidate. For archives, inspect and hash members in place before any permitted copy into a caller-selected quarantine root; never use unsafe bulk extraction. For directories, reject symlinks and non-regular file types, validate canonical relative paths, and detect source changes during inventory. Apply documented member-count, per-file, total-expanded-size, and compression-ratio limits before reading unbounded content.

Remote acquisition accepts only HTTPS GitHub repository identity plus a full commit SHA, with a constrained redirect allowlist and bounded response size/time. It refuses branch names, tags, abbreviated hashes, credentials, arbitrary hosts and redirects outside the allowlist. Network behavior is deterministic under tests through a mocked transport; tests never retrieve arbitrary third-party content.

The receipt records source type, canonical repository/path, immutable commit when applicable, archive/content digest, complete normalized file list and per-file SHA-256, skill identity, author claim and evidence/verification state, license evidence and decision, static findings, duplicate matches, limits used, and tool/schema version. Receipt and manifest serialization are canonical and deterministic. Author/license text in an upstream file is a claim, not verification. A LICENSE file alone never authorizes reuse.

Decision values are explicit and separate from provenance, security review, maturity, channel availability and production eligibility. Intake emits UNKNOWN or REVIEW_REQUIRED unless an authorized reviewer explicitly records a decision with identity, timestamp, rationale/evidence reference and exact receipt digest. REJECTED is terminal for that exact digest. Approval is unusable when any upstream revision or file digest differs. Static findings are triage evidence, not proof of safety; unresolved prompt injection, secrets, tool permission changes, destructive operations, dependency confusion, network/write behavior and embedded assets require review/refusal. Do not waive findings to make CI green.

## Frozen acceptance criteria

- **617-A1 Inventory/provenance:** local directory, local bundle and pinned remote repository produce a complete deterministic inventory with canonical relative paths and SHA-256 for every file; source/commit, author and license fields preserve verification state and never invent missing facts.
- **617-A2 Immutable pin and reproducibility:** mutable/partial remote refs are refused; receipt and pinned manifest are byte-stable for identical inputs; authorization is bound to exact commit plus inventory digest and becomes invalid on any source/file drift.
- **617-A3 Quarantine/no execution:** discovery never executes or imports candidate instructions or scripts, never makes candidate-directed network/write actions, and does not modify the source tree or production/package/catalog state. Content is only held in an isolated quarantine location after path and size checks.
- **617-A4 Threat handling:** safe and hostile fixtures exercise prompt injection, secret exfiltration, tool/permission escalation, destructive commands, dependency confusion, embedded assets, unexpected network/write behavior, symlinks, traversal, archive bombs, malformed files and missing resources. Static findings/refusals remain explicit and bounded.
- **617-A5 License/review/duplicates:** all four license decisions are modeled separately; no source evidence auto-approves; unknown and rejected states fail closed; exact duplicate detection is deterministic; similarity is review-only; any approval is explicit and bound to exact receipt identity.
- **617-A6 Archive/path safety:** reject unsafe paths, symlinks/hard links, duplicate normalized members, unsupported/encrypted/malformed archive entries and configured resource-limit violations before creating quarantined files; no file may escape the quarantine root.
- **617-A7 Regression/compatibility:** existing security, provenance, catalog/package, repository validation and Domain Integrity contracts pass; no automatic trust, ownership, license, channel, maturity, or production promotion is added.

## Test plan

Authoritative ledger: [Iteration 16 acceptance matrix](../../../evals/campaigns/iteration-16-es02-secure-skill-intake-2026-11/acceptance-matrix.md). All rows start NOT_RUN. Required acceptance surfaces are the deterministic intake library/CLI, local directory and archive fixtures, controlled mocked remote transport, receipt/manifest verifier, quarantine boundary, static security scanner, and repository/package/provenance CI. Runtime N/A is declared at scope lock for Site MCP/Chat and production because no skill, runtime adapter, Site, or package behavior is changed; re-evaluate this against the final diff before closure.

Run deterministic helper contract cases for normal input, invalid input, limits/boundaries, malformed archives and error/fallback. Include authorized review, missing authorization, stale/wrong authorization and unavailable/rejected states with zero unauthorized side effects. Cover each threat vector listed above with a faithful synthetic fixture. Run all configured offline CI suites on every PR revision and applicable exact-main gates; preserve each failed attempt. Final shared checks include identity/invocation smoke, authorization/no-side-effect, receipt integrity, output determinism, source/catalog/package compatibility, and two unchanged-domain validation probes selected before final execution. No real external repository is fetched in CI; any optional manual smoke must use a reviewed immutable fixture and retain exact URL/commit/digest.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| Scope baseline | `0c193d6982c8f18255cc33c31356f95078f2e882` | N/A for scope lock | Existing exact-main closeout checks for #616; this iteration not run | N/A for scope lock; no Site behavior | None |
| Accepted candidate | `ddf800634a7bd6de81d3cd5622dfab154cb910cb` | N/A (CLI tooling only) | PR #666 source candidate `3295a0810fa28351a04eb3f6c81b6e6a38375eae`; Validate Skills `43414175351`, Domain Integrity `43414175314`, Evaluation CI `43414175425` all SUCCESS; matrix evidence lists hashes/artifacts | No Site/runtime behavior; CLI smoke was local synthetic and authorization remained NOT_AUTHORIZED | No prior candidate; merge result is exact source tree from PR #666

## Regression selection and counts

- Changed contracts / direct and transitive consumers: new intake API/CLI, remote transport boundary, quarantine write boundary, receipt/manifest schema, license decision/reviewer gate, duplicate detection, security scan and package/provenance consumers. Verify exact consumer graph before implementation.
- Included cases / exclusions: all 16 matrix rows; archive/path adversarial cases; mocked remote transport; explicit review/drift; existing offline CI and package/provenance/security validators. Excludes UI/runtime/site, production release, arbitrary internet retrieval, adaptation/matching and upstream update automation.
- Fixed sentinels / rotating unchanged-domain probes: no-execution and no-side-effect sentinel; exact-hash/receipt integrity; package/catalog/provenance compatibility; static scanner unchanged behavior; two rotating unchanged skill/workflow probes selected before final validation.
- Last full runtime baseline candidate / behavior iterations since baseline: Iteration 14 exact main `834c29258ce48d111a147b26540f13554a83be34`; this iteration changes repository tooling only; Site/runtime N/A rationale is declared above.
- Planned distinct scenarios / executions: 16 required ledger rows; deterministic directory/ZIP/remote transport suites; all license states; exact duplicate and review gate; source drift; hostile archives; threat fixtures; existing security/provenance/package/validation suites; shared smoke and two rotating probes.
- Critical stochastic scenarios repeated at least 3 times / instability history: none; all acceptance tests are deterministic synthetic cases.
- PR CI / final-main checks and build / external runtime runs: Validate Skills, Domain Integrity, Evaluation CI where triggered, source/provenance/schema, security scan, package profiles and exact-main Lab build as applicable. No runtime deployment requested or claimed.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None at scope lock | Baseline reviewed; no defect inferred before implementation | N/A | N/A | N/A | Owner |

## Closure / abort decision

- Outcome: CLOSED (ACCEPTED)
- Final source candidate: `3295a0810fa28351a04eb3f6c81b6e6a38375eae`; exact-main merge SHA: `ddf800634a7bd6de81d3cd5622dfab154cb910cb`; [acceptance matrix](../../../evals/campaigns/iteration-16-es02-secure-skill-intake-2026-11/acceptance-matrix.md); [PR #666](https://github.com/aras-2003/skills-factory/pull/666).
- Committed Issues accepted / unresolved: #617 accepted and ready to close; none unresolved in locked scope.
- Required rows: PASS 16; FAIL 0; NOT_RUN 0; BLOCKED 0; REVIEW_REQUIRED 0; runtime N/A reviewed against the final six-file implementation diff.
- Shared regression verdict: PASS; all applicable PR workflows passed on source candidate `3295a0810fa28351a04eb3f6c81b6e6a38375eae` before squash merge to `main`.
- Non-blocking limitation: host Python lacked PyYAML/jsonschema; full locked-dependency CI passed and the exact synthetic CLI smoke passed. Owner/reviewer accepts this as environment-only.
- Scope compared with lock commit: unchanged; only the frozen #617 intake command/library, tests, schema, docs, and acceptance evidence were added. No Site, runtime or production behavior changed.
- Issue / Project / PR reconciliation: #665 scope lock merged; #666 implementation merged; #617 accepted for closure; parent #615 and later work remain planned.
- Owner acceptance / decision timestamp: Arkadiusz Kamrowski, 2026-11-13T11:12:47Z (self-review; not independent).
- If ABORTED: reason, partial evidence and complete unresolved-criterion mapping: N/A
- Next iteration eligibility: only after #617 terminal; parent #615 remains planned; no automatic start or production promotion.
