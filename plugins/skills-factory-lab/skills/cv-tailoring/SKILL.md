---
name: cv-tailoring
description: 'Tailor an approved mastery CV to one specific executive technology role
  while preserving factual accuracy, seniority and evidence. Use after cv-gap-analysis;
  do not invent experience, inflate scope or optimize for keywords at the expense
  of credibility.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: candidate
  risk: medium
  last_reviewed: '2026-10-09'
---

# CV Tailoring

## Purpose
Produce a role-specific CV variant that improves relevance without weakening factual integrity.

## Use when
- A role is worth pursuing.
- An approved mastery CV and gap analysis exist.

## Do not use when
- There is no authoritative base CV.
- The user asks for unsupported experience to be added.

## Inputs
### Required
- mastery CV
- target role description
### Recommended
- cv-gap-analysis output

If the user refers to a stored “base CV” but multiple CVs are available, identify the approved mastery CV before drafting. Do not silently merge facts from several CVs. If the authoritative CV is unavailable or ambiguous, ask the user to select or provide it. If the job description is missing, ask for it or clearly limit the draft to the information supported by the role title; do not imply that title alone establishes the role's mandate.

## Procedure
1. Establish the approved mastery CV as the sole source of candidate facts. A prior tailored CV, generated draft, recruiter summary or other secondary document may help locate a question, but cannot substantiate a claim unless the user explicitly approves it as a source.
2. Before drafting, check each material claim that will be retained or emphasized against the mastery CV. For numbers and leadership claims, record both the value and what it measures (for example, organization size, direct reports, co-led team, governance reach or program participants).
3. Preserve identity, dates, employers, titles and factual achievements. Keep distinctions such as led/co-led/contributed/influenced, direct management/organizational reach, and portfolio oversight/program participation exactly within the source evidence.
4. Reorder emphasis around the role's highest-value requirements. Rewrite the summary and selected bullets only to surface relevant mandate, scale, outcomes and technology breadth that the source supports.
5. Strengthen evidence density using existing facts; do not strengthen the underlying claim. Never transfer a number from one scope to another or add a number found only in a secondary draft.
6. Remove low-value detail only when it improves fit and does not distort history.
7. Run a final claim-by-claim accuracy pass against the approved mastery CV. Omit unsupported material claims or label them as needing confirmation; do not silently keep them because they appeared in an earlier tailored version.

## Decision rules
- Factual truth outranks ATS optimization.
- Reframing is allowed; fabrication is not.
- Never inflate team size, budget, reporting line, ownership or business outcome.
- A supported number does not support a different scope: organization headcount is not personal span of control; governance reach is not line management; program size is not team size; portfolio oversight is not proof of a project count.
- When a material claim cannot be traced to the approved mastery CV, omit it or ask for confirmation. Do not use a second generated/tailored CV to close the evidence gap.

## Output contract
Return: tailored summary, changed bullets/sections, retained critical evidence, removed/de-emphasized items, and a change log with rationale. Include a concise source check for material experience claims, marking each as supported, carefully reframed, omitted, or awaiting confirmation. Do not reproduce sensitive source details that are not needed in the CV.

## Model guidance
Default model class: **standard**.
Escalate only for major restructuring across multiple CV versions or nuanced executive-positioning trade-offs.

## Quality checks
- [ ] Every material claim traceable to mastery CV/source.
- [ ] The approved mastery CV is the source of candidate facts; prior tailored drafts did not introduce or substantiate claims.
- [ ] Each material number retains its original subject and scope.
- [ ] No scope inflation.
- [ ] Seniority and executive narrative improved.
- [ ] Change log included.
