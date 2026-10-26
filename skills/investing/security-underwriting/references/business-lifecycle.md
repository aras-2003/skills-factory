# Business Lifecycle Classification (Investment OS)

A deterministic five-phase research signal for equity underwriting:
`startup`, `hyper_growth`, `operating_leverage`, `capital_return`, `decline`.

## Execution
`python -m pytest tests/investing/test_business_lifecycle.py -q`

Use `FinancialPeriod` and `classify_lifecycle` from
`skills/investing/security-underwriting/scripts/business_lifecycle.py`.
Provide at least three **chronological, comparable and equally spaced** financial
observations (annual or TTM; don't mix with single quarters). Values must have
consistent units and accounting basis, and require reliable dated sources.

## Contract
Returns phase, phase affinity percentages, confidence, missing data fields,
calculated KPI evidence, and explicit limitations. Missing history yields
`INSUFFICIENT_DATA`. No database writes or external I/O occur.

**Affinity percentages are NOT calibrated probabilities.** No false certainty:
do not label a phase score "70% probability" until a historical labeled cohort,
out-of-sample validation, sector stratification and calibration diagnostics exist.
This is phase classification, not a transition forecast. Use margin trends, FCF,
net distributions and changing growth alongside segment-level interpretation.
Never equate a mature profitable issuer or buybacks alone with capital return.
The five-stage taxonomy is a useful heuristic, not a universal life-cycle law.

## Integration boundary
Security underwriting: run only after primary-source metric sanity gates.
Show the phase separately from equity valuation, thesis quality and portfolio fit.
Monitoring: compare results across dated observations and flag phase transition
for analyst review; do not auto-generate trading orders or infer certainty from
a score. Persistence belongs exclusively to `investment-record-store`, subject
to verified canonical `public` schema and explicit write authorization.
