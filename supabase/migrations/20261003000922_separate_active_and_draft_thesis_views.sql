-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

alter table public.thesis_versions
  drop constraint if exists thesis_versions_state_check;

alter table public.thesis_versions
  add constraint thesis_versions_state_check
  check (state is null or state in ('DRAFT','ACTIVE','RETIRED'));

create or replace view public.current_theses as
with ranked as (
  select
    t.thesis_id,
    t.instrument_id,
    t.horizon,
    tv.thesis_version_id,
    tv.version,
    tv.effective_date,
    tv.thesis,
    tv.assumptions,
    tv.catalysts,
    tv.risks,
    tv.kill_criteria,
    tv.state,
    tv.created_at,
    row_number() over (
      partition by t.thesis_id
      order by tv.version desc, tv.created_at desc
    ) as rn
  from public.theses t
  join public.thesis_versions tv on tv.thesis_id = t.thesis_id
)
select
  thesis_id,
  instrument_id,
  horizon,
  thesis_version_id,
  version,
  effective_date,
  thesis,
  assumptions,
  catalysts,
  risks,
  kill_criteria,
  state,
  created_at
from ranked
where rn = 1
  and state = 'ACTIVE';

create or replace view public.draft_theses as
with ranked as (
  select
    t.thesis_id,
    t.instrument_id,
    t.horizon,
    tv.thesis_version_id,
    tv.version,
    tv.effective_date,
    tv.thesis,
    tv.assumptions,
    tv.catalysts,
    tv.risks,
    tv.kill_criteria,
    tv.state,
    tv.created_at,
    row_number() over (
      partition by t.thesis_id
      order by tv.version desc, tv.created_at desc
    ) as rn
  from public.theses t
  join public.thesis_versions tv on tv.thesis_id = t.thesis_id
)
select
  thesis_id,
  instrument_id,
  horizon,
  thesis_version_id,
  version,
  effective_date,
  thesis,
  assumptions,
  catalysts,
  risks,
  kill_criteria,
  state,
  created_at
from ranked
where rn = 1
  and state = 'DRAFT';

revoke all on table public.current_theses from public, anon, authenticated, service_role;
revoke all on table public.draft_theses from public, anon, authenticated, service_role;
grant select on table public.current_theses, public.draft_theses to service_role;
