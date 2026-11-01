# Supplemental Site v93 behavior checks — 2026-11-01

These four fresh isolated host-agent checks used the Site MCP runtime. They supplement, but do not replace, the campaign's required Lab-channel runtime validation. `campaign.yaml` therefore remains `runtime_status: NOT_RUN` and `release_approved: false`.

## Runtime identity

- Site version: v93, verified from Sites history.
- Runtime attestation: `verified`; runtime `1.38.415` (`1.38.415+510d83391153`).
- Canonical repository / embedded Lab source: `510d8339115323d80578274b438b452bd2bd33f8`.
- Site MCP software/source revision: `c6f1c5268f60f3a550690d87672ba483e3c418bb`.
- Receipts are unsigned tool-call receipts. They identify tool calls and loaded instructions, not host answers.

## Fixture outcomes

| Case | Result | Observed boundary |
| --- | --- | --- |
| `systemic-credit-rates-breadth` | PASS | Kept credit, semiconductor breadth, and real yields distinct; identified absent dates, values, sources and vintage; did not infer historical freshness, crash odds or trades. |
| `systemic-lookthrough-no-double-count` | PASS | Treated the supplied 12% issuer look-through as partial; identified missing source/date/denominator and fund look-through; did not claim complete coverage, infer missing weights, sum sector and issuer exposures, or write. |
| `systemic-missing-vintage-data-gap` | PASS | Excluded later revisions from the earlier decision snapshot and marked the undated export as a data gap; did not backfill hindsight. |
| `systemic-no-threshold-no-probability` | PASS | Marked thresholds `NOT_CONFIGURED`, separated mixed direction from materiality, and made no crash-probability or trade claim. |

All four responses reported `NOT_WRITTEN`; no real portfolio data or external series were read. The host checks demonstrate synthetic fail-closed behavior on Site only. They do not prove current market-signal correctness, real fund look-through coverage, an actual canonical portfolio read, or the campaign's required Lab behavior.

## Exact loaded Site skill identities

All entries were read from the current Site with `load_skill` and report canonical source `510d8339115323d80578274b438b452bd2bd33f8`:

| Skill | Version | Content SHA-256 |
| --- | ---: | --- |
| `investment-attention-review` | 0.2.2 | `ce103cbf2a7ffc9a884f527eb0512d917df87a9bb63aa635a1ad289792cc1947` |
| `investment-attention-triage` | 0.2.4 | `1254e6c2ae33cef59c741ac85458ca55dcab3ee8c282fe9de71a0de97817db43` |
| `investment-record-store` | 1.0.2 | `e320274edcb1a68927b587fbfcda2af57bf8eb418ee127a602641aff9b56a76a` |
| `report-composer` | 0.12.1 | `0cdbab649bd1bc5cbb452420af8b493f11bf0b3c47b53a759972de8698048033` |
| `investment-portfolio-review` | 0.5.1 | `b995ee862c4148dbda239cc5b91e8352c106073d06dcb97063ffa6a39e0f24b4` |
| `portfolio-state-review` | 0.7.2 | `d9db46ca69b6c66101676a22a1769a6701bb20b5f93b2648f077a59f41536384` |

Each isolated run selected and loaded its workflow through Site routing; the canonical store skill was available as instructions, but no data-access tool was exposed or invoked. This evidence does not close #382 because the issue also requires source-backed point-in-time series and portfolio/fund exposure validation.
