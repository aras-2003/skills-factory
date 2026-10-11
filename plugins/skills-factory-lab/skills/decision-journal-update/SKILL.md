---
name: decision-journal-update
description: 'Append a structured investment decision record capturing what was known,
  decided and expected at the time, then later support ex-post review of thesis, timing
  and sizing quality. Use after meaningful buy/add/reduce/exit/watchlist decisions
  or when reviewing past decision quality. Do not rewrite old decisions using hindsight.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: production
  risk: medium
  last_reviewed: '2026-10-09'
---

# Decision Journal Update

## Purpose
Create the learning loop required to distinguish skill from luck and identify recurring decision errors.

## Procedure
1. Capture decision timestamp, instrument, action/lifecycle state, price/context, position weight and horizon.
2. Store the contemporaneous thesis, assumptions, catalysts, risks, kill criteria and confidence.
3. Link evidence and source dates used at decision time.
4. Append the record only after an explicit user request to save it and a verified safe canonical target. Drafting or discussing a decision is not permission to persist. Never write to production during controlled tests, previews, or an unknown write boundary. Never alter the original rationale after outcomes are known.
5. On review, add a separate outcome record: thesis quality, timing quality, sizing quality, process adherence and lessons.
6. Distinguish a good process/bad outcome from bad process/good outcome.

## Decision rules
- Outcome does not retroactively change what was knowable.
- P/L alone is not decision quality.
- Missing rationale at entry is itself a process defect.
- Hindsight commentary must be stored separately.
- A request to analyze, summarize, or draft a decision journal entry does not itself authorize a canonical write.

## Output contract
Decision record ID; contemporaneous context; thesis; action; sizing rationale; invalidation; evidence links; later review fields when applicable.

## Quality checks
- [ ] Decision-time and review-time fields are separated.
- [ ] Append-only behavior is explicit.
- [ ] P/L is not the sole quality metric.
- [ ] Evidence provenance is retained.
