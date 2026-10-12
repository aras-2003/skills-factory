# Iteration 1 — prospective acceptance and evidence matrix

**State: NOT LOCKED.** This is a truthful gap inventory, not an approved frozen criterion set. Exact final main candidate, Lab payload digest and independently observed provider/surface identity are **UNKNOWN**. A CI pass on a component PR is not an iteration runtime PASS.

| Issue | Criterion / required proof | Current evidence | Verdict | Next gate |
| --- | --- | --- | --- | --- |
| #160 | 90 historical IDs mapped exactly once | `backlog-legacy-issue-map.json` (PR #332) | REVIEW_REQUIRED until CI on amended head | Validate updated map against current BACKLOG.json |
| #160 | All overlap dispositions and live Project membership/status/fields/dependencies | Partial screenshot/pilot only | BLOCKED | Authorized Project V2 item-by-item readback + overlap assessment |
| #160 | Approved cutover and README authority | Proposed docs PR #332, not merged | REVIEW_REQUIRED | Owner approval after complete Project audit |
| #233 | Two-week planning and working agreement | Closed #233; PR #331 merged | historical source DONE | Not a release or iteration outcome |
| #234 | Current main SKILL/WORKFLOW/Lab source versions | #270 and inspected tree (64 skills, 19 workflows); historical 54/17 | REVIEW_REQUIRED | Verify manifest revisions/runtime against actual source |
| #234 | Each AIS/RT linked to exact revision and status | Not supplied in current integrated receipt | BLOCKED | Audit history and independent evidence map |
| #258 | Competing active backlog files reviewed; no accidental archival | Historical roadmap/docs observed | REVIEW_REQUIRED | Complete source-wide inspection; classify every active/historical file |
| #249 | License and redistribution status explicitly determined | No license approved, PR #332 describes current legal limitation | BLOCKED | Owner licensing decision; do not assign license unilaterally |
| #249 | SECURITY.md secure reporting route/version support verified | PR #332 creates conditional route, private channel not verified | BLOCKED | Verify GitHub private security intake or authorize alternate private channel |
| #249 | CODEOWNERS/real reviewer capacity | PR #332 maps known owner, no independent reviewer | REVIEW_REQUIRED | Exact-head CI and independent/explicit self-review |
| #245 | Static scanner coverage, mutation/suppressions and source receipt | PR #333 and merged #274 | REVIEW_REQUIRED | Code review + full negative/positive mutation suite |
| #245 | Actual untrusted-content/obfuscation runtime behavior | No executed identity-bound receipt | NOT_RUN | Isolated controlled runtime/security evaluation |
| #246 | Five-dimension contract and source inventory | Merged #280/#324; PR #334 preflight | REVIEW_REQUIRED | Observed-vs-declared audit and per-component manual evidence |
| #246 | Host manifest preconditions and write approvals observed in real runtime | PR #334 only checks caller-supplied manifest | NOT_RUN | Verify exact host/connector identity and denied/approval paths |
| #248 | Immutable Actions, dependency locks and publisher job permissions | Merged #270/#279 partial; exact admin rules unknown | REVIEW_REQUIRED | Complete GitHub workflow/lock and promotion-path audit |
| #248 | main/production branch protection + required reviews | GitHub protection API returns 403; rulesets list empty | BLOCKED | Repository admin access/readback and change authorization |
| #248 | Immutable publication identity, digest and rollback rehearsal | Static validator only | NOT_RUN | Authorized isolated publisher rehearsal |
| #291 | thesis-monitor source authorization/failed-read rules | Merged #292/#305 source behavior | REVIEW_REQUIRED | Runtime replay on isolated TEST store |
| #291 | Approved, denied, unavailable READ/WRITE and receipt verification | Missing isolated execution receipts | BLOCKED | Synthetic fixture + explicit approval/denial and independent rubric |
| #303 | Harmonized investing write authority across downstream workflows | Merged #304/#305 | REVIEW_REQUIRED | Same candidate/identity integration smoke |
| #303 | Side-effect absence, authorized idempotent writes, denied store cases | No executed isolated trace | BLOCKED | Disposable TEST target + actual read/write/denial receipts |
| All | Exact combined main candidate checks, catalog/build and source SHA | Individual PR CI only | NOT_RUN | Post-integration exact-main validation |
| All | Independent installed-version smoke and cross-domain sentinel regressions | No receipts for this candidate | NOT_RUN | Scope-locked campaign; separate executor inputs and evaluator rubrics |
| All | Verified Project status/native Iteration, PR reconciliation, reviewer close | Issue markers updated, no Project GraphQL readback | BLOCKED | Inspect Project #1 and obtain review/closure decision |

`REVIEW_REQUIRED` is not a failing code assertion. `BLOCKED` means a required external prerequisite is not available. Every row must be individually resolved or its nonapplicability approved under the source-lock protocol; do not label required rows N/A merely to close the iteration.

## Counts and compatibility
Distinct planned criterion rows: **25**; the count is a preliminary audit inventory, not execution coverage. No final integrated candidate or complete runtime source/trace/receiver evidence exists. The owner must expand this into the policy's exact per-surface case IDs, run repetition counts, input/rubric SHA isolation and immutable receipts before freezing or closing the iteration.
