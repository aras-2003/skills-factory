---
name: job-validity-check
description: 'Verify whether a known job opportunity is still active, current, unique
  and materially unchanged across employer, ATS and aggregator sources. Use before
  spending time on role evaluation, company research or CV tailoring.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: candidate
  risk: low
  last_reviewed: '2026-10-09'
---

# Job Validity Check

## Purpose
Prevent wasted effort on stale, withdrawn, duplicated or materially changed vacancies.

## Use when
- A role is already known and needs freshness validation.
- A discovered role is about to enter deeper evaluation.

## Do not use when
- The user wants new roles discovered.
- The user wants a fit/career decision.
- The user asks to find a new set of roles; route to `job-discovery`.
- The user asks only for factual company research; route to `company-context-research`.

## Inputs
### Required
- role/company or vacancy URL

## Procedure
1. Check the employer or ATS source first.
2. Check at least one secondary source when the primary page is unavailable or ambiguous.
3. Confirm title, location, hiring status and posting identity.
4. Detect duplicates/reposts and materially changed descriptions.
5. Classify: ACTIVE / PROBABLY ACTIVE / UNCLEAR / CLOSED.
6. Return the newest authoritative URL and date evidence.

## Decision rules
- Employer/ATS current listing outranks aggregator copies.
- A missing aggregator page does not imply the role is closed if the employer page is active.
- A repost may be the same requisition; do not double-count without evidence.

## Output contract
Status | Confidence | Authoritative URL | Last verified | Change vs prior version | Evidence | Next step.

## Model guidance
Default model class: **fast**. Escalation normally unnecessary unless sources conflict in a way that changes whether to invest further effort.

## Quality checks
- [ ] Primary source checked when possible.
- [ ] Duplicate/repost risk assessed.
- [ ] Status and confidence explicit.
- [ ] No role-fit decision added.
