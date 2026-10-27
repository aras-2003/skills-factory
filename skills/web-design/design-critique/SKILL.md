---
name: design-critique
description: >
  Use when reviewing a supplied interface screenshot or visual artifact for hierarchy,
  clarity, affordance, responsiveness, consistency, distinctiveness and cognitive
  risk. Give evidence-bound findings and practical repairs; do not infer hidden
  behavior or claim automated accessibility/runtime checks.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
  execution:
    default_model_class: standard
---

# Design Critique

## Purpose

Review an existing interface artifact and help the owner decide which visual or interaction-design issues to fix first. Ground each finding in what the supplied artifact actually shows.

## Use when

- The user asks for critique, review, or prioritization of an existing screen or flow.
- A screenshot, rendered page, design file, or other inspectable visual artifact is supplied or explicitly linked.
- The requested output is findings and proposed repairs, not a replacement interface or implementation.

## Do not use when

- The user wants a new screen or flow designed; use `interface-design`.
- The user asks for code changes; use an implementation workflow.
- The request is for a report, chart, diagram, brand identity, or content-only critique.
- No inspectable visual artifact is available. Ask for one before making claims about the design.

## Inputs

### Required

- The screen or flow to review, supplied as an inspectable visual artifact.
- The intended user and task, or an explicit statement that these are unknown.
- The target device or viewport when judging responsive behavior.

### Optional

- Product constraints, design system, accessibility requirements, user research, and known technical limits.
- A baseline and a changed version for a comparative critique.
- The decision the critique should support and any severity scale already used by the team.

## Evidence boundary

- Separate direct observations from interpretation and recommendations.
- Cite visible evidence precisely: region, component, text, alignment, contrast relationship, or supplied state. Do not cite a hidden implementation detail.
- A static screenshot can support claims about visible hierarchy and presentation. It cannot prove that a control works, navigation is correct, focus is managed, the page reflows, contrast meets a numeric standard, or an animation is usable.
- Treat interaction, responsive, accessibility, and performance claims as unverified unless the relevant behavior was directly exercised or measured with suitable evidence. State the specific test needed.
- Do not infer user research, business impact, conversion effects, or established design tokens from appearance alone.
- If the artifact, intended user/task, or relevant viewport is missing, ask a concise question naming only the missing inputs. Do not substitute a generic checklist.

## Procedure

1. Confirm which supplied artifact and state are being reviewed, the intended user/task, viewport, and decision sought. Identify unavailable context.
2. Describe the primary visual hierarchy and the path a user appears expected to follow. Mark this as an interpretation when the task is not supplied.
3. Look for material issues across hierarchy, clarity, affordance, readability, consistency, responsiveness, distinctiveness, cognitive load, and visible accessibility risks. Report only issues supported by the artifact.
4. For each finding, record severity, confidence, evidence, likely user consequence, and a specific repair. Keep inferred consequence distinct from observed evidence.
5. Prioritize by impact and scope. Avoid false precision, aggregate quality scores, or rankings that imply measurement when none occurred.
6. For a baseline/changed comparison, verify both artifacts depict the same screen, state, and viewport. Report observed deltas; do not credit a change for an unrelated difference.
7. List relevant behavior that needs an interactive, responsive, keyboard, screen-reader, or automated measurement check. Do not present those checks as passed.

## Severity

- **Critical** — the visible design prevents or seriously misdirects the stated primary task, or exposes a serious user risk.
- **Major** — a prominent obstacle or ambiguity is likely to affect a meaningful part of the task.
- **Moderate** — a localized issue adds friction or weakens comprehension without blocking the task.
- **Minor** — a small polish or consistency issue with limited task impact.

Severity is a reasoned prioritization, not a measured probability or confirmed outcome. Lower confidence when the user/task, viewport, or artifact state is unknown.

## Output contract

Return a **Design critique** with:

1. **Scope and evidence** — artifacts/states/viewports reviewed, supplied task and constraints, and important unknowns.
2. **Overall read** — one short statement about what is visually clear and the main issue to address first.
3. **Findings** — for each: severity, confidence, visible evidence, interpretation/likely consequence, and concrete repair. If none are supported, say so.
4. **Comparison** — only when comparable baseline and changed artifacts were supplied; describe observed deltas without assuming causality.
5. **Needs verification** — interaction, responsive, accessibility, or performance checks that cannot be established from the artifact.
6. **Recommended order** — the smallest useful sequence of fixes, tied to the findings.

## Quality checks

- [ ] Every finding points to visible evidence in the supplied artifact.
- [ ] Observations, interpretations, and proposals are distinguishable.
- [ ] Severity reflects the stated user task and is not presented as a metric.
- [ ] No unseen interaction, responsive behavior, contrast ratio, or user outcome is claimed as verified.
- [ ] Each repair is specific enough to act on and does not invent product capabilities.
- [ ] A missing artifact or essential context produces a request for that input, not a generic critique.
