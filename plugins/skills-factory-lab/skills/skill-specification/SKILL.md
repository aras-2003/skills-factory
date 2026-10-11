---
name: skill-specification
description: 'Decide whether a repeatable task should become an Agent Skill and define
  its behavioral contract before implementation. Use when proposing a new skill, splitting/merging
  skills, or when an existing skill has unclear scope, trigger conditions, inputs,
  outputs or boundaries.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.0.1
  maturity: production
  risk: low
  last_reviewed: '2026-10-09'
---

# Skill Specification

## Purpose

Prevent premature skill creation and define a testable contract before instructions are written.

## Procedure

1. Define the recurring user goal in one sentence.
2. Confirm recurrence: identify at least 2–3 realistic situations where the same method applies.
3. Decide the correct abstraction:
   - use a **project instruction** for project-specific context or policy;
   - use a **script/tool** for deterministic calculation or transformation;
   - use a **workflow** for orchestration across multiple independently useful stages;
   - use a **skill** for one reusable reasoning/execution/control method.
4. Define trigger conditions in user-goal language.
5. Define near-miss and competing cases that must not trigger. State the concrete user-goal signal and one realistic adjacent request that belongs to a named competing skill or to no skill; do not leave trigger conditions implied by the proposed name or domain alone.
6. Define required and optional inputs.
7. Define preconditions.
8. Define the output contract.
9. Define stop, ask, decline and escalation conditions.
10. Identify tool, connector, script, reference and runtime dependencies.
11. Identify evidence/verification requirements.
12. Assign risk: low / medium / high.
13. Decide whether the output is a substantial decision report. If yes, define report-composition needs: sections, inline visual slots, progressive disclosure and target (chat-native / rich integrated report / text fallback).
14. Decide which local visuals (chart, diagram, interactive component, Figma/deck) materially improve particular sections.
15. Produce candidate test prompts before authoring.

## Output contract

Return:

### Skill candidate
- Proposed name
- Domain
- Class: reasoning / execution / control
- Problem solved
- Why a skill is the right abstraction

### Trigger boundary
- Should trigger when
- Should not trigger when
- Competing skills

### Contract
- Required inputs
- Optional inputs
- Preconditions
- Procedure summary
- Output
- Report-composition affordances / integrated report target when useful
- Inline visual affordances / preferred renderer class when useful
- Stop/escalation rules
- Evidence/tool requirements

### Risks
- Failure modes
- Security/surprise concerns
- Portability concerns

### Candidate eval cases
At least:
- direct positive;
- indirect positive;
- realistic near-miss negative.

## Quality checks

- Do not create a skill merely because a prompt can be saved.
- Do not embed user-specific or project-specific facts that belong in context.
- Do not combine tasks with different triggers or success criteria.
- Do not hide deterministic algorithms in natural-language instructions when code is more reliable.
- Do not proceed if the output cannot be specified well enough to test.
