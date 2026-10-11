---
name: decision-rights-review
description: 'Map and review critical organisational decision rights, including who
  proposes, decides, executes, advises and escalates. Use when the primary question
  concerns ownership or authority for identified material decisions. Repeated escalation,
  decision circulation and uncertainty about who has final authority are decision-rights
  signals, even when latency is also present. Do not lead a mixed cross-unit handoff/accountability/capacity
  diagnosis before the decision problem is isolated, and do not use merely to create
  a generic RACI.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.1.1
  maturity: production
  risk: medium
  last_reviewed: '2026-10-09'
---

# Decision Rights Review

## Purpose
Clarify ownership and authority for identified important decisions and how those decisions actually move through the organisation.

If the initial problem spans interfaces, accountability and resource/capacity authority across units without a defined decision set, first use the operating-model diagnostic and then apply this skill to the decision classes it exposes.

When the prompt identifies recurring decisions and says the final decision owner is unknown, begin with decision-rights diagnosis. Repeated escalation or delay is supporting context; it does not make bottleneck analysis the lead specialist unless the decision owner/path is sufficiently established and the user's primary question is where elapsed time accumulates.

## Procedure
1. Select the critical decision set relevant to the problem.
2. For each decision, identify proposer, formal decision owner, actual decision owner, mandatory advisers, execution owner and escalation path.
3. Compare formal governance with observed practice.
4. Detect duplicate vetoes, missing owners, shadow decisions, escalation loops and authority/accountability/resource mismatch.
5. Classify each issue by impact on speed, quality and accountability.
6. Separate diagnosis from design:
   - finding;
   - hypothesis;
   - evidence needed;
   - design implication only if evidence supports it.
7. Recommend the smallest evidence-gathering step before governance redesign when ownership is still uncertain.

## Decision rules
- Do not map every operational decision; focus on material decisions.
- One clear decision owner is preferred where feasible.
- Consultation is not decision authority.
- Escalation is not a valid decision mechanism unless destination, trigger, timeframe and authority are explicit.
- Prioritisation authority without funding/capacity authority may be nominal rather than effective.
- Do not prescribe a new owner when the evidence only shows that the current owner is unknown.

## Output contract
Decision | formal owner | actual owner | advisers | executor | escalation | issue | evidence needed | design implication.

Then:
- top decision-rights risks;
- formal-versus-actual practice;
- critical unknowns;
- smallest next diagnostic step.

## Model guidance
Default: **standard**.
Validated on Luna for structured diagnosis and specialist review.
Escalate for highly contested executive evidence, politically sensitive authority redesign, or cross-enterprise decision architecture design.

## Quality checks
- [ ] Formal vs actual practice distinguished.
- [ ] Decision owner explicit or marked unknown.
- [ ] Bottlenecks linked to consequences.
- [ ] Authority, accountability and resources checked together.
- [ ] Diagnosis does not silently become governance redesign.
