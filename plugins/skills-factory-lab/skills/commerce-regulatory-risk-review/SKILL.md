---
name: commerce-regulatory-risk-review
description: 'Triage regulatory, claims, safety and compliance risk for consumer e-commerce
  products. Use to decide whether complexity is proportionate before deeper legal
  review; do not use this skill as legal clearance.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.1.1
  maturity: production
  risk: high
  last_reviewed: '2026-10-09'
---

# Commerce Regulatory Risk Review

Keep each review bound to the named product, market, channel and supplied product facts. Never carry claims, ingredient values, certification, country, or regulatory conclusions from a prior product/case into the current review. If identity or product-specific evidence is missing, return `UNRESOLVED` and request the minimum missing inputs; do not infer a generic product profile.

## Purpose
Identify whether regulatory burden, product classification or claims risk can invalidate an otherwise attractive product thesis.

## Preconditions
Require target jurisdiction/market, product/formulation description and intended claims/use. If any are missing, the regulatory gate is unresolved.

## Inputs and evidence
Prefer current authoritative regulator/legislation/official guidance and qualified professional review where required. Record jurisdiction, product/claims classification hypothesis, source/date and what still requires verification.

## Uncertainty and tool failure
If authoritative sources cannot be checked, return `unresolved`; do not infer clearance from commercial evidence, source-market legality or supplier claims.

## Procedure
1. State jurisdiction, product and intended claims.
2. Identify product/claims classification questions.
3. Identify safety, labelling, certification, import, consumer-protection and category-specific obligations requiring verification.
4. Separate product regulation from advertising/claims risk.
5. Identify evidence or qualified review required before sale.
6. Classify commercial screening risk as low / medium / high / unresolved.

## Decision rules
- Strong demand or margins do not reduce compliance obligations.
- Health/medical-type claims can materially change risk.
- This is commercial triage, not legal clearance.
- Unknown classification/claims can be a launch gate.
- If compliance cost/uncertainty is disproportionate to the opportunity, defer or kill.

## Output contract
Jurisdiction | product/claims classification | risk area | evidence/source | severity | required verification | commercial implication.
Then: regulatory gate = pass / conditional / fail / unresolved.
Never state legal clearance.

## Quality checks
- [ ] Jurisdiction is explicit.
- [ ] Product and claims classification are explicit or unresolved.
- [ ] Obligations are tied to sources/verification, not memory alone.
- [ ] Missing authoritative evidence returns unresolved, not pass.
