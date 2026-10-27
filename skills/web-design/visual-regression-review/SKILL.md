---
name: visual-regression-review
description: >
  Review rendered UI against an approved visual baseline and implementation brief.
  Use when the request is to find visual regressions in comparable screenshots or
  browser captures; distinguish measured diffs from human interpretation.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
  execution:
    default_model_class: standard
---

# Visual Regression Review

## Purpose

Identify meaningful visual changes between an approved baseline and a candidate rendering under comparable conditions. Report evidence and likely impact without treating every pixel difference as a defect.

## Use when

- The request is to compare an implemented screen with an approved baseline or implementation brief.
- Both baseline and candidate renderings, or an executable target and capture conditions, are available.
- A visual regression suite has produced diffs that need triage.

## Do not use when

- Only one artifact is supplied; use `design-critique` for a critique or request the missing baseline.
- The user wants implementation or test code changes.
- The request is primarily about keyboard, screen reader, semantic HTML or accessibility conformance; use `accessibility-gate`.
- The target, viewport, state, data, theme or capture conditions differ and cannot be normalized.

## Required evidence gate

Before comparing, identify the same page/component, state, viewport, data/fixture, theme, browser/device scale and capture conditions for both versions. If material conditions differ, report `BLOCKED` for direct regression comparison and explain the mismatch. A single screenshot can support a bounded visual critique, but not a regression claim.

## Procedure

1. Inventory the baseline, candidate, relevant brief, capture metadata and any automated diff output.
2. Confirm comparability. Record the viewport, state, data, theme, browser and scale, noting any missing metadata.
3. Separate measured evidence (for example, changed pixels or DOM geometry) from visual interpretation and inferred user impact.
4. Triage only material changes: hierarchy, content visibility, clipping/overlap, alignment, typography, spacing, color, affordance, responsive layout and state presentation.
5. Check whether a difference is expected by the approved brief. Do not label intended changes as regressions.
6. Name further interaction, responsive or accessibility checks. Screenshots do not prove these behaviors.

## Output contract

Return a **Visual regression review** with:

1. **Scope and evidence** — artifacts, revisions, states, viewports and capture conditions.
2. **Comparability** — `PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED`, with reasons.
3. **Findings** — severity, measured/visible evidence, interpretation, expected-vs-unexpected status, and concrete repair or confirmation.
4. **Needs verification** — interaction, responsive, keyboard or accessibility checks not established by the render.
5. **Disposition** — regressions found, no supported regression found, or why a conclusion is unavailable.

## Status rules

- `PASS` means the defined comparison ran under matched conditions and no in-scope regression was found; attach the comparison evidence.
- `FAIL` means a reproducible difference violates a stated requirement.
- `NOT_RUN` means the comparison was not executed or suitable artifacts are absent.
- `BLOCKED` means a specific mismatch or unavailable dependency prevents a valid comparison.
- Do not convert `NOT_RUN` or `BLOCKED` into a pass because a page looks plausible.
- Do not claim pixel-perfect equivalence from visual inspection alone or infer functional correctness from screenshots.

## Quality checks

- [ ] Baseline and candidate are comparable, or the result is explicitly blocked.
- [ ] Measured differences and human interpretations are distinct.
- [ ] Expected design changes are not mislabeled as regressions.
- [ ] No interaction, responsive, or accessibility result is claimed from static imagery.
