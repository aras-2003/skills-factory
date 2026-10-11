---
name: investment-portfolio-review
description: Child workflow for full portfolio review. Use when selected by investment-os-review,
  explicitly requested, or when another Investment OS workflow delegates a portfolio-level
  decision. It performs canonical reads, reconciliation, concentration/diversification
  analysis, policy/thesis checks, integrated reporting and the visual-floor path.
  Do not use as the default natural Investment OS entry point; natural portfolio requests
  should enter through investment-os-review.
metadata:
  owner: arkadiusz-kamrowski
  version: 0.5.1
  maturity: production
  risk: high
  last_reviewed: '2026-10-09'
---

# Investment Portfolio Review Runtime Entrypoint

## Purpose

Expose a repository workflow to the skill runtime without duplicating its orchestration logic.

## Procedure

1. Load `references/WORKFLOW.md`.
2. Follow it as the authoritative orchestration procedure.
3. Route only to specialist skills that the workflow actually requires.
4. Preserve workflow gates, stop conditions and evidence discipline.
5. If an optional dependency is unavailable, apply the declared reduced-scope behavior below and explicitly disclose that the specialist did not run.
6. Do not replace the workflow with a generic best-practice answer.

## Output contract

Use the output contract defined in `references/WORKFLOW.md`.

## Quality checks

- [ ] The workflow source was loaded.
- [ ] Specialist skills were selected selectively.
- [ ] Required dependencies were available.
- [ ] Missing optional dependencies were disclosed and not simulated.
- [ ] Workflow stage order and gates were preserved.
- [ ] Evidence and uncertainty remain explicit.
- [ ] No extra domain was added merely for completeness.
