---
name: thesis-challenge
description: 'Stress-test an existing investment thesis by seeking contradictory evidence,
  priced-in expectations, alternative explanations and failure modes. Use after an
  initial thesis exists or when confirmation bias is a material risk. Do not use to
  create the initial thesis from scratch.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.2
  maturity: production
  risk: high
  last_reviewed: '2026-11-06'
---

# Thesis Challenge

## Purpose
Try to falsify the preferred investment case before capital or additional conviction is added.

## Procedure
1. Restate the thesis and its critical assumptions without strengthening it. If the user has not supplied or approved an existing thesis and canonical history has none, stop with `INSUFFICIENT EVIDENCE`; do not invent a baseline thesis or continue as if an initial thesis existed.
2. Identify up to three strongest materially plausible countercases, ranked by expected impact and evidence strength. Return fewer when evidence does not support more; never fill a quota with a fabricated bear claim.
3. For each, state the causal mechanism, dated supporting and contradictory evidence, affected thesis assumption, and potential transmission through revenue, margins, FCF and valuation over an explicit horizon. Give a quantified downside range only when sourced inputs support it; otherwise mark magnitude N/M and explain the missing input. Mark what evidence would disconfirm the challenge.
4. Test what is already embedded in consensus and price. Separate business deterioration, valuation, priced-in expectations, timing and sizing.
5. Classify each challenge `REFUTED`, `UNRESOLVED` or `THESIS_DAMAGING`; an absence of source evidence is `UNRESOLVED`, not a negative fact.
6. Return the strongest supported countercase, ranked challenges, surviving thesis, weakened assumptions and evidence needed next.

## Decision rules
- Lack of contradictory evidence is not proof.
- A correct industry view can still produce a bad investment if priced in.
- Do not manufacture objections with no plausible mechanism.
- Changes in evidence should modify the thesis, not merely confidence wording.
- The output must explicitly report the revised thesis state as `SURVIVES`, `WEAKENED`, `INVALIDATED`, or `INSUFFICIENT EVIDENCE`; do not substitute an ungrounded numeric conviction score or omit the state.

## Output contract
Original thesis and baseline source; strongest countercase; up to three ranked challenges with evidence, causal transmission, horizon, disconfirming evidence and state; priced-in analysis; unresolved tests; separate business, valuation, timing and sizing implications; revised thesis state: SURVIVES / WEAKENED / INVALIDATED / INSUFFICIENT EVIDENCE. Do not issue a buy/sell/short instruction.

## Quality checks
- [ ] Countercase is materially plausible.
- [ ] Contradictory evidence is dated.
- [ ] Price/expectations are considered.
- [ ] Thesis state follows evidence.
- [ ] No more than three challenges; ranking reflects impact and evidence, not rhetorical intensity.
- [ ] Each material downside claim has a dated source and plausible causal path; missing evidence remains unresolved.
- [ ] Business risk, valuation risk, priced-in expectations, timing and sizing are separated; no trading instruction is inferred.
