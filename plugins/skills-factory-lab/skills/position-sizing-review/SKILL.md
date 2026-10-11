---
name: position-sizing-review
description: 'Determine a decision-support position-size band from investment policy,
  thesis strength, uncertainty, valuation, downside, volatility, correlation and current
  portfolio concentration. Use after underwriting and challenge when deciding starter,
  build, hold or reduction sizing. Do not use without portfolio context and policy
  constraints.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.3.1
  maturity: production
  risk: high
  last_reviewed: '2026-10-09'
---

# Position Sizing Review

## Purpose
Separate the decision to own an asset from the decision of how much risk to allocate.

## Procedure
1. Load current portfolio state and applicable investment policy.
2. Read surviving thesis, evidence-sanity status, valuation state, priced-in expectations and key uncertainty.
3. If decision-critical evidence is UNVERIFIED/CONFLICTED, stop numeric sizing and return the exact verification requirement.
4. Parse policy semantics literally:
   - review threshold = mandatory review trigger only;
   - hard cap/ceiling = maximum allowed weight only when explicitly defined;
   - target band = desired range only when explicitly defined.
5. Review downside, volatility/liquidity, correlation and existing thematic exposure.
6. Distinguish current weight caused by a new trade from weight drift caused by price appreciation.
7. Determine whether the state supports no position, starter, building, normal/full, hold or reduction review.
8. Express a policy-consistent size band only when the policy actually defines one.
9. State what evidence would justify increasing or decreasing the band.

## Decision rules
- A review threshold is not a hard ceiling.
- If policy says positions above 8% require explicit review, 9.5% means REVIEW REQUIRED; it does not imply trim-to-8%, mandatory reduction or an 8% provisional ceiling.
- A position above a review threshold may remain above it after explicit review if the actual policy permits that exception.
- High conviction does not override portfolio concentration.
- High uncertainty can justify a small starter even when expected value looks attractive.
- A position that became oversized through appreciation may require review despite intact thesis.
- Strong momentum is not permission to add.
- A surviving business thesis does not imply attractive security valuation.
- Without policy or portfolio state, return requirements instead of inventing a percentage.
- When required policy, portfolio, or risk inputs are missing, return `UNRESOLVED`/`BLOCKED` and the specific inputs needed. Do not emit `0%`, `0.0%`, or another numeric placeholder as a position recommendation; zero is a substantive recommendation, not a missing-data marker.
- Do not recommend ADD/TRIM or an exact numeric band from a case with missing decision-critical evidence.
- Without a verified valuation/priced-in assessment, do not recommend adding to an already-large position.

## Output contract
Lifecycle state; business-thesis state; security-attractiveness state; priced-in context; policy rule type; review-trigger status; explicit cap/band only if actually present; current weight; drift source; constraints; rationale; add conditions; reduce conditions; missing/blocked data.

## Quality checks
- [ ] Policy and portfolio state were used.
- [ ] Review threshold was not converted into a ceiling or trim target.
- [ ] Conviction and sizing are not conflated.
- [ ] Business thesis, valuation and portfolio fit are separate.
- [ ] Market-driven drift is distinguished from a new trade.
- [ ] Unverified critical evidence blocks numeric sizing.
- [ ] No unsupported exact percentage is invented.
