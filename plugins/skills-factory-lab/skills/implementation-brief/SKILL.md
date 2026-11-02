---
name: implementation-brief
description: 'Turn an approved interface concept into a build-ready specification
  for an existing product implementation, including components, states, props, tokens,
  responsive rules and verifiable acceptance checks. Use when the user asks to hand
  a design to engineering; do not use to design a new concept or implement it.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.0
  maturity: candidate
  risk: medium
  last_reviewed: '2026-10-27'
---

# Implementation Brief

## Purpose

Convert an approved interface concept and available product evidence into a precise handoff an engineer can implement and verify. This is a specification, not code or proof that the implementation works.

## Use when

- An approved screen, flow, or visual concept needs an engineering handoff.
- The user asks to translate design intent into components, data contracts, states, responsive behavior, or acceptance checks.
- An existing repository or runtime is identified, or the brief can clearly mark that target as unresolved.

## Do not use when

- The user is still asking what interface should be designed; use `interface-design`.
- The user asks to change the application or run its tests; follow the implementation workflow for that repository.
- The user asks to compare rendered output with an approved baseline; use `visual-regression-review`.
- The user asks for an accessibility audit; use `accessibility-gate`.

## Required context gate

Identify the approved design/concept, the user task, and the target application or runtime. If the approved design or task is absent, ask for it. If the target application is unknown, ask for it when repository-specific component or token mapping is required; otherwise produce only a product-agnostic handoff and mark mappings unresolved. Never fill gaps with invented product behavior.

## Procedure

1. Inventory the supplied approved design, product constraints, repository references and evidence. Separate verified facts, assumptions and unresolved decisions.
2. Map each visible region to a component responsibility and define its inputs, outputs, ownership and data shape. Reuse named components, tokens and APIs only when evidence supplies them.
3. Specify interaction transitions, validation, permissions and feedback. Include loading, empty, error and unavailable states when relevant, with recovery behavior.
4. Describe responsive behavior at the supported viewport classes. State what reflows, collapses, scrolls or remains persistent; do not infer behavior from a static desktop image.
5. Convert design requirements into acceptance checks. Prefer deterministic checks for structure, links, responsive breakpoints, keyboard operation and accessibility rules. Name the required tool, viewport or evidence for each check.
6. Record visual-regression baselines by artifact, state, viewport and capture conditions. A screenshot comparison only counts when baseline and candidate conditions match.
7. List dependencies, open questions and exclusions. Keep design review, implementation, and test results distinct.

## Output contract

Return an **Implementation brief** with:

1. **Source and scope** — approved artifact/revision, target, user task, verified context, assumptions and exclusions.
2. **Component map** — region, component responsibility, data/props contract and existing component/token references; mark unknown mappings.
3. **Behavior and states** — actions, transitions, validation, permissions, loading, empty, error and unavailable states.
4. **Responsive rules** — supported viewports and explicit layout changes.
5. **Accessibility requirements** — semantics, labels, keyboard/focus, announcements, contrast checks and reduced-motion behavior to implement or verify.
6. **Acceptance matrix** — requirement, deterministic or human check, setup/viewport, expected evidence, and status (`PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED`).
7. **Visual regression protocol** — approved baseline, matched capture conditions and comparison owner.
8. **Open decisions and handoff** — unresolved product rules, dependencies and next owner.

## Evidence and status rules

- `PASS` requires an observed result and its evidence. A proposed test, source inspection, or generated brief is not a runtime pass.
- `FAIL` requires a reproducible mismatch against an explicit requirement.
- `NOT_RUN` means the check was not executed or no suitable evidence was supplied.
- `BLOCKED` means a named dependency prevents execution; state the dependency.
- Do not claim an implementation, screenshot baseline, responsive behavior, keyboard behavior, or accessibility result unless it was actually produced or tested.
- Keep automated pixel/DOM checks separate from human judgment about visual quality.

## Quality checks

- [ ] Every implementation decision traces to the approved design, repository evidence, or an explicit assumption.
- [ ] Components, data contracts, states and responsive rules can be implemented without guessing.
- [ ] Acceptance checks name observable evidence and an honest status.
- [ ] Visual and accessibility checks do not claim results that were not measured.
