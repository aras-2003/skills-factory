# Fundamental Intelligence (P1 core, not production)
Source-backed benchmark computations, not an LLM guessing ratios. Python 3.10+; `openpyxl` for XLSX. Run: `cd skills/investing/fundamental-intelligence && python -m unittest -v`.

Invariants: no fictitious Damodaran numbers, source dates checked for lookahead, no incompatible unit/definition comparisons, no silent missing-value fills. Parser uses explicit sheet/columns, source URL, SHA-256, cell coordinates and PROVISIONAL-by-default status. Damodaran industry averages **cannot** generate peer percentiles. A minimum of five real company observations is required.

This remains an implementation foundation, not a production data pipeline. **NOT YET IMPLEMENTED**: verified real 2026 Damodaran XLSX fixture/column map, annual ingestion job, release snapshots, Supabase migration/API, industry mapping, complete metric registry, validated production scoring profiles, downstream workflow wiring, runtime tests. Do not label this production ready. No portfolio state changes.

## Horizon-aware opportunity score (provisional v0.1)

`engine.py` also exposes `score_opportunity` for the pure aggregation layer
requested in #360. It consumes upstream normalized 0–1 factor values with
explicit definitions, source IDs, as-of dates, normalization-profile IDs,
quality and confidence. It does not fetch data, calculate valuation metrics,
choose peers, update the database, or issue trading instructions.

The versioned default weights are intentionally provisional:

| Horizon | Factor weights |
| --- | --- |
| 1–3 months | Catalyst timing 0.22; estimate revisions 0.18; valuation/expectations 0.15; price setup 0.15; scenario asymmetry 0.20; cycle resilience 0.10 |
| 6–12 months | Scenario asymmetry 0.23; valuation/expectations 0.22; estimate revisions 0.18; business quality 0.17; risk resilience 0.10; cycle resilience 0.10 |
| >3 years | Growth durability 0.24; business quality 0.22; reinvestment returns 0.18; valuation/expectations 0.16; balance-sheet resilience 0.10; cycle resilience 0.10 |

The raw score is `sum(weight × normalized factor)`; display rounding uses two
decimal places, while ranking uses the unrounded value. All weights are visible
in `HORIZON_WEIGHTS`. Any weight change requires a new model version. Confidence
is the factor-weighted mean of input confidence multiplied by an evidence
quality factor (VERIFIED 1.0, PROVISIONAL 0.7); completeness is the sum of
weights whose factors passed the evidence gate. The output contains exact
factor inputs, weights, contributions, source IDs, as-of, confidence and
completeness so the displayed rounded score can be reproduced.

The score is not a return probability. The five score bands follow the ticket's
provisional ranges; `PRIORITIZE`, `WATCH`, `DEPRIORITIZE`, and `REJECT` are
research-queue dispositions, never BUY/SELL decisions. Band and queue thresholds
are evaluated against the unrounded score. `PROVISIONAL` evidence
can produce only a review-required score, not a queue disposition. Missing,
stale, future-dated, invalid, or weak-confidence factors return `NOT_SCORED`;
the engine never renormalizes remaining weights or imputes the middle of the
scale. Ranking refuses to compare different model versions, as-of dates,
horizons, factor definitions or factor-normalization profiles. Scoreable rows
are sorted on the unrounded score; the audit reports the gap to the next row to
three decimals. `NOT_SCORED` rows stay in the result without a rank.

Unit tests include six explicitly synthetic profiles: a cyclicality example
named MU (no current MU facts), a quality compounder, an event setup, a cyclical
value trap, a negative-EPS/no-FCF case without a comparable valuation input, and
a stale-consensus case. These fixtures test horizons, ranking and failure gates;
they are not market data, historical calibration or investment conclusions.
Production use still requires real evidence inputs, sector-comparable
normalization, historical calibration, source/CI review, and runtime acceptance.
This slice consumes normalized factor scores; it does not yet implement source
ingestion or the normalization formulas. Scores can be compared only when the
normalization-profile IDs match exactly. Cross-sector risk adjustment,
historical stability/backtesting and sensitivity reporting on real as-of data
remain open before production use.
Portfolio overlap and position suitability are intentionally excluded from the
intrinsic candidate score. A separate portfolio-fit layer must use verified
holdings and report overlap without changing this score or implying a trade.

## Iteration 07 evidence audits (#318, #306)

The security-underwriting helper at
`skills/investing/security-underwriting/scripts/financial_quality.py` accepts caller-reviewed facts and computes explicitly
defined multi-period FCF, operating/gross margins, revenue and FCF growth where
comparable, FCF conversion, net debt, debt-due share, stock-compensation ratio,
share dilution and optional ROIC. It preserves revision history and each
reported optional fact's provenance instead of silently selecting a new value.
It expects three to five contiguous fiscal years plus current/prior same-quarter
YTD; missing, conflicting, future-published, mixed-basis or mixed-currency
inputs block dependent outputs. It scales units but performs no FX conversion,
source retrieval, canonical writes or investment recommendation. Banks, insurers
and ETFs require their own accounting/provider path.

The valuation helper at
`skills/investing/valuation-scenario-review/scripts/peer_comparison.py` builds
a reproducible peer table and the exact snapshot consumed by the optional PEG
reference plot (`scripts/peer_growth_plot.py`). A peer is
included only for matching sector, industry, business model and as-of date.
Metric definition, period, basis, unit, currency and forecast horizon must also
match. Forward estimates older than 90 days, lookahead, or nonpositive EPS
growth produce N/M. A compact table requires three compatible peers; percentiles
require five and remain descriptive. PEG=1 is a heuristic reference, never a
buy signal or cross-sector rank. Plot generation uses table snapshot data only;
it neither fetches nor repairs inputs.

Consensus revisions, historical multiples, FCF yield, capital intensity and
cycle-normalized measures may be compared only when supplied with a consistent
definition, period, basis, unit, currency and source. Missing provider data stay
N/M. Cyclical issuers can be explicitly flagged; ticker identity never guesses
cyclicality. These helpers do not independently calculate consensus history,
historical valuation, or calibrated peer scores.

These helpers are local calculations, not a verified runtime capability or
production data pipeline. If the selected runtime cannot execute the packaged
code, use the stated gates and formulas manually and do not claim the helper ran.
All fixtures are synthetic. No market conclusion is implied.
