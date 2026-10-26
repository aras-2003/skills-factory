# Iteration 05 acceptance matrix — interface-design

Candidate baseline: canonical Skills Factory main `508f35cdba43e2f93a231ae6f828d46b70534ba9`; candidate skill content SHA-256 `b6bd50e5afc710e2fd585a78ab2da7ed843fa2692ac76e17d1c29acb8f9b8b8d`.

Run each row on Lab and Site independently. `C1` requires the exact same release, source revision and payload on both. Do not mark rows PASS based on a matching version string, direct package load, source CI, or an unobserved tool invocation. Lab runtime currently reports 1.38.354 and Site embeds 1.38.360; therefore `ID-SAME-CANDIDATE` is presently BLOCKED.

| Row ID | Issue / criterion | Layer + case ID / definition | Required | Candidate / surface | Input / rubric source | Planned runs | State / verdict | Receipt / reviewer |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| ID-OFFLINE-01 | #423 AC-01 | `python scripts/eval/campaign.py validate` | Yes | C1 / local | campaign + case manifest | 1 | NOT_RUN | — |
| ID-OFFLINE-02 | #423 AC-01 | `python scripts/eval/validate_isolation.py` | Yes | C1 / local | campaign executor/evaluator separation | 1 | NOT_RUN | — |
| ID-OFFLINE-03 | #423 AC-01 | interface-design campaign + skill contract unit tests | Yes | C1 / local | `scripts/eval/tests/test_runtime_campaign.py`; `scripts/capabilities/tests/test_contract.py` | 1 | NOT_RUN | — |
| ID-OFFLINE-04 | #423 AC-01 | final-main Validate skills, Domain integrity, packaging, security and applicable eval CI | Yes | exact merged main SHA | #423 and campaign | all applicable jobs | NOT_RUN | — |
| ID-IDENTITY-LAB | #423 AC-05 | `runtime_info` plus `list_skills`; record package integrity, release/source/payload/catalog and host attestation | Yes | Lab | actual tool receipt | 1 | PASS (identity only; package is not C1) | `runtime_info` 2026-10-26T23:13:10.953Z reports Lab 1.38.354, source 6dcbd09a…, payload 2596fa5…, integrity verified; host unattested. Not behavior acceptance. |
| ID-IDENTITY-SITE | #423 AC-05 | `runtime_info` plus `list_skills`; record Site attestation, canonical revision and embedded Lab release separately from platform mirror tag | Yes | Site | actual tool receipt | 1 | PASS (identity only; platform mirror tag stale) | Site 2026-10-26T23:13:08.365Z: attested, canonical SHA 508f35c, embedded Lab 1.38.360 payload 4c3f8ff; platform tag still 8f6cf96d. |
| ID-SAME-CANDIDATE | #423 AC-05 | Lab and Site release ID, source SHA and payload digest all equal C1 | Yes | Lab + Site | both runtime_info receipts | 1 | BLOCKED | Lab must be updated to 1.38.360+508f35cdba43; no parity claim while bytes differ. |
| ID-LOAD-LAB | #423 AC-05 | actual `load_skill(interface-design)` and host response under loaded candidate | Yes | C1 / Lab | ordinary Chat positive prompt | 1 | NOT_RUN | — |
| ID-LOAD-SITE | #423 AC-05 | actual `load_skill(interface-design)` and host response under loaded candidate | Yes | C1 / Site | ordinary Chat positive prompt | 1 | PASS (load only) | Chat shows Skills Factory Cloud Next invoked; response identifies skill v0.1.0 Candidate, source 508f35cd. Behavior verdict is recorded separately as FAIL. https://chatgpt.com/c/6adfe192-4ac4-83eb-b795-28e99b6a143f |
| ID-DIRECT-LAB | #423 AC-03/04 | `interface-design-direct-positive` | Yes | C1 / Lab | `skills/web-design/interface-design/tests/cases.yaml` | 1 | NOT_RUN | — |
| ID-DIRECT-SITE | #423 AC-03/04 | `interface-design-direct-positive` | Yes | C1 / Site | same case manifest | 1 | FAIL | 2026-10-26 23:29 UTC; input SHA `a6a8d0b380229d6da30279ffbc1a71d15ceadb7fe0acba1fa454b275d628cd2a`; answer accessibility-tree SHA `1e814251425793b5e7497aa3f918d3c0e435c86e7bdb0383f1fe2947d56132ad`; chat https://chatgpt.com/c/6adfe192-4ac4-83eb-b795-28e99b6a143f. Invented order IDs, status/count/timing data violate the frozen must-not assertion despite a synthetic-data disclaimer. See #474. |
| ID-INDIRECT-LAB | #423 AC-03/04 | `interface-design-indirect-positive` | Yes | Lab | same case manifest | 1 | NOT_RUN | — |
| ID-INDIRECT-SITE | #423 AC-03/04 | `interface-design-indirect-positive` | Yes | Site | same case manifest | 1 | NOT_RUN | — |
| ID-NEAR-REPORT-LAB | #423 AC-02/03 | `interface-design-nearmiss-report-diagram` | Yes | Lab | same case manifest | 1 | NOT_RUN | — |
| ID-NEAR-REPORT-SITE | #423 AC-02/03 | `interface-design-nearmiss-report-diagram` | Yes | Site | same case manifest | 1 | NOT_RUN | — |
| ID-NEAR-IMPLEMENT-LAB | #423 AC-02/03 | `interface-design-nearmiss-implementation` | Yes | Lab | same case manifest | 1 | NOT_RUN | — |
| ID-NEAR-IMPLEMENT-SITE | #423 AC-02/03 | `interface-design-nearmiss-implementation` | Yes | Site | same case manifest | 1 | NOT_RUN | — |
| ID-CLARIFY-LAB | #423 AC-03/04 | `interface-design-insufficient-context` | Yes | Lab | same case manifest | 1 | NOT_RUN | — |
| ID-CLARIFY-SITE | #423 AC-03/04 | `interface-design-insufficient-context` | Yes | Site | same case manifest | 1 | NOT_RUN | — |
| ID-ACCESSIBILITY-LAB | #423 AC-03/04 | `interface-design-accessibility-edge` | Yes | Lab | same case manifest | 1 | NOT_RUN | — |
| ID-ACCESSIBILITY-SITE | #423 AC-03/04 | `interface-design-accessibility-edge` | Yes | Site | same case manifest | 1 | NOT_RUN | — |
| ID-ROUTE-POS-LAB | #423 AC-02 | `interface-design-screen-natural-en` | Yes | Lab | input `evals/routing/web-design-interface-design-natural-en.input.md`; rubric `...natural-en.rubric.yaml` | 3 | NOT_RUN | — |
| ID-ROUTE-POS-SITE | #423 AC-02 | `interface-design-screen-natural-en` | Yes | Site | same input/rubric | 3 | NOT_RUN (1/3 observed routing PASS) | One invocation selected Cloud Next and loaded the candidate. Two independent attempts remain; chat link and hashes are in ID-DIRECT-SITE. |
| ID-ROUTE-REPORT-LAB | #423 AC-02 | `interface-design-report-nearmiss-en` | Yes | Lab | input `evals/routing/web-design-interface-design-report-nearmiss.input.md`; rubric `...report-nearmiss.rubric.yaml` | 3 | NOT_RUN | — |
| ID-ROUTE-REPORT-SITE | #423 AC-02 | `interface-design-report-nearmiss-en` | Yes | Site | same input/rubric | 3 | NOT_RUN | — |
| ID-ROUTE-IMPLEMENT-LAB | #423 AC-02 | Natural implementation request must remain an implementation task, not select design-only brief | Yes | Lab | `Implement the approved checkout design in the existing React app, run the tests, and fix responsive runtime errors.` | 3 | NOT_RUN | — |
| ID-ROUTE-IMPLEMENT-SITE | #423 AC-02 | Same natural implementation near-miss | Yes | Site | same input | 3 | NOT_RUN | — |
| ID-SENT-001-LAB | #423 AC-06 | I01-SENT-001 punctuation-only edit; no unrelated routing or persistence | Yes | Lab | `evals/campaigns/iteration-01-safety-governance-2026-10/campaign.json` | 1 | NOT_RUN | — |
| ID-SENT-001-SITE | #423 AC-06 | Same I01-SENT-001 | Yes | Site | same manifest | 1 | NOT_RUN | — |
| ID-SENT-002-LAB | #423 AC-06 | I01-SENT-002 synthetic 123 PLN gross at 23% VAT = 100 PLN net; no external call/write | Yes | Lab | same campaign manifest | 1 | NOT_RUN | — |
| ID-SENT-002-SITE | #423 AC-06 | Same I01-SENT-002 | Yes | Site | same manifest | 1 | NOT_RUN | — |
| ID-PROBE-INV-LAB | #423 AC-06 | unchanged Investment Opportunity Hunter synthetic candidate probe; preserve UNKNOWN, preview only | Yes | Lab | `scripts/package/tests/test_investment_runtime.py::test_candidate_screen_is_not_misrouted_by_incidental_xtb_history` | 1 | NOT_RUN | — |
| ID-PROBE-INV-SITE | #423 AC-06 | Same synthetic Investment Opportunity Hunter probe | Yes | Site | same input | 1 | NOT_RUN | — |
| ID-PROBE-COM-LAB | #423 AC-06 | unchanged unit-economics capability on supplied synthetic inputs only | Yes | Lab | `Synthetic order: net sales 100 PLN, landed product cost 30 PLN, fulfillment 12 PLN, payment fee 3 PLN, return allowance 5 PLN. Calculate contribution before ads and state CAC is UNKNOWN. Use no external calls.` | 1 | NOT_RUN | — |
| ID-PROBE-COM-SITE | #423 AC-06 | Same synthetic unit-economics probe | Yes | Site | same input | 1 | NOT_RUN | — |
| ID-ISSUE-CLOSE | #423 AC-07 | Verify all required rows, update #423 to Done only after PASS; record candidate and residual risk | Yes | final candidate | matrix + issue state | 1 | NOT_RUN | — |

## Input, rubric and candidate digests

| Artifact | SHA-256 |
| --- | --- |
| Candidate skill content | `b6bd50e5afc710e2fd585a78ab2da7ed843fa2692ac76e17d1c29acb8f9b8b8d` |
| Skill content file | `86199a9301be1bef6b28c61c8e6337ee22e409c87c01cd4edc63d05ec2286e9c` (packaged content digest recorded separately as `b6bd50e5afc710e2fd585a78ab2da7ed843fa2692ac76e17d1c29acb8f9b8b8d`) |
| Existing campaign YAML | `416a775d8253797c2ac6ea580a4cd62cb99953cc8273e6cddd288a634b02aa90` |
| Six-case YAML | `a546d3555d9101c3e7be5adfb945763b662e55514f42b095c61f3b835ded1b30` |
| Natural positive input | `e965deab4f2f8cd563315f421d1c875e573359a633a8c8966b4c99091275b47d` |
| Natural positive rubric | `95f9134ee89f347f36064b0ebf049c1116d3a54a8cbc3026f9a3c301a28070b5` |
| Report near-miss input | `4687f0fa198519198a4c65b4425381ffc36135787adc19cbc7e97eae2b70a25c` |
| Report near-miss rubric | `113b2defd8573e15a94d18bc5570498aa0216645cf0e835632620f8785f11147` |
| Shared sentinel campaign manifest | `d48d7ff6040ce0ad33c32a452102330b605aad7012db70373693046c8d45bf65` |
| Iteration runtime probes | `bbccfc2f94e8007cb9e1785ab843e4249c4a9a1e6f0ce01a50f1432c5d1e9dc4` |

## Execution totals

| Layer / surface | Distinct scenarios | Planned executions | PASS | FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | N/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Offline | 4 | 4 plus exact-main CI jobs | 0 | 0 | 4 | 0 |
| Lab | 15 | 21 | 0 | 0 | 21 | 0 |
| Site | 15 | 21 | 0 | 0 | 21 | 0 |
| Total runtime | 30 | 42 | 0 | 0 | 42 | 0 |

Critical route prompts are run three independent times per surface. Keep every attempt and do not retry until green. Evaluator rubrics remain outside executor context. Direct package-load receipts and these identity observations do not count as behavior execution.
