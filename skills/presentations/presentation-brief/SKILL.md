---
name: presentation-brief
description: >
  Establish the audience, communication objective, intended decision or behavior and constraints before producing a slide deck. Use when someone asks to prepare a presentation from a topic, idea, notes, brief or source documents; do not use for a narrow request to edit a known slide.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-09"
---

# Presentation Brief

## Purpose
Derive a decision-useful, audience-specific, sufficient brief. Presentation production does not begin with a default agenda or template.

## Preconditions
A user has asked for a deck/presentation, or a presentation workflow delegates brief intake. Reuse all already provided context, files and user decisions.

## Procedure
1. Extract **WHAT** topic/problem, **WHO** specific audience and their prior knowledge/potential objections, **WHY NOW** communication occasion, **TO WHAT END** decision, belief or action, and **HOW** live talk, workshop, standalone leave-behind or asynchronous circulation.
2. Capture duration/slide budget, language, evidence/assets available, brand style, target platform, editable/export needs, deadline and confidentiality/tool-sharing constraints when material.
3. Classify purpose: BOARD_DECISION / STRATEGY / BUSINESS_CASE / TRANSFORMATION / TECHNICAL / SALES_PITCH / WORKSHOP / KEYNOTE / TEACHING / RESEARCH_BRIEF; refine if hybrid. Never assume board density suits a keynote.
4. Identify decision-critical missing facts. Ask **up to three compact, high-value questions** only when plausible answers change the storyline, research or output. Do not ask the user to repeat known answers or force a long form.
5. If missing details are noncritical, proceed with stated assumptions, identify what could change them and invite corrections only when necessary. If the core audience or desired outcome is unknown and genuinely changes output, pause **deck generation** while making the smallest useful brief proposal.
6. Establish success test: what must the audience understand/decide/do immediately after the last slide? Define the central audience objection and single governing question.
7. Warn if time/slide cap, source restriction or agenda request conflicts with decision objective; offer the smallest trade-off.

## Decision rules
- A topic is not a communication objective. "AI transformation" with no audience/action is not a sufficient final-production brief.
- User-requested format overrides defaults. Do not insist on PPTX if editable Figma Slides is requested.
- Confirm only consequential interpretation forks; do not make every presentation a bureaucratic approval process.

## Inputs
User idea/notes/initial hypothesis, known context, audience, decision/action, constraints and assets.

## Output contract
Return `Brief{topic,audience,audience_state,purpose,decision_or_behavior,occasion,delivery_mode,duration_or_slide_budget,language,evidence_sources,brand_constraints,privacy,tool_target,export_requirements,success_test,open_questions,assumptions,readiness}`.
Readiness: `READY`, `ASSUMPTIONS_VISIBLE`, `BLOCKED_CRITICAL_CONTEXT`. Give a one-sentence brief back to the caller.

## Evidence requirements
Separate confirmed user context from inference and unverified assumptions. Keep user-supplied material private according to its permissions.

## Failure and uncertainty handling
If critical context is missing, ask directly before generating slides; a rough outline may still be useful if explicitly labelled provisional. If the user supplies a fully specified brief, do not re-interrogate.

## Quality checks
- [ ] Audience, purpose and desired change are explicit.
- [ ] Questions would materially alter the work.
- [ ] Delivery mode and success test drive density/flow.
- [ ] No automatic vendor use or exposure of private material.
