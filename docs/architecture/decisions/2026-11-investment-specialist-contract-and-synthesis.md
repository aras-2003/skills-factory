# Investment specialist contract and synthesis decision

## Decision identity

- Issues: #753 (AC #1–#4), #754 (AC #1–#5)
- Status: `DRAFT` (advisory; exact-candidate review required)
- Baseline SHA: `f08abcf81bace86cb60908d7945dbebeb0df6dbc`
- Impact: A3; two sequential contracts, #753 first and contract-only
- Decision owner: investment-security-review; independent reviewer required
- Related contracts: `docs/architecture/content-to-artifact-contract.md`, `skills/investing/historical-decision-replay/SKILL.md`

## Scope and source-backed consumers

Extend the existing investment evidence and replay patterns. Do not create a new
database, generic DomainResult, valuation formula, model score, or persistence
path. #753 owns a domain-internal JSON exchange contract. #754 consumes its
validated immutable references through a pure deterministic advisory function.

| Producer / interface | Consumer | Source evidence |
| --- | --- | --- |
| `investment-os-review` context owner | `investment-security-review` | `workflows/runtime-registry.yaml`; `workflows/investment-security-review/WORKFLOW.md` |
| `security-underwriting`, `valuation-scenario-review`, `thesis-challenge` | synthesis as immutable result references | `workflows/investment-security-review/WORKFLOW.md`; corresponding `skills/investing/*/SKILL.md` |
| `position-sizing-review`, `investment-policy-design`, `portfolio-state-review` | portfolio gates only | corresponding skill paths under `skills/investing/` |
| investment decision | #297 reporting adapter | `docs/architecture/content-to-artifact-contract.md` (one-way mapping only; no runtime dependency) |
| replay context | publication cutoff semantics | `skills/investing/historical-decision-replay/SKILL.md` |
| persistence | existing `investment-record-store` only | `skills/investing/investment-record-store/SKILL.md`; no writes in this change |

The listed paths establish observed consumers, not a proven complete dependency
graph. External clients and unregistered callers remain `UNKNOWN`; preserve full
affected-channel regression until their inventory is complete.

## Trust, failure and compatibility

All test fixtures are synthetic. A digest, source URL, or caller-supplied
`VERIFIED` state is an assertion unless independently checked against its source.
Historical replay requires publication eligibility at or before `as_of`.
Incompatible periods, bases, currencies, adjustments, or missing provenance are
preserved as separate observations and block comparison; never normalize by
inventing a conversion or treating missing as zero. Unknown contract major
versions fail closed. No contract call performs retrieval, trade execution, or
store access.

## Decision and alternatives

- #753: `EXTEND` with strict Draft 2020-12 AnalysisContext and SpecialistResult
  envelopes plus deterministic semantic validation. The existing #297 result is
  a one-way report artifact adapter, not a replacement for this producer contract.
- #754: `COMPOSE` a pure read-only decision function from validated context and
  specialist references; do not modify producer-owned findings or existing
  workflow defaults. Missing or conflicting decision-critical evidence abstains.
- Rejected: free-form averaging, copied/recomputed formulas, a new persistence
  schema, implicit policy/portfolio reads, and workflow auto-registration.

The labels in #754 are not fully calibrated decision thresholds. Implementation
must only emit an advisory label where explicit verified inputs and an accepted
mapping suffice; otherwise return a diagnostic/abstention. A SELL review is not
a SELL instruction. Every result requires owner approval and sets
`execution_authorized=false`.

## Sequencing, migration and rollback

1. Merge #753 schemas, validator, synthetic contract tests, and compatibility
   documentation before implementing #754.
2. Add #754 as a separate PR against the merged #753 contract; preserve existing
   workflow behavior by default and exercise synthesis only through an explicit
   synthetic/read-only entry point.
3. No persisted state migration occurs. Before a consumer adopts v1, revert both
   PRs in reverse dependency order. After adoption, stop new references, retain
   the v1 reader or provide an explicit adapter, and only then remove v1.
4. Any changed contract path, consumer set, decision gate, or fixture set
   invalidates this review and requires an exact-SHA re-review.

## Verification plan

| Case IDs | Expected / forbidden behavior | Evidence class |
| --- | --- | --- |
| I753-01–I753-05 | Synthetic equity, ETF, bank, partial evidence, and duplicate symbols with distinct canonical IDs validate without aliasing | Schema + deterministic unit |
| I753-06–I753-17 | Timezone/as-of boundary, late publication, period/basis/currency mismatch, missing currency, corporate-action mismatch, duplicate IDs, unknown major/source, absent policy, write escalation, and dangling references remain explicit and fail closed for dependent comparisons | Deterministic unit; schema validity alone is insufficient |
| I754-01–I754-04 | G0–G6 ordered gates, missing/conflicting evidence, held/new distinction, threshold/hard-cap distinction, and optional technical input produce traced abstention or bounded advisory result | Deterministic unit; no score aggregation |
| I754-05 | Output is immutable/read-only, `owner_approval_required=true`, `execution_authorized=false` | Unit/no-write spy |
| I754-06 | Existing route/load/stop behavior remains intact; new code is not claimed as deployed workflow behavior without an actual supported execution bridge | Existing MCP receipt + candidate runtime boundary |

The Cloud Next loader returns instructions and references; it does not execute
the Python module. A matching route/load receipt proves only the existing
workflow's routing and loading. Runtime acceptance of the new synthesis code
requires an actual supported invocation at the exact candidate source revision
and an independently graded result. No production promotion is authorized.

## Open questions

- Native Project Architecture Impact and WIP readback are unavailable through
  the connected GitHub tools; do not represent the issue stage as updated.
- Complete external consumer inventory is unknown.
- Recommendation thresholds are uncalibrated; no automatic BUY/SELL mapping
  will be invented to fill that gap.
