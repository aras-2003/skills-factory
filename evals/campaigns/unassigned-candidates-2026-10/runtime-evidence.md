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
