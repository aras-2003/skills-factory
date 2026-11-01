# Supplemental Site v93 behavior check — 2026-11-01

This is Site-channel evidence for the `scan-opportunity-score-evidence-gate` case. It does not replace the Lab-channel test required by `source-coverage.yaml`; keep `runtime_status: NOT_RUN` and `release_approved: false` until that exact campaign is executed on Lab.

## Runtime and candidate identity

- Latest saved Site: v93; runtime attestation `verified`.
- Runtime: `1.38.415` (`1.38.415+510d83391153`).
- Canonical source / Lab revision: `510d8339115323d80578274b438b452bd2bd33f8`.
- Site MCP software/source revision: `c6f1c5268f60f3a550690d87672ba483e3c418bb`.
- `investment-opportunity-hunter` v0.5.1, content SHA-256 `fe9b8fc6d43af2a2a709186ccbaa6341b55fcab1eeddcdf593691abe81172d93`.
- `market-opportunity-scan` v0.4.1, content SHA-256 `ef794ab470721380ff7ac5cf4ddb60438b53f6e85520771b74346d730b267988`.
- `investment-record-store` v1.0.2, content SHA-256 `e320274edcb1a68927b587fbfcda2af57bf8eb418ee127a602641aff9b56a76a`.

## Exact-case outcome

Input: “Rank six stocks using the Opportunity Score across 1-3 months, 6-12 months and over 3 years. I have not supplied research data or factor evidence.”

The Site router selected `opportunity-hunter`; the host returned `NOT_SCORED` for all three horizons because no tickers or required factor inputs, source IDs, `as_of` date, or normalization profiles were supplied. It identified `opportunity-score-v0.1-provisional`, stated `score_is_probability=false`, did not rank or impute missing values, made no BUY claim, and returned `NOT_WRITTEN`. No portfolio or external research read occurred.

Result: PASS for the missing-evidence gate. This does not demonstrate differentiated scores, calibrated thresholds, ranking from a six-candidate evidence set, historical/OOS validity, canonical state reads, or the campaign's Lab execution. The Site tool receipts are unsigned and do not attest to the semantic host response.

## Six-candidate synthetic profile — Site supplement

A second isolated Site v93 run supplied six synthetic candidates and the complete factor profiles for all three horizons (18 candidate/horizon rows). The host routed through `opportunity-hunter` to `investment-opportunity-hunter`, then loaded `market-opportunity-scan`, `investment-record-store`, and `report-composer`. It made no record-store call and read no portfolio, canonical records, external research, or market data.

| Horizon | Provisional ordering (raw score) | Gated rows |
| --- | --- | --- |
| 1–3 months | event-driven .7820; MU-cycle .6855; quality-compounder .5755; cyclical-value-trap .3615 | negative-eps-no-fcf: `NOT_SCORED` (missing `valuation_expectations`); stale-consensus: `NOT_SCORED` (stale revisions) |
| 6–12 months | quality-compounder .6965; MU-cycle .5940; event-driven .5665; cyclical-value-trap .3860 | negative-eps-no-fcf: `NOT_SCORED` (missing `valuation_expectations`); stale-consensus: `NOT_SCORED` (stale revisions) |
| >3 years | quality-compounder .8100; stale-consensus .5600; MU-cycle .5540; event-driven .4560; cyclical-value-trap .3390 | negative-eps-no-fcf: `NOT_SCORED` (missing `valuation_expectations`) |

Every scored row was labeled provisional with `score_is_probability=false` and action `REVIEW_PROVISIONAL`. The stale-consensus candidate was blocked in shorter horizons but scored in >3 years, where estimate revisions are not a factor. The host did not impute missing values or renormalize absent factors. Its arithmetic was independently cross-checked against the source-pinned local deterministic engine; this is not independent market validation.

Result: PASS for supplied-input scoring, ranking, horizon-specific freshness gating, and provisional-action boundaries on this synthetic profile. This remains Site-only evidence; campaign `source-coverage.yaml` is still `NOT_RUN` because Lab execution, historical calibration, and out-of-sample evidence remain outstanding. The Site tool receipts are unsigned and do not attest to semantic host output.

Runtime was Site v93, attested `verified`, runtime `1.38.415`; canonical source/Lab revision `510d8339115323d80578274b438b452bd2bd33f8`; Site MCP source revision `c6f1c5268f60f3a550690d87672ba483e3c418bb`. Loaded skill content SHA-256 values are listed above for the first two skills; the run additionally loaded `report-composer` v0.12.1 (`0cdbab649bd1bc5cbb452420af8b493f11bf0b3c47b53a759972de8698048033`).
