# Iteration <id> acceptance matrix

Template only. Follow [iteration delivery](../ITERATION-DELIVERY.md). The complete required-row set is established at scope lock. A candidate change supersedes evidence; it never erases it.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface/model/tools | Input/rubric hashes | Execution state | Verdict | Receipt/output/trace + run time | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <AC-01-offline> | <Issue/AC-01> | <unit/static check> | required | <candidate> | offline | <test revision> | NOT_RUN | none | <missing> | <owner> |
| <AC-01-runtime> | <Issue/AC-01> | <behavior case> | required | <candidate> | <surface> | <hashes> | NOT_RUN | none | <missing> | <reviewer> |
| <shared-smoke> | iteration | <installed identity + invocation> | required | <candidate> | <each required surface> | <hashes> | NOT_RUN | none | <missing> | <reviewer> |
| <shared-regression> | iteration | <routing/auth/evidence/output/critical-path sentinels; expand into separate rows> | required | <candidate> | <surface> | <hashes> | NOT_RUN | none | <missing> | <reviewer> |

Use existing receipt semantics for execution state and verdict; do not invent PASS for absent execution. Split cases and surfaces into separately reviewable rows. The table is an index, not a replacement for detailed receipts.

Completeness review: every frozen criterion mapped; every required case/surface accounted for; verdicts compatible with final candidate; no duplicate row IDs or unreviewed N/A; no required FAIL/NOT_RUN/BLOCKED/REVIEW_REQUIRED; durable evidence links verified. Retain prior candidate tables or link immutable snapshots when superseded.
