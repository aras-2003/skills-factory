---
name: thesis-challenge
description: 'Stress-test an existing investment thesis by seeking contradictory evidence,
  priced-in expectations, alternative explanations and failure modes. Use after an
  initial thesis exists or when confirmation bias is a material risk. Do not use to
  create the initial thesis from scratch.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.1
  maturity: production
  risk: high
  last_reviewed: '2026-10-09'
---

# Thesis Challenge

## Purpose
Try to falsify the preferred investment case before capital or additional conviction is added.

## Procedure
1. Restate the thesis and its critical assumptions without strengthening it. If the user has not supplied or approved an existing thesis and canonical history has none, stop with `INSUFFICIENT EVIDENCE`; do not invent a baseline thesis or continue as if an initial thesis existed.
2. Identify the strongest competing explanation for the same facts.
3. Search for contradictory operating, industry, valuation and market evidence.
4. Test what is already embedded in consensus and price.
5. Distinguish thesis risk, timing risk and sizing risk.
6. Classify each challenge as refuted, unresolved or thesis-damaging.
7. Return surviving thesis, weakened assumptions and evidence needed next.

## Decision rules
- Lack of contradictory evidence is not proof.
- A correct industry view can still produce a bad investment if priced in.
- Do not manufacture objections with no plausible mechanism.
- Changes in evidence should modify the thesis, not merely confidence wording.
- The output must explicitly report the revised thesis state as `SURVIVES`, `WEAKENED`, `INVALIDATED`, or `INSUFFICIENT EVIDENCE`; do not substitute an ungrounded numeric conviction score or omit the state.

## Output contract
Original thesis; strongest countercase; contradictory evidence; priced-in analysis; unresolved tests; revised thesis state: SURVIVES / WEAKENED / INVALIDATED / INSUFFICIENT EVIDENCE.

## Quality checks
- [ ] Countercase is materially plausible.
- [ ] Contradictory evidence is dated.
- [ ] Price/expectations are considered.
- [ ] Thesis state follows evidence.
