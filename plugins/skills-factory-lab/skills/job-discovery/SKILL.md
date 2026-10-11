---
name: job-discovery
description: 'Find current senior and executive technology roles from approved sources
  using explicit career filters, remove obvious mismatches and duplicates, and return
  a shortlist for validity checking. Use for role discovery, not deep role evaluation
  or company research.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: candidate
  risk: low
  last_reviewed: '2026-10-09'
---

# Job Discovery

## Purpose
Find plausible senior/executive technology opportunities efficiently without doing expensive downstream analysis too early.

## Use when
- The user asks to find current executive/senior technology roles.
- A recurring job-market scan needs a clean shortlist.

## Do not use when
- The user asks whether one specific role is worth pursuing.
- The task is only to confirm whether an already-known vacancy is still active.
- The user asks whether a known vacancy is current/active; route to `job-validity-check`.
- The user asks for company background only; route to `company-context-research`.

## Inputs
### Required
- target role families or current career profile
### Optional
- geography/work model
- compensation floor
- excluded employers/role types
- approved sources

## Procedure
1. Load the active career profile and hard constraints.
2. Search approved sources broadly enough to avoid source bias.
3. Extract title, company, location, work model, source URL, date, and visible scope signals.
4. Remove clear mismatches against hard constraints.
5. De-duplicate by company + role + location/source.
6. Keep uncertain but potentially strong opportunities; mark missing data as UNKNOWN.
7. Return a shortlist for `job-validity-check`.

## Decision rules
- Do not reject a role only because the title is unconventional.
- Do reject obvious sales, narrow specialist, or non-leadership roles when excluded by the target profile.
- Discovery is recall-oriented: borderline roles may pass forward; deep fit belongs elsewhere.

## Evidence requirements
- Every discovered role needs a traceable source.
- Prefer employer/ATS pages over aggregators when available.
- Currentness must be verified by `job-validity-check`.

## Output contract
Table: Company | Role | Location/work model | Source | Date signal | Why potentially relevant | Missing/uncertain | Next step.

## Failure and uncertainty handling
- Do not invent compensation, team size, reporting line or mandate.
- If source freshness is unclear, mark it for validity check.

## Model guidance
Default model class: **fast**.
Escalate only when search results are highly ambiguous, titles require nuanced executive interpretation, or source conflicts materially affect inclusion.

## Quality checks
- [ ] Hard constraints applied.
- [ ] Duplicates removed.
- [ ] Every role has a source.
- [ ] No deep fit verdict was smuggled into discovery.
