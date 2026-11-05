---
name: experience-design-routing
description: Use as the UI/UX task router when a user asks for interface design, visual critique, design handoff, accessibility review, or visual regression; route to the existing specialist skill.
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.5
  maturity: candidate
  risk: low
  last_reviewed: '2026-11-02'
---

# Experience Design Routing

## Purpose
Select the smallest existing design capability for an explicit UI/UX task. This router does not create a new report, presentation, visualization or implementation architecture.

## Procedure
1. Classify the requested deliverable before checking which artifacts are available.
2. For an explicit request to implement, build, edit, debug or test code in an existing application, treat it as an implementation task. State concisely that `interface-design` does not apply and direct the request to the application's coding workflow. Do not replace implementation with a design-only brief or ask UX discovery questions. If the coding workflow cannot proceed, request only the missing implementation inputs (such as repository access or an approved design) and state that edits/tests have not run.
3. For an active design/review request, route only as follows:
   - Design a new screen or short product flow: `interface-design`. A request to design a screen that includes role-based access, permission states, or accessible behavior remains an interface-design request; mentioning accessibility or permissions does not turn it into an implementation accessibility review.
   - Critique a supplied visual artifact and propose repairs: `design-critique`.
   - Convert an approved concept into an engineering handoff: `implementation-brief`.
   - Review accessibility evidence and gaps for an existing implementation: `accessibility-gate`.
   - Compare a rendering to an approved baseline: `visual-regression-review`.
4. If intent is genuinely unclear between design and implementation, ask one narrow question. Do not infer permission to edit code from a design request.
5. Before routing a design request to `interface-design`, check its required-context gate against the current request and explicitly referenced sources: screen/flow goal, intended user and primary task, and target runtime/device. Ask only about fields that are genuinely missing. When runtime/device is missing, directly ask whether the target is mobile, desktop, or a specific runtime. Do not substitute product name, industry, or audience discovery for these required fields, and do not ask for fields already supplied. If all three are present, proceed without a clarification question.
6. If the primary output is a report, presentation, chart, diagram or data analysis, keep its existing domain/output workflow. Use UX skills only when the user explicitly asks for interface design or review.
7. Preserve each domain's evidence IDs, source revision, as-of date, uncertainty and output contract. A visual handoff may reference those facts but must not replace or rewrite their provenance.
8. Do not change the requested response format, render an artifact, or invoke a design capability for ordinary text, calculations or a single chart request.

## Output contract
For an explicit implementation-only request, say that `interface-design` does not apply and route to the coding workflow; do not emit a design brief. Ask only for missing inputs that block implementation, and never claim code or tests changed unless they actually did.
For an active design request with enough context to proceed, name the selected specialist in the first sentence and identify the supplied artifact or target it will use. Do not imply the specialist has already run. When `interface-design` lacks required context, ask only for the missing required fields from its gate (screen/flow goal, intended user and primary task, target runtime/device). In particular, whenever runtime/device is missing, directly ask whether to target mobile, desktop, or a specific runtime. The single question must name `interface-design` itself, with no introductory sentence. For other specialists, if a required artifact or approval is missing, state the missing prerequisite and stop at that boundary.
For a near-miss, preserve the user's requested deliverable by name (for example, “executive report” or “line chart”), continue its existing workflow, and preserve requested evidence and citations. Do not name or invoke a design specialist when the router says `should_trigger: false`.
When inputs are missing for other specialists, make the routing visible without claiming execution: “I’ll use `<specialist>` for `<target>`. Please provide `<missing prerequisite>` so I can proceed.” For a near-miss, keep the original output type visible while asking for inputs (for example, “I’ll prepare the executive report once you share the findings and citations.”).

## Portability boundary
This is a routing contract, not evidence that a capability is installed or invoked on Chat, mobile, Cloud or Codex. Confirm the actual host surface and tool receipt before recording runtime acceptance; an unsupported surface is `NOT_RUN`, not PASS.
