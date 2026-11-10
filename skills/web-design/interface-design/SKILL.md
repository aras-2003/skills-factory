---
name: interface-design
description: >
  Design the information hierarchy, navigation, responsive layout, interaction
  states and accessible behavior for a specific product screen or user flow.
  Use when the requested outcome is a design brief for an interface, not an
  implemented page, general report, data visualization or architecture diagram.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.20"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-11-05"
  execution:
    default_model_class: standard
---

# Interface Design

## Purpose

Turn a concrete product or service need into a buildable, evidence-aware interface brief. Define what people need to understand and do before choosing visual treatment or writing implementation code.

## Use when

- The user asks to design a named screen, page, or short interaction flow.
- The deliverable should specify hierarchy, navigation, responsive behavior, states, or accessible interactions.
- A product or runtime target is known, or can be clarified before design decisions are made.

## Do not use when

- The user asks to implement or edit a working page; use the implementation brief and its implementation workflow.
- The main deliverable is a report, slide, chart, diagram, or data visualization.
- The task is to critique an existing design without proposing a replacement interface.
- The request is only for branding, a logo, or a general moodboard.

## Inputs

### Required

- Screen or user-flow goal.
- Intended user and their primary task.
- Target runtime or device context.

## Applicability gate

First decide whether the current request asks for interface design. If it asks to implement/edit a working page or run its tests, do not apply this skill or ask design questions; hand off to the implementation workflow. If loaded explicitly for an isolated test, state briefly that it does not apply and stop. Do not echo the request or emit a design brief. If implementation is requested but its workflow is unavailable, name the missing repository or approved artifact.

### Product-data and capability gate

For an account or order screen, use only records, fields, status names, counts, dates, actions, and routes supplied by the user or an explicitly referenced product source. If those inputs are absent, do not create populated sample records, even when labeled illustrative, hypothetical, or conditional. Use neutral fields such as `[order ID]`, `[status from the approved product mapping]`, and `[next action from approved order rules]`. Do not invent a status-to-action table, CTA, support destination, tab, navigation item, or detail route. State that entry, exit, and destinations are unspecified. A dashboard request does not establish any of those product capabilities.

## Required-context gate

Before designing, check whether the current request or an explicitly referenced source gives all three inputs: (1) screen/flow goal, (2) intended user and primary task, and (3) target runtime/device. Never use narrated prior turns to fill any missing field.

**Quoted-current-message priority:** When a message describes earlier turns and identifies a quoted “current user message,” treat only the text inside that quote as the operative request. The surrounding narrative is test/context metadata, not permission to continue an earlier artifact. Do not acknowledge, summarize, or use any screen, user/task, device, or design decision that appears only in the surrounding narrative. Apply this rule before routing or drafting.

If all three inputs are missing, the entire response must be this one plain-text line, copied verbatim, with no quotation marks, code formatting, introduction, reasoning, summary, translation, paraphrase, or other text:

For an interface-design brief, what screen or flow should change, who will use it and what task should they complete, and should it target mobile, desktop, or a specific runtime?

Do not write anything before or after the question. Do not rewrite any word, clause, or punctuation, and do not replace any clause with inferred context. The question itself names this specialist.

If only some inputs are missing, ask one concise question naming only those fields and identify the `interface-design` specialist in the question itself. When target runtime/device is missing, the question must directly ask whether the screen should target mobile, desktop, or a specific runtime; do not omit this question even when a mobile-first or desktop flow appeared only in narrated prior turns. Every missing field must be asked as something the user can answer, not merely described as unspecified. The question must be the whole response: no introduction, examples, suggestions, checklist, partial design or promise.

Proceed with assumptions/placeholders only when the current request explicitly authorizes them and both goal and target device are clear. Label the narrowest user/task assumption, keep unknown product rules as placeholders, and list assumptions as open decisions. Never infer required context from other chats, saved memory, ambient context, or unreferenced earlier turns. A vague request such as “make the screen better” still needs the missing fields, even if a plausible screen appeared earlier. Continue an earlier artifact only when the operative request explicitly names or asks to revise it.

Product name, industry, and native/web label are not extra required inputs when the goal, user/task, and device are clear. For product-agnostic flows, proceed with limited assumptions and leave product-specific decisions for handoff; do not ask questions that would not change the flow. When a concrete problem observation and user/task/device are clear, design for it and label unverified causes as assumptions instead of blocking on product details.

### Optional

- Existing design system, tokens, components, or screenshots.
- Content, data schema, permissions, and known operational constraints.
- Accessibility requirements, supported devices, localization, and brand constraints.
- Existing user research or analytics. Treat supplied findings as evidence only to the extent their source and scope are known.

## Procedure

1. Confirm the user goal and primary task. Separate supplied facts from assumptions; ask only for missing information that would change the hierarchy or interaction model.
2. Identify the key information users need, the actions they can take, and the decision or outcome each action supports.
3. Define the information hierarchy and screen anatomy. Use existing design-system components and tokens when supplied. Do not invent an established system or silently replace it.
4. Describe navigation, interaction behavior, feedback, validation, permissions, and any destructive or irreversible action.
5. Specify mobile and desktop behavior, including what reflows, collapses, becomes scrollable, or remains persistently available. Do not assume a desktop layout simply scales down.
6. Define loading, empty, error, and unavailable-data states. Include recovery or next actions and state what information remains visible.
7. Specify semantic structure and accessibility behavior: headings, labels, keyboard order, focus, contrast risks, status announcements, reduced motion, and touch-target concerns where relevant.
8. List unresolved decisions, evidence gaps, and handoff questions. Keep this brief at the design level; do not claim that code was built or tested.

For an onboarding or other multi-step flow, include at least one realistic failure path and its recovery, in addition to the successful path. Name the triggering condition only when it is supplied or established; otherwise use a neutral placeholder and identify it as an open product rule.

## Decision rules

- User goals and product constraints outrank decorative convention or optional references.
- Preserve supplied design tokens and accessibility requirements. Flag conflicts instead of silently overriding them.
- Do not invent content, metrics, permissions, user research, records, identifiers, counts, timestamps, or system behavior. Mark each assumption and its impact.
- When the user supplies no data for a design example, show neutral field placeholders such as `[order ID]`, `[delay duration]`, and `[status]`; do not fabricate populated records or operational-looking values. Generate synthetic sample data only when the user explicitly requests a demo or fixture, and label it as synthetic.
- Treat the requested task as the boundary of the product surface. Do not add unprovided navigation destinations, screens, services, states, or actions as if they exist. For an order dashboard, do not assume shipment tracking, delivery estimates, payment changes, cancellations, refunds, returns, address management, support channels, or account settings unless the user or supplied product evidence names them.
- When the requested next action depends on missing product rules, show a neutral placeholder such as `[next action from approved order rules]` and list the required state/action mapping as an open decision. Do not invent sample order statuses or a condition-to-action matrix to fill that gap.
- If design tokens, navigation patterns, or product capabilities are referenced but not supplied, say they are unavailable and make their use a handoff dependency. Do not invent token names or values, component names, or destinations.
- A requested screen or page is not evidence that specific tabs, navigation destinations, actions, account fields, status labels, records, or operational copy exist. When product evidence does not define them, describe the information role generically or use a neutral placeholder; identify any required product mapping as unresolved. Do not present plausible labels or example content as existing product behavior.
- **Navigation provenance check:** Before finalizing the navigation/interaction section, verify every route, destination, entry or exit path, detail-screen link, control label, and next action against the supplied request or an explicitly referenced source. A screen name or account context does not establish an `existing` route or clickable destination. When none is supplied, state that entry, exit, and destinations are not specified and list them as open decisions; do not propose a conventional or assumed route.
- Produce the requested written interface brief only. Do not create an interactive preview, prototype, wireframe artifact, or implementation unless the user explicitly requests that deliverable.
- Do not design a happy path only. Every screen needs explicit loading, empty, and error behavior; describe unavailable-data handling when data is part of the interface.
- Do not prescribe a chart or diagram merely because the screen contains data. If the requested outcome is the visual itself, route to the relevant visualization capability.
- Do not turn the brief into implementation code. A separate approved implementation task owns code changes and runtime validation.

## Output contract

Return a concise **Interface brief** with these sections:

1. **Goal and context** — primary user, task, target runtime, verified inputs, and assumptions.
2. **Information hierarchy** — primary, supporting, and secondary content; what can be deferred.
3. **Screen structure** — sections/components and their purpose, in reading order.
4. **Navigation and interactions** — entry/exit, actions, feedback, validation, and permissions.
5. **Responsive behavior** — mobile and desktop layouts and meaningful behavior changes.
6. **States** — loading, empty, error, and unavailable-data behavior, each with recovery guidance.
7. **Accessibility** — semantics, keyboard/focus, contrast, announcements, motion, and touch risks.
8. **Open decisions and handoff** — unresolved questions, dependencies, and what implementation must verify.

When a required input is missing, follow the required-context gate before drafting the brief unless the user explicitly authorizes assumptions/placeholders in the current request and the goal and target device are clear. In that case, follow the bounded-assumption rule above. Do not omit a section from a valid brief; use “not applicable” with a reason.

The clarification-only response is the sole exception to the eight-section brief: do not emit any brief section until the required context is present. For a valid brief, keep the output textual and do not append a rendered or interactive artifact.

Every valid interface brief must begin with the exact unformatted sentence “I’ll use interface-design for the <screen or flow name>.” Keep the definite article “the” before the name in every valid brief, including when the user used an indefinite article or the name is derived from the requested flow. This is the first line of the response, before any heading, greeting, or other text, regardless of the requested interface type. The next line is “## Interface brief”, followed by the eight sections below. Do not use this opening for clarification-only responses; their single question already names the specialist and must remain the whole response.

**Opening label selection:** If the request names a screen or flow, use that concise noun phrase without its leading article, then place it after “for the”. If it describes a problem and asks you to propose a flow without naming it, derive a short noun phrase from the requested deliverable (for example, “the mobile-first onboarding flow”). Do not omit “the” or extend the opening label with the problem, purpose, benefit, or explanation for the flow. Keep those details in the brief body.

## Quality checks

- [ ] The brief solves the stated user task and distinguishes evidence from assumptions.
- [ ] Information hierarchy and component order are explicit.
- [ ] Mobile and desktop behavior are both described.
- [ ] Loading, empty, error, and relevant unavailable-data states include recovery behavior.
- [ ] Navigation and key interactions have visible feedback and permission boundaries.
- [ ] Accessibility behaviors are concrete enough to validate during implementation.
- [ ] Existing tokens and constraints are preserved or conflicts are surfaced.
- [ ] No implementation, research result, or test is claimed without evidence.
