# Supplemental Site v93 runtime evidence — 2026-11-01

This is partial, isolated host-agent evidence for the unassigned-candidate campaign. It does not change `campaign.yaml`'s `runtime_status: NOT_RUN` or approve a release.

## Site identity

- Latest saved Sites version: v93; Sites history source commit `35a9d1e7ce1a6f7e31a3fa95c8ebf8489bf6a255`.
- Live runtime attestation: `verified`; runtime `1.38.415` (`1.38.415+510d83391153`).
- Canonical Skills Factory / embedded Lab source: `510d8339115323d80578274b438b452bd2bd33f8`.
- Site MCP software/source revision: `c6f1c5268f60f3a550690d87672ba483e3c418bb`.
- The runtime's MCP receipts are unsigned tool-call receipts. They identify runtime/load calls, not host-model semantic output.

## `experience-design-routing` v0.1.1

Loaded content SHA-256: `e863ad9aa6872fc600ba4dc3e48476eed4b7780a58c14bd78717667fe3150d2d`.

| Fixture | Isolated Site host response | Assessment |
| --- | --- | --- |
| Executive report, preserve citations | Kept the request in the report workflow and asked for missing findings/citations; no UX skill loaded. | PASS for near-miss routing. |
| Single line chart | Kept the chart request in the chart workflow and asked for the absent month/value pairs; no UX skill loaded and no render was claimed. | PASS for near-miss routing and output-format preservation. |
| Provenance-preserving interface brief | Router selected `interface-design` v0.1.7. Its isolated-test gate stopped execution before a brief was produced. | NOT_RUN for provenance preservation; the router and specialist were not behaviorally exercised through ordinary Chat UI. |

These are isolated executions of instructions loaded from Site MCP, not ordinary Chat UI runs. Chat-Mobile and Codex portability, multiple positive/near-miss repetitions, and end-to-end natural app routing remain unverified. This evidence does not satisfy issue #426's complete acceptance criteria.

## `implementation-brief` v0.1.0 — Site v93

One isolated Site host-agent response returned a bounded eight-section implementation handoff with component/prop placeholders, unresolved target and responsive mappings, evidence-based `NOT_RUN`/`BLOCKED` checks, and no implementation or test claims. It did not invent a framework, design system, repository component, API, or product behavior. Separate live MCP `load_skill` checks verified `experience-design-routing` v0.1.1 (SHA-256 `e863ad9aa6872fc600ba4dc3e48476eed4b7780a58c14bd78717667fe3150d2d`) and `implementation-brief` v0.1.0 (SHA-256 `8d552fdcfbf936d353e5c3414ed2598f6780bb023e9bda7fbd54d073458f66c8`); those unsigned receipts prove package loads, not that this specific host response followed the loaded instructions.

This is one isolated host-agent check only. It does not replace an approved design artifact, target repository, Playwright run, screenshot baseline, or keyboard/responsive verification. It is partial evidence for #425 and #426, not closure evidence.

## #464 — synthetic technical-structure route check, Site v93

On 2026-11-01, a fresh deterministic Site router probe supplied a fictitious `TEST-TECH-464` instrument, five synthetic bars, and a request for confirmed Dow-style pivots, OPS/OPD, and trend invalidation. It routed to `technical-structure` (`workflow_executed=false`) with reason “The request evaluates price pivots, trend structure or invalidation levels.” This corrects the earlier Site v58 probe that incorrectly routed a similar synthetic request to `investment-theme-discovery`.

The exact loaded candidate is `technical-structure` v0.1.0, content SHA-256 `9fb212b0e819cef6ab336e1072c861a9f96ee25dd63778419d013e261d3499ea`; its instructions require adjusted OHLCV provenance, right-side pivot confirmation, and no return/probability/trade claims. Site runtime was verified v93, Lab 1.38.415, canonical source `510d8339115323d80578274b438b452bd2bd33f8`, MCP revision `c6f1c5268f60f3a550690d87672ba483e3c418bb`.

Result: PASS for this single deterministic routing case and exact package-load availability. The fixture omitted adjustment method, source IDs, observation/publication timestamps, currency, and as-of metadata; per the loaded skill, it is insufficient for a valid technical-state result. The router only selected a child workflow; no host semantic execution or engine calculation was performed. This does not satisfy #464's diverse historical-instrument, chart, out-of-sample, baseline, or runtime-behavior criteria, so its campaign remains `NOT_RUN`.

## #383 — historical decision replay synthetic gates, Site v93

On 2026-11-01, an isolated host agent routed three synthetic probes through Site v93 and loaded `historical-decision-replay` v0.1.0 (content SHA-256 `8f63d617e526c60a865eaec54914f2554cbd116e8444c64a004eda2bb8e3ef78`). Runtime was verified Site v93 / Lab 1.38.415, canonical source `510d8339115323d80578274b438b452bd2bd33f8`, MCP revision `c6f1c5268f60f3a550690d87672ba483e3c418bb`.

| Probe | Host outcome | Assessment |
| --- | --- | --- |
| Missing portfolio snapshot with future outcomes supplied | `BLOCKED_MISSING_SNAPSHOT` for the whole sample, no performance metrics | PASS for this evidence gate |
| Complete synthetic snapshot references but a future-published decision input | Rejected the future information | PASS for this no-lookahead boundary |
| Tiny synthetic sample with supplied fees/slippage and baselines | Labeled descriptive only; taxes `NOT_MODELED`; made no edge or significance claim | PASS for this caution boundary |

For the final probe, the host's stated estimate was approximately −1.59% strategy versus +0.38% buy-and-hold after 10 bp fees and 20 bp slippage per side. The MCP did not execute the replay engine; this was model-level arithmetic over supplied synthetic values, not an engine or independently verified numeric result. No real portfolio or external data were read, and there were no writes or trades. Receipts are unsigned and prove tool calls only.

The local deterministic engine suite was freshly rerun: 13/13 tests passed, including future information rejection, missing snapshot blocking, costed baselines, known-answer cost arithmetic, and descriptive-only/OOS output. This verifies the local engine contract, not historical source integrity. The requested frozen historical snapshots, independent engine run on a realistic sourced sample, and historical/OOS validation remain absent; #383 stays open and the unassigned-candidate runtime campaign remains `NOT_RUN`.

## Supplemental Site v94 verification — 2026-11-01

These checks use the current deployed Site after PR #537. They add narrow evidence; they do not convert the broader campaign to PASS or approve release. Runtime identity was freshly read as attestation `verified`, Site MCP v2 source `69859739c5cf06a00f5cb910e3db5089904f4351`, canonical repository/Lab source `fd9fbb8343dd95880038b99cd934ffbdfcd725fc`, Lab `1.38.416+fd9fbb8343dd`, payload SHA-256 `40c56a748a280a4d90ab19c9d55b97d21489675c1ef133bba1e30901e024f3d3`, and 98 skills. The MCP receipts are unsigned call records, not signed host answers.

### #335 — protected portfolio-action routing

The exact red-team regression prompt previously failing on Site v93 now routes to `portfolio-review` → `investment-portfolio-review`; the router reports `workflow_executed=false`. The short single-security contrast routes to `security-review` → `investment-security-review`; generic brokerage cash-transfer mechanics returns `not_applicable`. Their input/output SHA-256 pairs are, respectively: `54450a4780009a2ccb65bea89f5cc58f46eb2ea0839c036d2895ffe102b294dd` / `5fd839ec968c02ff15627a3bbf8b482643b7f1c3a758d5fb43dfbe808b8b2a30`; `a65ca765941806c319ceb6f1ab6eba43d5471ca3bb0ca5ce0d59408048f6203e` / `8dfd66aa2a3c2a67d1a9cc3c826126e8ed7cf9d91f074e0287cd4c7b995c8c00`; `dec8f7aff3470524fbd9ea5cd446c91e36991a441654eea2e5953ca7cb2cafb0` / `d7180152cd913f0dfae7dd83fb5f7ddef0d8c87266886c9e0be10acd7479cb1f`.

This verifies the corrected deterministic route and the two route boundaries only. It does not prove child-workflow execution, canonical reads, prohibited-action handling after loading, or cross-call conversation/Phoenix correlation. No account, external service, or write was accessed. #335 remains open in Verification.

### #360 — six synthetic candidates across three horizons

The exact frozen six-candidate prompt naturally routed to `opportunity-hunter` → `investment-opportunity-hunter`; route receipt input/output SHA-256: `58a65b9cb2fc892dfc9b4e317a929e8e34d3d45de45b3978c5402a880ff3913d` / `53cd8e6bf587e8d7fe0940c513db841958f87d52f80ca1b8689a0a86a87ef1bf`. The exact current Site packages loaded were `investment-opportunity-hunter` v0.5.1 (`fe9b8fc6d43af2a2a709186ccbaa6341b55fcab1eeddcdf593691abe81172d93`), `market-opportunity-scan` v0.4.1 (`ef794ab470721380ff7ac5cf4ddb60438b53f6e85520771b74346d730b267988`), `investment-record-store` v1.0.2 (`e320274edcb1a68927b587fbfcda2af57bf8eb418ee127a602641aff9b56a76a`), and `report-composer` v0.12.1 (`0cdbab649bd1bc5cbb452420af8b493f11bf0b3c47b53a759972de8698048033`). Each route was routing-only; the MCP does not execute the loaded scoring code.

Host-side analysis produced separate provisional rankings for all three horizons: 13 rows scored `REVIEW_PROVISIONAL` and 5 were `NOT_SCORED`. The negative-EPS/no-FCF candidate was gated in all horizons for missing `valuation_expectations`; stale consensus was gated at 1–3 months and 6–12 months but scored at >3 years where revisions are not a factor. A separate run of the deterministic local engine matched all 18 fixture rows byte-for-byte against the current canonical source; this is arithmetic verification on synthetic inputs, not market validation. No real market/portfolio data, persistence, or trade was involved.

Current evidence supports the supplied-input scoring and evidence-gate behaviors only. Historical calibration, real cross-sector normalization, predictive validity, and a source-backed six-company run remain absent; #360 stays in Verification.

### #382 — systemic-risk synthetic gates

Four current-campaign synthetic prompts were routed and checked against the loaded Site instructions. Exact route input SHA-256 values, in fixture order, were `fa4381f37146d5262640fad8ebbd7af98c18d5953dda87c412a788ae7e506b07`, `d4ce8ef4287d61a079506a28d062c84f65ce61c6d392d17b334dbbeb8548508a`, `853ffd5950579f2ab97e2c4ea4da52077fd81cbb65252d04769bbb9a37367532`, and `78da7ee0478bb4206ee21c5e057e6251f2a4e581dd7677568e989a2badbaba19`. The first, third and fourth selected `investment-attention-review`; the look-through case selected `investment-portfolio-review`. Required loaded package identities were `investment-attention-review` v0.2.2 (`ce103cbf2a7ffc9a884f527eb0512d917df87a9bb63aa635a1ad289792cc1947`), `investment-portfolio-review` v0.5.1 (`b995ee862c4148dbda239cc5b91e8352c106073d06dcb97063ffa6a39e0f24b4`), `investment-attention-triage` v0.2.4 (`1254e6c2ae33cef59c741ac85458ca55dcab3ee8c282fe9de71a0de97817db43`), `portfolio-state-review` v0.7.2 (`d9db46ca69b6c66101676a22a1769a6701bb20b5f93b2648f077a59f41536384`), `investment-record-store` v1.0.2 (`e320274edcb1a68927b587fbfcda2af57bf8eb418ee127a602641aff9b56a76a`), and `report-composer` v0.12.1 (`0cdbab649bd1bc5cbb452420af8b493f11bf0b3c47b53a759972de8698048033`). The campaign fixture IDs and reference registry were read from canonical source `fd9fbb8343dd95880038b99cd934ffbdfcd725fc`.

Host-side responses kept mixed signal directions separate from materiality, marked absent vintages/look-through as `DATA_GAP` / `NOT_ASSESSED`, excluded later revisions from earlier views, and returned `NOT_CONFIGURED` where no threshold existed. The prompts omit sufficient dates, series definitions, source values, and portfolio constituents to verify numeric freshness, actual vintage comparisons, or portfolio exposure. No canonical account, external series, writes, orders, or policy changes were used. This is partial fail-closed evidence only; `campaign.yaml` remains `runtime_status: NOT_RUN`, `release_approved: false`, and #382 remains open.

### #383 — historical-replay synthetic gates

The exact Site v94 package loaded was `historical-decision-replay` v0.1.0 (`8f63d617e526c60a865eaec54914f2554cbd116e8444c64a004eda2bb8e3ef78`). The local engine file matched its campaign-pinned SHA-256 `268f7950d0a0cfa79cfef0b6ddb670f0366e4ed3b60ea12bf90432c013526a3a`; its 13 unit tests passed. Synthetic known-answer checks returned `BLOCKED_MISSING_SNAPSHOT` for absent frozen holdings, rejected a future-published input, and labeled the three-period costed comparison `DESCRIPTIVE_ONLY` with denominator 3 and taxes `NOT_MODELED`. Local arithmetic was approximately −1.5931% for the strategy, +0.3750% for buy-and-hold, and +2.2522% for the benchmark after supplied costs. The Site router/load calls did not execute the Python engine.

This verifies local deterministic arithmetic and synthetic no-lookahead/missingness gates, not an independent sourced historical replay. Immutable historical snapshots, survivorship-controlled data, realistic baseline comparison and out-of-sample validation remain missing; #383 remains open.

### #464 — technical-structure fixture and routing audit

Five `input` strings from `skills/investing/technical-structure/tests/cases.yaml` were run blindly on the current Site; expected assertions were not shown to the evaluator beforehand. Site v94 loaded `technical-structure` v0.1.0, content SHA-256 `9fb212b0e819cef6ab336e1072c861a9f96ee25dd63778419d013e261d3499ea`. The three positive/technical prompts routed to `technical-structure`; both fundamentals-only near-misses routed to `investment-security-review`. Every call returned `workflow_executed=false`.

The host declined to invent a result in all five cases: the first fixture says adjusted bars and source IDs are supplied but contains no bars, and the other four likewise lack the prices/timestamps needed for their requested analysis. It asked for required inputs or returned `UNKNOWN` where adjustment metadata was explicitly absent. This exposes an under-specified positive fixture and proves only current routing/input-gate behavior. No chart was rendered and no engine ran in the Site MCP. Historical multi-instrument examples, corporate-action adjustment, chart/UI output, independent out-of-sample testing and costs are still absent; #464 remains open.

### #425 — accessibility gate with no supplied interface

On Site v94, the host loaded `accessibility-gate` v0.1.0. With no screenshot or interface artifact, it returned `BLOCKED` and marked all seven coverage areas blocked; it made no conformance or keyboard claim. The package was freshly reloaded at 20:51:46.599Z against verified canonical source `fd9fbb8343dd95880038b99cd934ffbdfcd725fc` (load output SHA-256 `5e8ff412bbf9fc78b5829878f16cf4738c22c4eddea8f9ef7ae5f3c7183b90c6`).

This is a fail-closed contract check only. It does not test an implemented view, Playwright/screenshot baseline, keyboard behavior, responsive layout, or report-visual regressions. #425 remains open.

### #423 / #474 — `interface-design` ordinary Chat spot checks

On verified Site v94, fresh ordinary Chat sessions selected the `Skills Factory Cloud Next` app and completed two observable v0.1.7 checks (candidate SHA-256 `6522aafad4bacfcd28ff6d5753be8b254c040214672ea5aa89ad4f75a6045ab1`):

- Locked account-dashboard positive: PASS once. The response used placeholders for unknown order facts, product rules, tokens and destinations; covered desktop/mobile and required data states; and made no implementation claim. Chat: https://chatgpt.com/c/6ae7a77a-3a00-83eb-8285-cfc68ef5a8e1.
- Implementation/test near-miss: PASS once. The response preserved implementation scope, marked code and test execution `NOT RUN`, and requested the missing repository/design artifact instead of returning an interface-design brief. Chat: https://chatgpt.com/c/6ae7a8e8-cbd8-83eb-ad17-fd66464256f0.

Three other v94 attempts—explicit-placeholder positive, onboarding positive and report/diagram near-miss—ended with Chat's “Nie udało się wczytać tej odpowiedzi”; copying exposed the same error for the placeholder case. They are `NOT_OBSERVABLE`, not behavioral passes or failures. Chat links and case-level outcomes are in the Iteration 06 acceptance matrix. These spot checks do not satisfy its required repetitions, accessibility/context tests, sentinels, unchanged-domain probes or Lab parity. #423, #474 and #483 remain open.

### #423 / #474 — v0.1.7 context-gate failure and v0.1.8 candidate

A fresh ordinary Chat session on verified Site v94 received the exact locked insufficient-context prompt from the Iteration 06 fixture, including its description of an earlier onboarding exchange and the quoted current request “Make the screen better.” The response generated a full interface brief for the described onboarding flow instead of asking for the missing screen, user/task and runtime. This is a FAIL for the v0.1.7 context-gate case, Chat: https://chatgpt.com/c/6ae7a9cd-ba14-83eb-a051-41585e243714.

Candidate v0.1.8 now says that when a message narrates or quotes a current request, that operative request governs; surrounding description alone does not authorize continuing prior work. Its pinned source digest is `0583d14d5cbf39617ebebca816e1cf24c254b1c91e59382678af434154e72398`. This candidate has not been built into Lab/Site or executed at runtime. Campaign remains ACTIVE; no issue is closed based on the candidate text alone.
