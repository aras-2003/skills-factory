---
name: interface-design
description: >
  Design the information hierarchy, navigation, responsive layout, interaction
  states and accessible behavior for a specific product screen or user flow.
  Use when the requested outcome is a design brief for an interface, not an
  implemented page, general report, data visualization or architecture diagram.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.4"
  maturity: candidate
  risk: medium
  last_reviewed: "2026-10-27"
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

## Applicability and required-context gates

First decide whether the current request is for interface design. This applicability check comes before the required-context gate below. If the user asks to implement or edit a working page or application, or to run its tests, do not apply this skill and do not ask design-context questions; hand control to the implementation workflow. If this skill was loaded explicitly for an isolated test, state that it does not apply and stop.

## Required-context gate

Before proposing any screen-specific design, verify that the current request or an explicitly referenced source provides all three required inputs: (1) the screen or user-flow goal, (2) the intended user and primary task, and (3) the target runtime or device context.

If any required input is missing, stop and ask one concise question that names every missing input. Do not provide a layout, a partial design, a generic UX checklist, or an assumption in place of missing context unless the user explicitly authorizes assumptions, placeholders, or a provisional concept in the current request. With that authorization, proceed only when the screen/flow goal and target device are clear; label the narrowest reasonable user/task assumption, keep unknown product rules as placeholders, and list the assumptions as open decisions. Never infer those inputs from unrelated chats, profile data, saved memory, or ambient application context.

For this gate, the entire response must be that clarification question. Name only the missing fields (screen or flow, intended user and task, target runtime/device); do not add an introduction, examples, suggestions, a checklist, or a promise of a future deliverable. A request such as “make the screen better” has no identifiable screen, user task, or target runtime and must receive one question asking for those three items.

A product name, industry, or native/web label is not an extra required input when the stated user-flow goal, intended user and primary task, and target device context are already clear. For a product-agnostic flow, proceed with explicit, limited assumptions and list product-specific decisions for handoff. Do not ask for details that would not change the requested flow.

When a user supplies a concrete problem observation and the intended user, goal, and device context are clear, design a flow that responds to that observation. Treat unverified causes as assumptions; do not block the flow by asking for product or platform details that can be left as handoff decisions.

### Optional

- Existing design system, tokens, components, or screenshots.
- Content, data schema, permissions, and known operational constraints.
- Accessibility requirements, supported devices, localization, and brand constraints.
- Existing user research or analytics. Treat supplied findings as evidence only to the extent their source and scope are known.

## Context boundary

- Use design context stated in the current request/conversation or in sources the user explicitly references for this request.
- Do not carry a product, screen, user task, workflow, or design constraint from an unrelated past chat, saved memory, or ambient history into an underspecified request.
- Generic phrases such as “the screen” do not identify a previously discussed screen unless the user explicitly asks to continue or revise that named conversation or artifact.
- The required-context gate applies even when prior or ambient context appears to make a plausible design possible. Ask before offering a layout or general screen-improvement checklist.

## Procedure

1. Restate the user goal and primary task. Separate supplied facts from assumptions; ask for missing information that would change the hierarchy or interaction model.
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

## Quality checks

- [ ] The brief solves the stated user task and distinguishes evidence from assumptions.
- [ ] Information hierarchy and component order are explicit.
- [ ] Mobile and desktop behavior are both described.
- [ ] Loading, empty, error, and relevant unavailable-data states include recovery behavior.
- [ ] Navigation and key interactions have visible feedback and permission boundaries.
- [ ] Accessibility behaviors are concrete enough to validate during implementation.
- [ ] Existing tokens and constraints are preserved or conflicts are surfaced.
- [ ] No implementation, research result, or test is claimed without evidence.
