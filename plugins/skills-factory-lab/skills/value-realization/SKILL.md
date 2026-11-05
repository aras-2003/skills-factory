---
name: value-realization
description: Review a funded strategy initiative against dated benefit baselines,
  forecasts, realized KPIs, owners and explicit decision rules.
metadata:
  owner: skills-factory
  version: 0.1.0
  maturity: candidate
  risk: medium
  last_reviewed: '2026-10-27'
---

# Value Realization

## Purpose
Connect an approved initiative portfolio to a dated benefit ledger and a human review decision. Reuse `evidence-loop-review` for the quality of the wider operating feedback system, `portfolio-prioritization` for comparing initiatives, `decision-rights-review` for authority, and `governance-design` for forums and escalation. This skill owns the initiative-level benefit reconciliation only; it does not duplicate those capabilities.

## Required inputs
- Initiative identity, accountable owner and approved funded amount with source IDs and publication dates.
- Benefit KPI definitions, leading/lagging classification, unit, baseline and target.
- Period-aligned forecast and realized values with source IDs and dates, as of an explicit review date.
- Review cadence and last review date.
- Explicit approved stop/correction thresholds if an action assessment is requested.

Missing inputs remain missing. Never treat an absent baseline, actual, owner, funding record or policy threshold as zero or as approval.

## Procedure
1. Confirm the initiative and funded portfolio source; reconcile identity and owner before calculating benefits.
2. Separate leading indicators from lagging outcomes and preserve each KPI's definition and unit.
3. Compare forecast and actual only for the same period. Report unmatched periods as gaps; do not impute.
4. Calculate absolute and relative variance when the forecast denominator is non-zero. Preserve source IDs and evidence dates.
5. Determine whether the review is due from the supplied cadence and last-review date; if either is missing, return `NOT_CONFIGURED`.
6. Apply only sourced, approved thresholds to exactly one decision-critical comparable KPI. Return `STOP_REVIEW`, `CORRECT_REVIEW`, or `CONTINUE_REVIEW`; these labels request a human decision and never execute one.
7. Summarize funding, accountable owner, expected versus realized benefit, lag/lead evidence, gaps, decision rights, next review date and required corrective owner/action where supplied.

## Output and safety
Use `engine.py` for deterministic ledger reconciliation. It is read-only and emits `writes_performed: false`. Do not create or update canonical portfolio/initiative records, approve funding, stop work, or change policy. Do not infer causal attribution from a KPI variance. Separate calculated variance from interpretation and state evidence coverage.

## Verification boundary
The bundled fixtures verify period matching, arithmetic, provenance, look-ahead rejection, explicit review cadence and threshold behavior on synthetic inputs. They do not verify a connected benefits database, strategy-to-initiative linkage, user permissions, runtime portability, or causal benefit attribution. The public source corpus is now hash-verified and used as method reference only. No third-party content is copied or claimed equivalent; runtime acceptance remains pending.
