---
name: portfolio-prioritization
description: >
  Structure transparent prioritisation of initiatives using agreed strategic, value, risk, capacity and dependency criteria. Use when a portfolio needs comparable decisions; use deterministic calculation for scoring where possible.
metadata:
  owner: arkadiusz-kamrowski
  version: "1.0.0"
  maturity: production
  risk: medium
  last_reviewed: 2026-09-30
  execution:
    default_model_class: fast
    validated_models:
      luna:
        status: pass
        validated_on: 2026-09-30
        validated_use:
          - evidence readiness
          - prioritisation framing
          - specialist review
---

# Portfolio Prioritization

## Purpose
Turn competing initiatives into a transparent decision set without creating false precision.

## Procedure
1. Confirm the portfolio decision objective and hard constraints.
2. Check whether initiatives have enough comparable evidence to support ranking.
3. If evidence is insufficient:
   - do not score;
   - define the minimum comparable data set;
   - classify mandatory work;
   - identify dependency and capacity data needed.
4. If evidence is sufficient, define a small set of non-overlapping criteria and agreed weights.
5. Separate factual inputs from judgment scores.
6. Normalize scoring scales.
7. Calculate weighted totals and sensitivity only through an actually executed deterministic calculator (a host code-execution tool is acceptable when formula, inputs and execution evidence are recorded). If execution is unavailable, return `NOT_CALCULATED` with the agreed criteria, weights, and qualitative constraints; do not generate numeric weighted scores, ranks derived from scores, or sensitivity values using model-only arithmetic.
8. Surface dependencies, mandatory work and capacity constraints outside the score.
9. Produce options and sensitivity, not a false single truth.

## Decision rules
- Mandatory/regulatory/security/continuity work should not be hidden inside normal value scoring.
- Dependencies and capacity can override rank order.
- Capacity is normally a constraint or scenario condition, not simply another value point.
- Low-confidence inputs must remain visible in the result.
- Do not invent weights or initiative scores when the evidence is missing.
- Criteria examples are design prompts, not an OAF universal standard.
- LLM interprets; code calculates.

## Evidence readiness minimum
For each initiative, seek:
- accountable sponsor/owner;
- strategic outcome supported;
- value hypothesis and measurable outcome;
- mandatory status and rationale;
- cost/funding profile;
- capacity demand;
- urgency/cost of delay;
- dependencies;
- risk exposure/reduction;
- confidence and evidence source;
- consequence of delay/non-delivery.

## Output contract
If evidence is insufficient:
- factual inputs;
- judgments/inferences;
- missing data;
- minimum evidence needed;
- portfolio decision postures;
- next evidence-normalisation step.

If evidence is sufficient:
Initiative | criteria scores | weighted score | confidence | dependencies | mandatory? | capacity impact | decision note.

Then: portfolio options and sensitivity.

## Model guidance
Default: **fast** plus deterministic calculation.
Validated on Luna for evidence-readiness and prioritisation framing.
Escalate for ambiguous strategic value, highly coupled portfolios, or contested executive trade-offs.

## Quality checks
- [ ] No false scoring without comparable evidence.
- [ ] Mandatory work separated.
- [ ] Dependencies/capacity explicit.
- [ ] Calculation deterministic when scoring is used.
- [ ] Confidence remains visible.
