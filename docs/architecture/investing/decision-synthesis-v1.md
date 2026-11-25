# Investment decision synthesis v1 (offline slice and Cloud Next fixture pilot)

Status: Python offline slice merged; Cloud Next fixture-only pilot candidate in this branch; independent exact-candidate review and runtime acceptance required.
Impact: A3. Owner: `investment-security-review`.
Dependency: accepted #753 contract (main merge `2d4d8595d10a49b1b29f9e5c9b9954d2e02ce8c0`).

## Boundary

`scripts/investing/investment_decisions.py` is a pure, deterministic function. It
consumes #753 AnalysisContext and SpecialistResult envelopes plus a typed v1
decision-signal projection carried in each source result. It neither retrieves
sources nor accesses the record store, writes a journal, calculates numeric
sizing, trades, or invokes a workflow. The production `investment-security-review`
route, load, stop conditions, and existing report remain unchanged.

A decision signal must match an allow-listed producer role, the same analysis
identity and cutoff, a supported signal schema, and result/claim/evidence IDs in
that producer's envelope. `LEGACY_OPAQUE` and free-text claims cannot supply a
gate state. A typed signal and `VERIFIED` marker are still producer assertions;
this offline validator does not authenticate a source, digest, policy, or host.

## Gate order

| Gate | State source | Bounded effect |
| --- | --- | --- |
| G0 identity/context/provenance | #753 validation and typed reference checks | Invalid inputs block dependent gates. |
| G1 evidence sanitation | Underwriting quality signal | `VERIFY`, `CONFLICTED`, or `BLOCK` abstains and blocks valuation/sizing. |
| G2 eligibility | Explicit policy/investability signal | Unknown or ineligible state prevents portfolio recommendation; independent research states remain visible. |
| G3 thesis | Independent `thesis-challenge` signal | Preserve `SURVIVES`, `WEAKENED`, `INVALIDATED`, or insufficient evidence. |
| G4 valuation | Valuation producer readiness plus separate attractiveness category | Requires G1 prerequisites; no averaging, recomputation, or invented threshold. |
| G5 portfolio | Policy-linked fit state and complete position snapshot | Review threshold yields `TRIM_REVIEW`; hard cap yields `REDUCTION_REVIEW`; neither creates a target or direct trade. |
| G6 timing | Optional technical producer | Omitted is `N/A`; supplied but unusable is `UNRESOLVED`; it cannot override earlier gates. |

Every gate retains result, claim, evidence, and policy references. Unknown position
state is a G5 unresolved state, not proof of an empty portfolio. Missing/conflicted
or late data abstain. Output always has `owner_approval_required=true`,
`owner_decision=null`, `execution_authorized=false`, and `numeric_sizing_blocked=true`.

## Recommendation mappings implemented in this slice

These are proposed diagnostic mappings from categorical producer states, not
calibrated investment rules:

- New, eligible, verified, surviving/weakened thesis with an unfavorable
  attractiveness state and in-policy portfolio context may yield `WAIT`.
- Held position with non-invalidated thesis, ready attractive/fair valuation,
  in-policy portfolio and explicit continuation rule may yield `HOLD`.
- A held position at a policy review threshold may yield `TRIM_REVIEW` only.
- A verified invalidated thesis may yield `SELL_REVIEW` for a held position or
  `AVOID` for a new candidate; no `SELL` instruction is emitted.
- A non-eligible new candidate may yield diagnostic `AVOID`; a held position
  remains without an inferred sale instruction.
- A hard-cap breach yields `REDUCTION_REVIEW`, not a recommendation or size.

`BUY`, `ACCUMULATE`, direct `TRIM`, and `SELL` remain intentionally unimplemented.
The repository has no accepted thresholds, outcome calibration, or precedence
rules for these labels. Attractive new candidates therefore abstain with an
explicit mapping-pending reason. A HOLD positive case requires an explicit
policy continuation rule in the referenced portfolio result. These missing
mappings are owner decisions; they are not filled with invented limits.

## Compatibility and rollback

No canonical state migration occurs. The function is not registered as a
runtime workflow. Rollback removes this module/schema/fixtures and retains #753.
If future consumers persist decisions, stop new references first and retain the
v1 reader or add an explicit adapter before removing it. Existing research and
store behavior stays authoritative.

## Cloud Next fixture pilot

`evaluate_investment_decision_fixture` is a Cloud Next-only additive tool. It
accepts a registered fixture ID and the exact canonical source revision. It
resolves digest-pinned, synthetic inputs from the Worker bundle and recomputes
a deliberately limited projection of gate statuses and recommendation fields
on each call. It returns `PARITY_SUBSET_ONLY`; this is not a general synthesis
API and does not accept caller-supplied evidence, live portfolio data, prompts,
or arbitrary decision bundles. The Python MCP common tool contract is unchanged.

The pilot covers four synthetic paths only: WAIT, HOLD, unresolved incomplete
snapshot abstention, and hard-cap reduction review. It preserves the
no-authorization, no-sizing, and owner-approval invariants. It does not execute
the `investment-security-review` workflow or specialist agents. It cannot
authenticate upstream evidence, source digests, policy, or host role/model
execution. The production route/load/report path remains unchanged.

The Python implementation now rejects non-TEST or write-scoped contexts,
abstains when G5 is unresolved/not applicable, and rejects noncanonical or
timestamps with finer than microsecond precision. These corrections do not authenticate caller
assertions or resolve the source/policy trust gap. General or live synthesis
remains blocked on those controls, broader parity, and accepted historical and
runtime evidence.

## Verification boundaries

Synthetic tests exercise all 36 combinations of held/new, three thesis states,
three attractiveness states, and two portfolio-constraint states, alongside
missing evidence, conflicts, late data, incompatible versions, dangling refs,
opaque payload rejection, policy review versus cap breach, ETF-shaped input,
optional timing, no-write guarantees and deterministic output. These tests do
not satisfy the issue's matched authenticated historical archive requirement.
Cloud Next candidate tests invoke the TypeScript projection and compare the
supported gates/recommendation fields against a freshly executed Python oracle.
Those local checks do not prove the deployed version has been updated or that a
host invoked the tool. Deployed runtime acceptance remains `NOT_RUN` until the
merged source is published, attestation is reconciled, and a fresh Cloud Next
conversation records successful calls for both a positive and abstaining
fixture. Issue #754 remains open for its full live-data, trust, historical, and
workflow acceptance scope; the fixture pilot alone does not close it.
