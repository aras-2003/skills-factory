---
name: investment-record-store
description: 'Read and persist canonical Investment OS records in Supabase/Postgres,
  including portfolio state, transactions, research, signals, theses, decisions, policy,
  themes and sources. Use whenever an investing workflow needs durable state or history.
  Google Drive is raw-document/legacy migration storage, not the canonical relational
  store after cutover.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.0.2
  maturity: production
  risk: high
  last_reviewed: '2026-10-12'
---

# Investment Record Store

## Purpose
Provide one durable, auditable persistence contract for Investment OS, with Supabase/Postgres as the target canonical store.

## Canonical-store rule
Exactly one canonical store may be active at a time.

Target state:
- **Supabase/Postgres** = canonical relational state and history.
- **Google Drive** = raw documents, broker exports, PDFs, statements and migration/archive material.
- Chat history, local Codex files, markdown, JSON sidecars, temporary workspace files and analytics outputs are never canonical.

During migration, the legacy Investment OS Google Sheet may remain the active canonical store only until an explicit cutover record is made. Once cutover occurs, Sheets becomes read-only migration/archive input and must never receive new canonical writes.

A local artifact may be created for convenience, but it must be labeled `NONCANONICAL`.

## Procedure
1. Resolve the canonical target through the bootstrap contract in `references/canonical-schema-governance.md` before any normalized read or write:
   - read `public.system_config`;
   - resolve `canonical_backend` and optional `canonical_schema_policy`;
   - verify project ID and canonical schema;
   - emit backend + project + schema + config source in the READ receipt.
   - do not report the bootstrap table as empty unless an explicit query to `public.system_config` returned zero rows;
   - if subsequent canonical `public.*` reads succeed after an "empty bootstrap" observation, treat that as contradictory evidence and retry the exact bootstrap read before finalizing the receipt.
   - **Fail-closed hard stop:** if the exact bootstrap read returns zero rows, cannot be read, has duplicate/conflicting active configuration, or does not verify the connected project ID, canonical schema, and cutover state, stop before every normalized read and write. Return `BLOCKED_CANONICAL_TARGET` (or `UNAVAILABLE` when the bootstrap itself is unavailable) with the observed reason and no persistence call.
   - User authorization, an isolated TEST project ID supplied in the prompt, visible target tables, previous successful runs, or a successful direct SQL connection do not override a missing or mismatched bootstrap. Do not try direct table SQL, another schema, Sheets, or another tool as a write fallback. A failed preflight means zero write attempts.
2. If Supabase is the configured canonical backend:
   - use only the resolved canonical schema for normalized Investment OS records;
   - never discover the canonical schema by scanning for whichever schema contains rows;
   - never silently fall back to an equivalent table in another schema;
   - read only required tables/views;
   - use relational keys and stable record IDs;
   - resolve instrument identity before creating a new instrument:
     - non-null ISIN is globally unique and takes precedence when available;
     - ticker alone is not a global unique key;
     - a composite legacy reference containing multiple symbols (for example `SMH.L|IUIT.L`) is not one instrument and must never be inserted into `instruments`;
   - treat append-only/event tables as immutable history;
   - derive current-state views from source records where practical.
3. If migration has not cut over yet, legacy Sheets may be read/written only under explicit `legacy_sheets` mode.
4. Never silently fall back from Supabase to Sheets or from one Supabase schema to another. If the configured backend/schema is unavailable, contradictory or empty for the requested record, return `UNAVAILABLE`, `FAILED` or an evidence limitation as appropriate; do not search a duplicate schema for substitute canonical data.
5. Require `as_of_date` for state records and `source_date` plus source reference for externally derived facts.
6. Persist transactions, research events, signals, thesis versions, decisions, outcomes and sources append-only.
   - Thesis version states are `DRAFT`, `ACTIVE` or `RETIRED`.
   - `DRAFT` is reviewable working state and must not appear in `current_theses`.
   - `ACTIVE` is the only thesis state eligible for thesis monitoring.
   - State transitions are append-only: write a new thesis version; never mutate historical thesis text/state to simulate a transition.
7. For `instrument_exposures`, require idempotent identity by instrument + as_of_date + exposure_type + exposure_key + source. A refresh of the same issuer snapshot must not create duplicate exposure rows.
8. Preserve policy versions with effective dates.
9. Prefer views for current positions/current thesis/current policy rather than duplicating mutable current-state tables when the relational model can derive them safely.
   - Use `latest_valid_snapshot_pair` and `portfolio_position_changes` for latest-vs-prior portfolio observation when available.
   - Use `portfolio_exposure_source_coverage` to identify the share of current portfolio weight with any exposure metadata.
   - Treat observation views as derived canonical-query surfaces for state/delta/coverage only, never as causal attribution evidence or proof of decomposition completeness.
10. Treat research-state persistence separately from owner-decision persistence, while honoring the caller's write boundary:
   - persist only when the user explicitly requests saving/persisting, or the invoking workflow clearly declares an authorized write as part of its contract and the current request does not say read-only, preview, no-save, or test;
   - a report, research, or discovery request alone is not write authorization;
   - never write to a canonical production backend during evaluation, controlled tests, previews, or when the environment/write boundary is unknown; use a verified isolated test store or perform reads only;
   - do not require an owner BUY/SELL decision before an explicitly authorized research-state write to `opportunities`;
   - owner decisions, policy changes, thesis activation, and transaction execution follow their separate approval contracts.
11. After every write attempt, return an explicit WRITE receipt. Never claim saved/preserved if canonical persistence failed.

## Decision rules
- Supabase is a datastore, not an evidence source.
- Data/BI outputs are derived analytics, not canonical state.
- Google Drive remains authoritative for raw uploaded documents only, not normalized investment records after cutover.
- Current-state correction and historical rewrite are different operations.
- Duplicate evidence should link to one source record.
- Repository files contain schemas/instructions only, never live holdings or credentials.
- No hidden fallback between canonical backends or schemas.
- Exposure refreshes are idempotent: identical issuer evidence for the same instrument/date/type/key/source is one canonical exposure row.
- Instrument master integrity: non-null ISIN must be unique; composite/multi-symbol legacy references are evidence or grouping metadata, not instrument identities.
- Draft thesis content is never treated as active canonical thesis state; `current_theses` exposes only latest ACTIVE versions and `draft_theses` exposes latest DRAFT versions.
- The fixed bootstrap authority is `public.system_config`; a duplicate `system_config` in another schema cannot redefine the active canonical target.
- Current deployment resolves to project `investment-os`, schema `public`; `investment` is deprecated/noncanonical until a future explicit cutover.
- An explicit report/discovery request does not by itself authorize a canonical write. An evidence-backed opportunity may be recorded as `RESEARCH_CANDIDATE` without an owner BUY/SELL decision only when the user or workflow has explicitly authorized persistence and the target is verified safe.

## Output contract
For every read/write operation return a Persistence receipt with:
- status: SUCCESS / UNAVAILABLE / FAILED
- operation: READ / APPEND / SNAPSHOT / UPDATE_CURRENT / POLICY_VERSION / MIGRATE
- backend: SUPABASE / LEGACY_SHEETS
- canonical_target: project + schema/table/view or workbook + tab/range
- config_source: bootstrap schema/table/key used to resolve canonical target
- as_of_or_effective_date
- record_ids or rows affected when successful
- source references / provenance when applicable
- integrity warnings
- failure_reason when not successful
- fallback_artifact, if any, explicitly labeled NONCANONICAL

## Quality checks
- [ ] Exactly one canonical backend and one canonical Supabase schema are active.
- [ ] Canonical target was resolved from `public.system_config`, not inferred from row presence.\n- [ ] Missing, unreadable, duplicate/conflicting, or mismatched bootstrap ended the operation before any normalized read/write attempt.
- [ ] No silent Supabase->Sheets or cross-schema fallback occurred.
- [ ] READ and WRITE outcomes are explicit.
- [ ] Append-only history was not overwritten.
- [ ] Source provenance is retained.
- [ ] Analytics outputs are not presented as canonical records.
- [ ] Instrument exposure refresh did not create duplicate identity rows.
- [ ] Instrument identity was not created from a composite multi-symbol legacy reference.
- [ ] Non-null ISIN identity is unique.
- [ ] DRAFT thesis versions are excluded from active-thesis reads/monitoring.
- [ ] Research-state writes have explicit authorization from the user or calling workflow.
- [ ] Controlled tests, previews, and unknown write boundaries never write to canonical production.
- [ ] A research opportunity write does not require an owner BUY/SELL decision when persistence was explicitly authorized.
- [ ] No personal portfolio data or credentials are written to Git.
- [ ] Persistence failure is surfaced explicitly.

## References
- references/supabase-contract.md
- references/canonical-schema-governance.md
- references/google-sheets-contract.md
