# Investment specialist exchange v1

The v1 exchange is internal to one Investment OS analysis. It does not create a
new database or user-facing recommendation API. Its schemas are strict JSON
shape contracts; `scripts/investing/investment_contracts.py` adds cross-document
checks that JSON Schema cannot express. A passing validator does not authenticate
an external source, independently prove a source digest, execute a skill, or
establish a recommendation's quality.

## Ownership and consumer map

| Data | Owner | Consumer | Boundary |
| --- | --- | --- | --- |
| `AnalysisContext` | `investment-os-review` / `investment-security-review` | Requested specialists | One canonical instrument ID, analysis ID, horizon and UTC cutoff are shared. Missing policy/portfolio is never inferred. |
| `SpecialistResult` | The producing skill | `investment-security-review` synthesizer | Producer owns its method, formula, interpretation, limitations and claim IDs. Consumers hold immutable references. |
| Evidence snapshot | Existing evidence retrieval/source owner | Producer and validator | Source ID and digest are identifiers/assertions. Source authenticity and license are not established by this offline validator. |
| Investment decision | `investment-security-review` | Proposed one-way #297 reporting mapping | Diagnostic/advisory output only. It cannot mutate producer results or authorize an action. |
| Persisted thesis/portfolio state | `investment-record-store` | Authorized existing workflows | No access or write occurs through these contracts. A separate approved store operation remains mandatory. |

`#297` (DomainResult) remains an output/reporting boundary. If the existing
report composer consumes an investment decision later, map stable finding,
metric, evidence and source-result IDs one-way. Do not clone `DomainResult` into
the specialist producer protocol. Historical replay semantics from #383 remain
source-publication cutoff rules; period-end alone never establishes availability.
The initial backward adapter `wrap_legacy_result` treats existing
`security-underwriting`, `technical-structure`, and `valuation-scenario-review`
outputs as versioned opaque payloads. It deep-copies rather than changes their
shape; synthesis must not read fields from an opaque legacy payload until a
producer-specific mapping is separately specified and tested.

## Versioning and compatibility

- `contract_version` is `1.0` for this first envelope. A new major version
  requires a separate explicit adapter; any unimplemented version fails closed.
  Additive fields require a new minor schema and an explicit compatibility
  decision before consumers accept them. PATCH does not change semantics.
- `analysis_id`, canonical `instrument_id`, `result_id`, `claim_id`, and
  `source_id` are stable IDs, not tickers or display labels. Two instruments
  may share a ticker while retaining distinct canonical IDs.
- Every result retains the context's analysis, instrument and instant in time.
  A specialist may narrow its observation window; it cannot shift the shared
  horizon or cutoff.
- Metrics preserve value, unit, reporting period, accounting and adjustment
  basis, corporate-action treatment, currency, publication time and method
  receipt. `metric_comparability` refuses direct comparison when a required
  dimension is missing or different. It never converts or normalizes values.
  Currency and corporate-action treatment may be null for a dimensionless or
  otherwise inapplicable metric; that does not make two observations comparable.
  Monetary comparisons require explicit currency and applicable corporate-action
  basis on both sides. `value_dimension` and applicability fields are producer
  assertions, not independently authenticated facts; consumers must compare them
  as contract metadata and never treat them as proof of the reported value or its
  source. The validator requires explicit nulls for N/A and rejects a verified
  monetary metric declared without currency.
- Missing, stale, conflicted, unavailable, and not-applicable states are
  explicit. None is encoded as numeric zero or neutral evidence.
- `TEST` and `HISTORICAL_REPLAY` contexts have `write_scope.mode=NONE`.
  Explicit write intent requires a live canonical context, a named operation,
  target and authorization reference; this contract still performs no write.

## Offline example command

```sh
python scripts/investing/investment_contracts.py \
  tests/fixtures/investing/interfaces/context-equity-v1.json \
  tests/fixtures/investing/interfaces/results-equity-v1.json
```

The fixtures contain synthetic data. Use exact-source receipts and an actual
execution channel for runtime claims; a valid fixture or CI result is not a
deployed Investment OS behavior PASS.
