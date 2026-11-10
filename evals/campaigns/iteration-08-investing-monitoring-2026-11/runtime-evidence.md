# Iteration 08 runtime evidence — 2026-11-10

## Exact private Site deployment

- GitHub PR #604 merged the Iteration 8 candidate; PR #605 merged the router correction, complete synthetic runtime fixtures, and hash-lock updates. Exact canonical `main` revision under test: `03ef9f554c395db6a1cc482ef2c6434424a250e9`.
- Skills Factory Cloud Next is Site v128 at `https://skills-factory-cloud-next.arek2003.chatgpt.site`, custom owner-only access (one owner, no groups). Deployment `appgdep_6af264fdd71c8191bbeab7c895f9ed9f` returned `succeeded` with MCP ready.
- Site mirror source commit: `a214e7798a28d0fc57bc3de67c54db4bfc79102a`. Saved version: `appgprj_6ac56f2116588191a4a1ebc682c97865~appgver_9abc6b77b4a881918d471445cb7578ca`.
- `runtime_info` completed at `2026-11-10T00:31:08.274Z`: `attestation_status=verified`, identity source `site_environment`, canonical and GitHub `main` revisions both `03ef9f554c395db6a1cc482ef2c6434424a250e9`, Lab release `1.38.481+03ef9f554c39`, payload SHA-256 `9f465d8dba2a877cc3d498313e77a4247a7a75afbd0d462b8e20754138543410`, catalog digest `df2e1731bee541b76d4f025858b9770f94941e9af28a37a9e11da017d543db89`, artifact SHA-256 `98774ade414ab032c6d10835bcbca1b6c4d6ac25f17356614366902aa9e64366`, tool schema digest `sha256:36a02382afadff8963e58dda963997077a1d3c6e2eacc2c18af3ae902123a1e5`.
- `list_skills` completed at `2026-11-10T00:28:45.748Z`, returned 98 skills from the same exact release/source. Its unsigned receipt: input SHA-256 `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`; output SHA-256 `12cd9f3d1caa30dfb93e981b053f85131c2b39cb5bb992608c064823082e0f69`.

## Loaded skill receipts

All five exact packaged targets were loaded from source `03ef9f554c395db6a1cc482ef2c6434424a250e9`; each tool receipt returned `SUCCESS`:

| Skill | Version | Completed (UTC) | Input SHA-256 | Output SHA-256 |
| --- | --- | --- | --- | --- |
| `security-underwriting` | 0.6.0 | 00:28:52.547 | `af41cbe400ff54bb0e6357300fd4b738fe17fb72b112a2035935faa344d5ef3f` | `3699e8543ae7185008eab7102ea4de99282423304b19ca270374c8edb78349c7` |
| `thesis-monitor` | 0.4.0 | 00:28:52.548 | `11bae79d22390fdb166368518d1e41fe54f0b733c6a17b4aac413533cda3fea2` | `8c11d858b00d2892e3fb2ac77ce33d1dc7946d510583ceeec53290e4bf0bc722` |
| `valuation-scenario-review` | 0.4.0 | 00:28:52.686 | `852741e448df6cfcd19556fd7de0cbcca74d3ab8168fb75915c295f5a62a61e2` | `9775e82f6455dbfffed398529dc01687c3a66460cf35d813d5043fef7e393099` |
| `investment-os-review` | 0.3.2 | 00:28:52.484 | `16c3b565b5f6a6c25e3da740e6434bd6bba0ebf448567f04ccc94e5ed3084654` | `39dc65a4560431026214d9bc146db7027034c6a24736fcb508ab5a7966374f24` |
| `investment-security-review` | 0.4.4 | 00:28:52.759 | `95524b2c75374b6cfce3ded2fbdae97a908541e91b3b81f34b0f84808aabb0bf` | `ec2162f7f4e1461bf42f2a721d0af6eb41fec9c49920c340b91e80f94bd88a87` |

## Behavior cases

Execution mode is `host_model_executes_loaded_instructions`; the Site exposes instruction loading and deterministic routing, not a separate skill-execution API. The summaries below are the host model's case outputs evaluated against the paired rubric. `load_skill` receipts prove instruction loading; they are not child-execution receipts.

| Case | Result | Runtime output / rubric evidence |
| --- | --- | --- |
| 308-01 | PASS | Returned two separate ACTIVE-thesis trigger rows from the supplied synthetic-only fixture. NRR baseline 116% LTM through 2026-09-30, source `fixture://iter08/testco/nrr-q3` published 2026-10-15T12:00Z; threshold `<110%` rolling four quarters, quarterly cadence, next check 2026-12-31, action `REVIEW`. GAAP gross margin baseline 42% FY2026 Q3, source `fixture://iter08/testco/gm-q3` published 2026-11-01T12:00Z; threshold `<38%` for two consecutive quarters, rolling two-quarter window, quarterly cadence, next check 2027-02-15, action `MONITOR`. Marked both as review triggers, not approved kill criteria; no write or trade. Fixture facts were explicitly identified as fictional and verified only within this test. |
| 308-02 | PASS | Compared the fixture-supplied ACTIVE gross-margin row (43% FY2026 Q2 baseline; 40% threshold) with 38% FY2026 Q3 from `fixture://iter08/testco/gm-q3`, published 2026-11-01T12:00Z. Classified the specified trigger as `REVIEW`, directed human review by 2026-11-17, and limited the conclusion to that assumption. No automatic invalidation, canonical mutation, persistence claim, or trade. |
| 308-03 | PASS | Reported the supplied 25% price decline as observed; attribution and business evidence remain `UNKNOWN`. Price alone is not a verified business-thesis breach. Security attractiveness requires separate valuation/current evidence; no trade instruction. |
| 308-04 | PASS | Returned `BLOCKED_THESIS_NOT_ACTIVE`; monitoring outcome `NOT_RUN`. A DRAFT is not an ACTIVE baseline. Required an activated thesis and dated baseline/trigger row; did not infer provider evidence or invent persistence criteria. |
| 309-01 | PASS | Kept the synthetic FY2026 Q3 total GAAP revenue series aligned: pre-event consensus USD 2.40bn (source `fixture://iter08/testco/consensus-pre`, 2026-06-25T14:00Z), revision USD 2.55bn (same metric/period, `fixture://iter08/testco/consensus-revision`, 2026-07-05T14:00Z), actual USD 2.50bn (`fixture://iter08/testco/actual-q3`, 2026-08-15T12:00Z). The actual met the original >=USD 2.45bn operating assumption. Kept FY2026 Q4 guidance USD 2.60–2.70bn (`fixture://iter08/testco/guidance-q4`, 2026-08-15T12:00Z) in a separate period row. Did not infer a price reaction or causal explanation. All facts are test-only fiction. |
| 309-02 | PASS | For decision time 2026-06-30, included only the pre-event FY2026 Q3 revenue consensus of USD 2.40bn published 2026-06-25. Excluded the 2026-07-05 revision and 2026-08-15 actual as future evidence. Labeled absent guidance `UNKNOWN`/`N/M`; no imputation. |
| 309-03 | PASS | Labeled the supplied +18% post-earnings return `OBSERVED`; causal attribution `UNKNOWN`. Operating/consensus change, multiple change, and current business attractiveness remain `UNKNOWN` without supporting data. Did not infer causality from timing or equate return with thesis quality. |
| 309-04 | PASS | Returned `BLOCKED_CANONICAL_READ` because the active baseline cannot be read with the Site's available capabilities; comparison did not run. Persistence `NOT_WRITTEN`; no record write or fabricated receipt. |
| 310-EN | PASS (routing) | All three route calls selected `investment-os-review` despite incidental MU. The receipt says `workflow_executed=false`, `execution_state=routed_only`. No portfolio/canonical read or write. No child execution was claimed. |
| 310-PL | PASS (routing) | All three Polish route calls selected `investment-os-review` despite incidental AMD, matching the English behavior. No portfolio/canonical read or write; route receipt does not claim child execution. |
| 310-SEC | PASS (routing) | All three calls selected `investment-security-review` for MU's thesis/valuation/downside request. No methodology-audit route and no write. The child workflow's required canonical store is unavailable in this Site surface, so no security analysis was claimed. |
| 310-NOWRITE | PASS (routing-only) | All three calls selected `investment-os-review`; the selected route is distinct from execution. The supplied workflow requires an execution receipt to claim a child run, and none is available. No portfolio/canonical read or write. |
| shared-portfolio | PASS | All three regression calls selected `investment-portfolio-review` with reason “Portfolio holdings or structure with a risk, concentration or allocation review.” Each remained `routed_only`; no child workflow, account read, or write was invoked. |
| shared-education | PASS | Answered directly in one sentence: “P/E is the share price divided by earnings per share, showing how much investors pay for each unit of earnings.” No Investment OS route or portfolio/canonical read. |

### Three-attempt routing receipts

Each entry is an unsigned `SUCCESS` receipt from the exact Site source above. Each trio has the same prompt input hash and expected output hash; individual completion times are retained here.

| Case | Route / child | Input SHA-256 | Output SHA-256 | Completed times (UTC) |
| --- | --- | --- | --- | --- |
| 310-EN | `os-review` / `investment-os-review` | `f965fe2529f9ad6823556e42d2b91d034b315678513425bba1f8235998e6011d` | `5621583715b1322660cff6919b1bde7b11a465d03304dfc911c8c988dd40411e` | 00:28:36.529, 00:28:36.548, 00:28:36.555 |
| 310-PL | `os-review` / `investment-os-review` | `09a713e96e9a7d29d7b0f76728bfd39569317426fcd41d6baf10d27391f57727` | `5621583715b1322660cff6919b1bde7b11a465d03304dfc911c8c988dd40411e` | 00:28:36.505, 00:28:36.725, 00:28:37.787 |
| 310-NOWRITE | `os-review` / `investment-os-review` | `38677a60d5447ac971a173c4be8281f505b3374cbade21718b670f6f623dcb4e` | `5621583715b1322660cff6919b1bde7b11a465d03304dfc911c8c988dd40411e` | 00:28:36.649, 00:28:36.674, 00:28:37.037 |
| 310-SEC | `security-review` / `investment-security-review` | `d154c3c1e4c365e3cefcbd925f2f46361b5052387c1f4e39813511a254aa732f` | `bfbbb16c69383466b0d355c7bf52f6945c3f9d0154027ac060a8823bdcf142f3` | 00:28:36.452, 00:28:36.649, 00:28:36.661 |
| shared-portfolio | `portfolio-review` / `investment-portfolio-review` | `f1bda9996be97fcc2764ca2d5f2db193792bd77d3446fa0f31e14cfacb5dc2d8` | `695931a3aed6596229c9612e21485b5d8438dac64d58e337bd8bb25ef86a27eb` | 00:28:36.467, 00:28:36.572, 00:28:36.651 |

## Validation and boundaries

- PR #605 head `857970ae23cdd4937111befa3592bf8d0a14d098`: Site CI run 594 PASS; Evaluation CI run 361 PASS; Domain integrity run 953 PASS; Validate Skills run 953 PASS.
- Local Cloud Next contracts: 39 passed, 0 failed. Local eval validators: 314 passed, 0 failed, 2 skipped. Iteration 8 hash/isolation validator passed. Exact-source Site preparation built the Lab artifact; TypeScript check, lint, and Site build passed.
- No portfolio/account data or canonical records were read or written; no trade was attempted. The Site capability surface lacks `investment-record-store` and a child-workflow execution API. Expected fail-closed cases are recorded as blocked/not-run outcomes rather than successful analysis.
- Synthetic earnings/KPI fixtures verify temporal and control behavior only; they do not validate live SEC/provider retrieval or independent authenticity of real-world financial sources. The Site run validates the Lab behavior and does not authorize production promotion (`release_approved=false`).
