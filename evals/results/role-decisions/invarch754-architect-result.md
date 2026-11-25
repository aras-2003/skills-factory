# Architect review — Issue #754

Observed pinned source SHA: `2d4d8595d10a49b1b29f9e5c9b9954d2e02ce8c0`.

Recommendation: implement first as an offline deterministic synthesis function that consumes #753 context/results plus strict typed decision evidence. Keep the production workflow unchanged. The pure function emits ordered G0–G6 gates, references evidence, requires owner approval, sets `execution_authorized=false`, and performs no writes or numeric sizing.

Key finding: #753 generic `SUCCESS`/`VERIFIED`, free text, or `LEGACY_OPAQUE` cannot prove a G1–G6 predicate. Any decision signal needs an allow-listed producer/version plus exact result, claim/metric, evidence and policy references. Position state must bind to the same instrument and a complete dated portfolio snapshot. Unknown material constraints abstain. Caller assertions and source digests are not authenticated by this offline implementation.

Gates: G0 validates schema/identity/horizon/cutoff/lineage; G1 preserves evidence conflict versus verified financial-quality block; G2 checks explicit eligibility while allowing independent research to continue; G3 carries the independent challenge result; G4 relays compatible dated valuation/method/downside/horizon without averaging; G5 applies literal policy, distinguishing review threshold (`TRIM_REVIEW`) from hard-cap breach/reduction review; G6 is N/A when timing is omitted and UNRESOLVED when supplied but unusable.

Do not emit BUY/ACCUMULATE/direct TRIM/SELL merely to fill the taxonomy. Source lacks approved thresholds and precedence for these; the issue should remain open until mappings and matched historical/runtime evidence are approved. WAIT/HOLD/invalidation review/AVOID are also proposed mappings, not calibrated rules; positive cases need explicit applicable policy and supporting states.

Compatibility: keep the existing `investment-security-review` route/load/stop behavior and outputs unchanged; no workflow registration, report/store changes, migration, or deployment. Before adoption rollback removes #754 references and retains #753; after adoption stop new references and keep a v1 reader or explicit adapter before removal.

Runtime: current Cloud Next runtime verifies existing route/load only; it cannot execute the candidate Python module. Candidate MCP runtime is NOT_RUN. Matched authenticated historical archive fixtures are also unavailable; do not infer their acceptance from synthetic tests.
