---
name: process-update
description: 'Convert new recruitment-process information into a concise structured
  status update with current stage, evidence, next action, owner/date and changes
  to prior assumptions. Use after recruiter calls, interviews, emails or offer updates.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: candidate
  risk: low
  last_reviewed: '2026-10-09'
---

# Process Update

## Purpose
Keep recruitment tracking current without re-running full analysis.

## Use when
- New recruiter/interview/process information arrives.
- The user wants the tracker/status updated.

## Do not use when
- The new information materially changes role attractiveness and needs full re-evaluation first.
- The user asks for company research or CV tailoring.
- The user asks only to draft a recruiter email/message and did not ask to update a recruitment tracker; draft the message directly without invoking a tracker update.

## Inputs
### Required
- new recruitment information
### Optional
- prior status/evaluation
- tracker schema

## Procedure
1. Extract factual changes: stage, date, people, next step, deadlines, requested artifacts, compensation/process signals.
2. Compare with prior state.
3. Separate new facts from interpretation.
4. Update only affected fields.
5. Flag any information that should trigger `executive-role-evaluator` update.
6. Produce the next concrete action.

## Decision rules
- Do not silently overwrite contradictory prior facts.
- A material change in mandate, reporting line, team, budget, compensation or role scope should trigger evaluator refresh.

## Output contract
Status | Stage | New facts | Changed assumptions | Next action | Owner | Due date | Re-evaluation needed? yes/no + reason.

## Model guidance
Default model class: **fast**.
Escalate only if the update materially changes the career decision or evidence is contradictory.

## Quality checks
- [ ] Facts separated from interpretation.
- [ ] Only changed fields updated.
- [ ] Next action explicit.
- [ ] Re-evaluation trigger assessed.
