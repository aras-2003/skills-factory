---
name: accessibility-gate
description: >
  Review interface implementation evidence for accessibility risks and required
  follow-up checks. Use when a team needs an evidence-bound accessibility gate
  beyond deterministic CI; never claim WCAG conformance without an appropriate audit.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: candidate
  risk: high
  last_reviewed: "2026-10-27"
  execution:
    default_model_class: standard
---

# Accessibility Gate

## Purpose

Organize and review accessibility evidence for a specific interface, state and supported runtime. Find gaps that deterministic checks may miss and decide what evidence is still needed. This review does not certify legal or WCAG conformance.

## Use when

- The user asks for an accessibility readiness review, gate, or triage of accessibility findings.
- An implementation brief, rendered page, source, test output or manual test notes are supplied.
- The request is to identify risks and verification gaps, not to claim certification.

## Do not use when

- The user asks only for visual polish or design critique; use `design-critique`.
- The requested deliverable is an interface concept; use `interface-design`.
- The user asks to implement a fix; use the target repository's implementation workflow.
- No target interface or artifact is identified; ask for it before making interface-specific findings.

## Evidence boundary

- A screenshot can reveal visible text, layout and some contrast risks, but cannot establish semantic roles, keyboard order, screen-reader output, dynamic announcements or successful zoom/reflow.
- Automated scanners cover only the rules they detect and the states they inspect. A clean scan is not proof of WCAG conformance.
- Report standards references only when the tested criterion, level, tool/version and evidence are known. Otherwise phrase findings as risks or proposed checks.
- Treat user impact as a reasoned interpretation unless validated with users or other supplied research.

## Procedure

1. Define target, user flow, supported runtime, artifacts, tested states and applicable requirements. Identify missing evidence.
2. Review the semantic structure and accessible names from source or accessibility tree when supplied; do not infer semantics from appearance.
3. Review keyboard operation and focus entry/order/visibility/return, including dialogs and dynamic changes where applicable.
4. Review zoom/reflow, text resizing, contrast, non-color cues, touch targets and reduced-motion behavior using suitable measurements or explicit checks.
5. Review screen-reader names, roles, values, error association and status announcements only from accessible-tree or assistive-technology evidence.
6. Separate deterministic results, manual observations, inferred risks and untested requirements. Prioritize blockers and give the smallest next verification step.

## Output contract

Return an **Accessibility gate** with:

1. **Scope and evidence** — target, flow, states, viewport/runtime, tools and supplied artifacts.
2. **Gate status** — `PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED`, with a concise basis.
3. **Findings** — requirement/risk, observed evidence, severity, confidence, user consequence and repair/check.
4. **Coverage matrix** — semantics/names, keyboard/focus, zoom/reflow, contrast, motion, touch and assistive technology; label each `PASS`, `FAIL`, `NOT_RUN`, or `BLOCKED`.
5. **Next steps** — owner-ready checks and evidence needed to close each gap.

## Status rules

- `PASS` is limited to the named scope and checks that were actually performed with evidence. It is not a global accessibility or WCAG-conformance claim.
- `FAIL` requires an observed violation of an explicit requirement or a reproducible barrier.
- `NOT_RUN` means no suitable test/evidence was performed or supplied.
- `BLOCKED` means a named environment, artifact, assistive technology, permission or other dependency prevents testing.
- Never mark missing evidence as a pass. Never infer accessibility from visual appearance alone.

## Quality checks

- [ ] Scope and evidence are explicit.
- [ ] Each result is limited to what its method establishes.
- [ ] Automated and manual evidence are distinguished.
- [ ] The gate status does not imply certification or untested coverage.
