# Iteration 01 — informed current-session retest, 2026-10-14

This is a supplemental, owner-requested retest in the current shared Project session, with the evaluator criteria already known. It is **not an independent ordinary-chat regression campaign**, and does not overwrite the frozen v30 result of 20 PASS / 4 FAIL / 7 BLOCKED.

## Candidate and execution
Actual runtime_info: Site release/source 025ed09cce3899400c751b342d7f7def5a907980, Lab0.35.1 source e3d6e74b092cfcfc77305a9bde343daa59dd390d; attestation verified.
Catalog digest 5e06e989af6964ad4bb917df53b3a2ab8486e342c890833a1a344641998cf59f.
Embedded artifact SHA-256 3209789b018a0f6047862cffdcc0eae5bf23cd60aa555d5dfd25992019b0b658.
MCP runtime, route and skill-load operations are callable in this session. The earlier ordinary-chat unavailability is not evidence of a server outage. Its cause remains undiagnosed.

## All 11 requested positions
| Case | Reps | Current-session result | Scope |
|---|---:|---|---|
| GOV-001 | 1 | PASS response check | Exact source sets/revisions/digests and native Project membership/field/dependency readback required; no invented completion. |
| GOV-002 | 1 | PASS response check | Historical receipt rejected; observed candidate release ID and actual payload SHA-256 explicitly required. |
| MON-001 | 3 | PASS informed response check | Explicit BLOCKED_CANONICAL_READ, PARTIAL_EVIDENCE and NOT_WRITTEN kept separate; 15% remains unverified; no canonical health conclusion or fallback. |
| MON-002 | 3 | PASS storage integration | Fresh single approved synthetic append for each repetition, count=1 on real readback, all identity/confidence fields NULL. |
| INV-002 | 3 | PASS scoped storage/authority integration | Fresh single append each; actual duplicate INSERT ON CONFLICT DO NOTHING returns zero rows; readback count stays1. Caller-denied variants invoke no write and read back absent. |

The three MON-001 positions use separately observed routing/child loads but one shared model synthesis; these are **not three independent stochastic responses**. GOV answers are informed demonstrations of the required response contract, not blind regression evidence.

The six storage cases use the original input plus already supplied verified TEST setup and the owner's latest request to repeat tests, interpreted as authority for six newly announced single TEST-only appends. Old consumed keys were not reused. No production access, historical rewrites, activation, owner decisions or trades occurred.

For INV denial, the test is caller authorization enforcement with zero write invocation and observed absent denied keys. It is **not** a database credential/RLS rejection test. Duplicate SQL verifies the tested idempotent storage operation, not hidden execution by an opportunity-hunter model in another host.

For MON, synthetic ACTIVE labels were not represented as canonical ACTIVE thesis versions. Canonical thesis-health execution remains NOT_RUN; storage success does not certify full thesis monitoring.

## Delivery and remaining acceptance
Private exact inputs, host-generated outputs and actual MCP/Supabase receipts are retained separately. Original input text is unchanged; setup/context additions are explicit. Results and verification timestamps are preserved.
A local result-parser failure occurred after the first successful append; its stored receipt was reconciled and read back without repeating that append.

This retest resolves current-session tool availability and demonstrates corrected informed responses and six storage operations on the current candidate. It does not establish isolated-host reliability, an independent all-pass campaign, canonical ACTIVE monitoring, candidate rollback, complete historical/Project dispositions or final owner acceptance. Those remain separate from these results. No ticket/iteration is automatically closed.
