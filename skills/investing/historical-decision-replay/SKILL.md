---
name: historical-decision-replay
description: Use when evaluating historical investment decisions from immutable dated snapshots with explicit no-look-ahead controls and simple baselines.
metadata:
  owner: arkadiusz-kamrowski
  version: 0.1.0
  maturity: candidate
  risk: high
  last_reviewed: '2026-10-27'
---

# Historical Decision Replay

## Purpose
Evaluate whether a defined, frozen investment decision rule would have changed outcomes on a supplied historical sample. This is an audit of past decisions, not a forecast or trade instruction.

## Required evidence
- Immutable decision, thesis, policy, portfolio and market snapshots with source IDs, publication/observation timestamps and a shared timezone.
- A frozen rule version and explicit review cadence, holding horizon, benchmark, fee and slippage assumptions.
- A sample definition fixed before results are examined, including exclusions and survivorship limitations.

If an as-of snapshot is absent, return `BLOCKED_MISSING_SNAPSHOT`; never reconstruct it from current state. Do not use a record in a decision unless its `published_at` is at or before the decision timestamp. Future observations may be used only as labeled outcomes after the decision is frozen.

## Procedure
1. Validate and freeze the sample, decision rules and evaluation assumptions before calculating outcomes.
2. Separate information available at decision time from future outcome data. Reject future-dated decision inputs.
3. Compare the same decision dates and horizons against a named buy-and-hold or index baseline. Apply identical explicit costs; if costs are missing, mark net results blocked.
4. Report counts and denominators, gross and net returns, turnover, drawdown where a complete dated path exists, and event-conditional hit rate only when its event labels were available ex ante.
5. Keep research quality, valuation, sizing and optional timing attribution separate. A favorable return does not validate a low-quality process.
6. Use chronological walk-forward splits; never tune rules on the reported out-of-sample segment. Preserve contiguous time order in stress tests.

## Output contract
State the rule/version, sample and dates, as-of policy, exclusions, costs, baseline, metrics with denominators, uncertainty, and all missing or blocked inputs. Do not invent odds, statistical certainty, taxes, or economic edge. Label short or selected samples as descriptive only. Read only by default; any persistence requires separate authorization and an actual idempotent-write receipt.

## Evaluation boundary
The bundled engine validates timestamp boundaries and deterministic arithmetic for supplied rows. It does not fetch canonical history, adjust prices, model corporate actions, select securities, infer taxes, or certify a walk-forward backtest. Those remain explicit input and review responsibilities.
