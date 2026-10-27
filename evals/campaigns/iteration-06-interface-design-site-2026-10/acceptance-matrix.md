# Iteration 06 acceptance matrix — interface-design / Site MCP

Candidate canonical SHA: `7c0f545a054ee411bb79d7a5bc6c0c2b26a3e3b6`

Site version: `54`; provider mirror SHA: `d75338ea2b3bad53142702e73f1f75d689f83394`

Embedded Lab: `1.38.369+7c0f545a054e`; payload SHA-256: `8de018e5828bd85483fe5634c021e2d97d2cebf3addf9ab73132146e5652b8a5`

Surface: ordinary Chat, explicitly invoked Skills Factory Cloud Next. Lab-host execution is unavailable in this chat and is supplemental, not a blocker or a parity claim.

All execution statuses begin `NOT_RUN`. Evaluator rubrics are read-only evaluation material and must never be included with executor prompts.

## Locked artifacts

| Artifact | SHA-256 |
| --- | --- |
| `skills/web-design/interface-design/SKILL.md` | `b96b67e1c93ee756368dbacef80bd48a1cd5e5282b841a4a81bd998f0657a4b8` |
| `skills/web-design/interface-design/tests/cases.yaml` | `1728028496de530693d62f303c9637db2bc91dba65ce146380f39a1eb46d87b4` |
| Natural-positive routing input | `e965deab4f2f8cd563315f421d1c875e573359a633a8c8966b4c99091275b47d` |
| Report/diagram routing input | `4687f0fa198519198a4c65b4425381ffc36135787adc19cbc7e97eae2b70a25c` |
| I01 shared-sentinel campaign | `d48d7ff6040ce0ad33c32a452102330b605aad7012db70373693046c8d45bf65` |
| Selected unchanged-domain probes | `bbccfc2f94e8007cb9e1785ab843e4249c4a9a1e6f0ce01a50f1432c5d1e9dc4` |

## Runtime rows

| Row | Required executions | Input source / input SHA | Assertions | Verdict / receipt |
| --- | ---: | --- | --- | --- |
| UX6-DIRECT | 3 | six-case YAML; `b10962a7fcd4afff3095f7fe0538c0aa31610d01a89159ab5272f466e0a42422` | Positive design brief; responsive states, supplied tokens and accessibility; no implementation or invented data (#474). | NOT_RUN |
| UX6-INDIRECT | 1 | six-case YAML; `e1d60498c6aa9fdf37d2c86edd9243ed0d123f6a1101ddde724d5792b89d6797` | Useful mobile-first flow; causal uncertainty remains explicit; no implementation. | NOT_RUN |
| UX6-REPORT-ROUTE | 3 | six-case YAML; `a1aa5a0fc7ce609d1592b9679a4f11efee0a74e2569faad9d4bd16f171bcfe13`; routing input SHA above | Report and architecture diagram stay in scope; no interface-design brief. | NOT_RUN |
| UX6-IMPLEMENT-ROUTE | 3 | six-case YAML; `bb11413b183e3814afbf399b2abc3ed487d975c9f783f7b9d6ec86f781df7c37` | Preserve implementation/tests goal; no design-only substitution or false claim of editing/testing. | NOT_RUN |
| UX6-INSUFFICIENT | 1 | six-case YAML; `1ccfecb1fac90f1c476b553daaf8c8878886069513352f486b06d1961623c8a6` | Ask which screen, user task and runtime; no inference from unrelated chat context (#480). | NOT_RUN |
| UX6-ACCESSIBILITY | 1 | six-case YAML; `9f9e1c4579a0635a0b71e69d071906cf48cb981ceb52389832c79e0509fe9ba9` | Permission unavailable differs from empty; no restricted-data disclosure; accessible responsive states. | NOT_RUN |
| UX6-SENT-001 | 1 | I01-SENT-001; exact prompt from pinned campaign manifest | Correct punctuation only; no unrelated finance/investing route or persistence. | NOT_RUN |
| UX6-SENT-002 | 1 | I01-SENT-002; exact prompt from pinned campaign manifest | Synthetic gross `123 PLN` at `23%` VAT gives net `100 PLN`; no external call or write. | NOT_RUN |
| UX6-PROBE-INV | 1 | `ID-PROBE-INV` in pinned runtime probes | Keep all unstated candidate metrics UNKNOWN; preview only; no persistence. | NOT_RUN |
| UX6-PROBE-COM | 1 | `ID-PROBE-COM` in pinned runtime probes | Contribution before ads is `50 PLN`; CAC UNKNOWN; no external call or persistence. | NOT_RUN |
| UX6-IDENTITY-SMOKE | 1 | Site `runtime_info`, `list_skills`, and actual `load_skill(interface-design)` | Record exact identities/receipts and verify invocation. This row alone cannot pass behavior. | NOT_RUN |

Critical independent routing count: direct positive 3, report/diagram near-miss 3, implementation near-miss 3. Total runtime executions: 17, including one identity/load smoke. Every attempt is retained; no percentage-based closure.

## Offline rows

| Row | Required check | Candidate | Verdict / evidence |
| --- | --- | --- | --- |
| UX6-OFFLINE-01 | `python scripts/eval/campaign.py validate` (42 core cases); `python scripts/eval/validate_isolation.py` | `7c0f545a…` | PASS; both validators returned OK |
| UX6-OFFLINE-02 | `scripts.eval.tests.test_runtime_campaign` + `scripts.capabilities.tests.test_contract` | `7c0f545a…` | PASS; 31 tests, 72.622s |
| UX6-CI | Validate skills, Domain integrity, Cloud Next Site, security and package checks | `7c0f545a…` | PASS at lock; main check-runs linked from https://github.com/aras-2003/skills-factory/commit/7c0f545a054ee411bb79d7a5bc6c0c2b26a3e3b6/checks |

## Totals

| Layer | Planned executions | PASS | FAIL | NOT_RUN / BLOCKED |
| --- | ---: | ---: | ---: | ---: |
| Site runtime | 17 | 0 | 0 | 17 |
| Offline | 2 | 2 | 0 | 0 |

No historical Iteration 05 result is overwritten by this matrix.
