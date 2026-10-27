# Megatrend radar: data and workflow design

Status: design proposal only. This document does not change the Supabase schema,
seed data, Investment OS workflow, or portfolio decisions. Any schema work below
requires a separately approved implementation scope.

## Recommendation

Keep `market_themes` as the stable identity for a theme and
`market_theme_versions` as dated observations of its thesis. Model the proposed
`megatrend → theme → subtheme` tree with a nullable self-reference on
`market_themes` in a future migration; do not encode the parent in a name or in
unvalidated JSON. Keep a stable machine key separate from the display name so
renames do not create new identities. Existing UUID `theme_id` values remain
the record identity. Do not create duplicate theme tables or a second signal
store.

A self-reference is the smallest fit for the current shallow 8/36 taxonomy and
keeps ancestry explicit. A closure table would make sense only if arbitrary
depth and frequent ancestor/descendant queries become measured requirements;
that added write consistency is not justified for this tree today.

Theme membership and instrument exposure are distinct facts. A future explicit
many-to-many link should classify the relationship as `revenue`, `supply_chain`,
`design_win`, `partnership`, or `narrative`, with source, as-of date, confidence,
and optional materiality. Revenue and verified supply-chain exposure may count
as economic exposure; design wins, partnerships, and narrative are evidence
states and must not be displayed as realized revenue. An instrument's link to a
theme must be evidence-backed and time-bounded.

## Existing schema reuse map

The canonical schema is `public`, as recorded in
[`SUPABASE-MIGRATION-SOURCE.md`](SUPABASE-MIGRATION-SOURCE.md). The older
`investment` schema in historical migration files is private and noncanonical.

| Need | Existing object | Reuse now | Gap / avoid |
| --- | --- | --- | --- |
| Theme identity | `market_themes(theme_id, name)` | Stable UUID identity | No hierarchy or immutable natural key; `name` is unique and mutable only by a future controlled change |
| Dated theme thesis | `market_theme_versions(theme_version_id, theme_id, as_of_date, mechanism, indicators, beneficiaries, losers, invalidation)` | Versioned thesis observations | Does not version hierarchy or attach sources directly |
| Observations/signals | `signals` | `theme_id`, `instrument_id`, `source_id`, `source_date`, `confidence` | No theme-only subtype or natural dedupe constraint; keep source evidence with each observation |
| Company/theme research | `research_events` | Existing `theme_id`, `instrument_id`, `thesis_id`, date and confidence | Reuse as research history; do not create a second research log |
| Instrument exposure | `instrument_exposures` | Dated exposure keyed by `exposure_type`/`exposure_key`, with source | Not a canonical theme membership relation; do not overload `exposure_key` with an undocumented hierarchy |
| Sources | `sources` | Publisher, URL/reference, published/accessed dates and content hash | Preserve source identity and provenance; do not duplicate source metadata in a theme table |
| Evidence-to-entity link | `evidence_links` | Links source to an entity type/id and claim key | Polymorphic target has no FK; validate allowed entity types and targets in any future write path |
| Opportunity | `opportunities` | Dated instrument opportunity and setup/risk/next step | Has no `theme_id`; do not infer a theme from free-text setup |
| Investment thesis | `theses`, `thesis_versions` | Instrument thesis, assumptions, catalysts, risks, kill criteria | Keep investment thesis distinct from market theme thesis |
| Watch priority | `watchlist` | Instrument setup and next trigger | No theme watchlist; current P1/P2 priorities remain research inputs, not persisted portfolio decisions |

The current unique index on exposures prevents duplicate rows with the same
instrument/date/type/key/source identity. It does not prevent semantically
duplicate `signals`; signal ingestion must use source identity, normalized
claim, subject, and source date for idempotency and report collisions for review
rather than silently merging conflicting evidence.

## Provenance path

The intended evidence graph is:

`source → signal / research_event → theme → evidenced instrument link → opportunity → thesis version`

Today, a `signal` or `research_event` can identify both a theme and an
instrument, and a research event can identify a thesis. `opportunities` and
`theses` identify an instrument, but there is no direct theme-to-opportunity
edge and no typed theme-to-instrument link. Therefore, a report may traverse
only explicit IDs and must show a missing edge as missing. It must not infer a
causal link from matching ticker text or use an opportunity's free-text fields
as proof of theme exposure. Each claim should retain `source_id`, `source_date`
or `as_of_date`, confidence, and a source/evidence link where available.

## Radar and scoring contract

Use the requested eight megatrends and 36 areas as a versioned research
taxonomy, not as hard-coded constants. Taxonomy rows need stable keys, parent
identity, lifecycle state, effective dates, and supersession; changes to labels
must not silently rewrite historical reports. Sector watchlists and P1/P2
priority are review inputs with an explicit as-of date.

The issue's initial coverage inputs are P1 energy networks, medtech, water, and
diagnostics; P2 quantum, robotics, and defense. They are not pre-approved
themes or position decisions. The actual 8/36 taxonomy must be reviewed and
versioned before loading it into a database.

Keep separate dimensions instead of one opaque score:

1. **Evidence strength:** primary/secondary source quality, recency, confidence,
   and whether the claim is independently corroborated.
2. **Commercialization stage:** research, prototype, design win, production,
   scaling, or mature. Stage requires dated evidence and is not revenue.
3. **Momentum:** change in dated indicators and signals versus a fixed prior
   observation; missing history yields `NOT_SCORED`.
4. **Valuation:** instrument-level valuation at a known price/as-of time; it is
   not a property of the megatrend itself.
5. **Risk and materiality:** explicit downside, dependency, concentration, and
   possible revenue materiality, with evidence and confidence.
6. **Distinctiveness / portfolio overlap:** a portfolio fit view kept separate
   from the underlying theme or security score. Do not double-count correlated
   exposures as multiple independent themes.

Any later aggregate score must have a named and versioned formula, weights,
normalization rules, coverage/completeness, confidence, input IDs and dates.
Missing, stale, incomparable, or contradictory evidence yields `NOT_SCORED` or
an explicit low-confidence result; it never defaults to a neutral midpoint.
The radar does not emit BUY/SELL decisions, modify the watchlist, or write to
Supabase as part of this design.

## Duplicate and change detection

- Themes deduplicate by immutable stable key, not display name or approximate
  text similarity. Similar names are review candidates, never automatic merges.
- A signal is an idempotent observation only when its source, subject, claim
  type, source date, and normalized value agree. Conflicting values remain
  separate observations with explicit conflict status.
- Theme changes create a new dated `market_theme_versions` observation; they do
  not overwrite an earlier mechanism, beneficiaries, losers, or invalidation.
- Instrument links are unique by theme, instrument, relation type, effective
  interval, and evidence identity. Evidence-free or expired links do not count
  toward exposure.
- Change detection compares a new snapshot to the last valid snapshot at or
  before its as-of date. It must not read future observations or current labels
  to rewrite a historical result.

Concrete contract examples for later implementation:

| Input sequence | Expected behavior |
| --- | --- |
| Same source, subject, claim type, source date, and normalized value imported twice | One idempotent observation; no duplicate row |
| Same source and date with a different normalized value | Preserve both versions or flag a conflict; never silently overwrite |
| Two sources report the same claim | Keep both provenance links; deduplicate the displayed claim only with an explicit aggregation rule |
| Similar theme labels with different stable keys | Keep separate pending-review identities; do not auto-merge |
| Current report requests an as-of date before a later signal/version | Later observation is excluded from the earlier result |
| Only a stale or missing valuation input exists | Valuation dimension returns `NOT_SCORED`; do not substitute a midpoint |

## Deferred migration and safety plan

No migration is included in this change. If implementation is separately
approved, prepare one additive migration with:

1. Stable theme key, nullable parent theme FK, parent-cycle prevention, and
   effective/supersession metadata.
2. A typed theme-instrument relationship table with constrained relation type,
   evidence/source FK, as-of/effective dates, confidence, and a uniqueness rule
   for idempotent imports.
3. Optional opportunity-theme link only if product behavior needs it; do not
   add a nullable theme column as a substitute for a many-to-many relationship.
4. Narrow indexes on parent, theme/instrument/effective date, and evidence
   lookup paths, based on explainable query patterns.
5. RLS enabled; grants limited to the existing server-side service role and
   only the operations required by a future persistence contract. Preserve
   denied `anon`/`authenticated` access and existing default ACLs.

Before any backfill, define a dry-run report with source row counts, invalid or
ambiguous mappings, duplicate candidates, and expected inserts. Backfill only
with explicit mapping, stable IDs, and source receipts. Reconcile counts and
sample provenance, then cut reads over behind a reversible feature flag or an
old-read fallback. Roll back by disabling the new read path; do not delete
source observations or rewrite history. Production application is a separate
reviewed deployment action.

## Verification plan for a future implementation

- Schema contract tests: parent FK and acyclic hierarchy, stable-key uniqueness,
  relationship-type validation, date validity, and restricted grants.
- Idempotency tests: repeating an identical signal/link import creates no
  duplicate; conflicting source values remain visible for review.
- Provenance tests: every displayed exposure has an allowed relation, source,
  date, and confidence; narrative-only links never become revenue exposure.
- Temporal tests: as-of queries exclude later source events and later theme
  versions; expired relationships are not counted.
- Scoring tests: missing/stale evidence returns `NOT_SCORED`; changing weights
  changes the model version; portfolio overlap is not folded into intrinsic
  theme score.
- Compatibility and rollback tests: old workflow reads remain valid during
  additive rollout, and disabling the new path restores the prior behavior.
- Use synthetic fixtures in local/disposable Postgres. Do not seed this
  taxonomy or alter production until a separate migration is approved.

## Scope decision

This design satisfies the current P3 research ticket without a schema or
workflow change. It does not claim that the 8/36 taxonomy has been loaded, that
current exposure links are complete, or that scoring has been calibrated.
