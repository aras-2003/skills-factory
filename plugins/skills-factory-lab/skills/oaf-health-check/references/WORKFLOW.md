# OAF Health Check Workflow

## Purpose

Run a selective organisational architecture diagnostic across OAF domains without turning OAF into one giant skill.

## Entry criteria

Use when the user asks for a broad diagnosis of how strategy, organisation, decisions, architecture and execution fit together.

Do not run every skill by default.

## Stage 1 — Frame the decision problem

Clarify:
- what outcome is failing or at risk;
- where symptoms appear;
- what evidence exists;
- what decision the diagnostic must support.

If the request is already narrow, route directly to the relevant OAF skill and stop.

## Stage 2 — Select diagnostic domains

Route only where evidence suggests a material issue:

- Strategy disconnected from execution -> `strategy-to-execution-diagnostic`
- Central/local or structural/interface problems -> `operating-model-review`
- Slow/unclear decisions -> `decision-rights-review`
- Excessive/weak governance -> `governance-design` after diagnosis
- Capability/organisation/technology misalignment -> `architecture-review`
- Capability-map quality/usefulness issue -> `capability-map-review`
- Initiative overload or prioritisation conflict -> `portfolio-prioritization`
- Reporting without learning/adaptation -> `evidence-loop-review`

## Stage 3 — Diagnose before design

Run diagnostic/review skills before design skills.

Do not use `governance-design` or `transformation-blueprint` until the relevant problem is sufficiently evidenced.

## Stage 4 — Cross-domain synthesis

### Normalize specialist findings to the evidence scope

Before creating any organisational claim, translate each specialist finding into the scope actually supported by its evidence:

- `not supplied / not verified / insufficient for this review` is a **review-state limitation**, not an organisational absence;
- a specialist's minimum evidence list identifies what the review needs next; it is not evidence that the organisation lacks those fields, owners, mechanisms or records;
- `organisation lacks X` requires evidence about the organisation showing that X is absent in the reviewed scope;
- when organisational absence is plausible but not established, keep it as a hypothesis to test.

Example: if `portfolio-prioritization` cannot rank because comparable outcome, owner, cost, capacity or dependency evidence was not supplied, the supported conclusion is: **this review cannot rank the initiatives from the available evidence**. It is not: **the portfolio has no comparable data**.

Build a short claim ledger before writing prose. Every material statement must be one atomic claim with four fields:

`claim | epistemic status | evidence | confidence rationale`

Calibrate confidence per claim to evidence quality, scope and sample coverage: use `high` only when direct, sufficiently representative evidence strongly supports the specific claim and credible alternatives have been checked. High confidence is allowed when those conditions hold; do not mechanically downgrade strong observed evidence. Thin, indirect, conflicting, or single-case evidence remains medium/low and should narrow the claim.

Allowed epistemic status:
- `observed` — direct paraphrase of the input or evidence actually collected;
- `supported` — mechanism directly supported by reviewed evidence;
- `hypothesis` — plausible mechanism not yet established;
- `implication` — possible consequence not directly observed.

Do not combine an observation with a hypothesis or implication in the same claim. Unknown reviewer knowledge is not evidence that the organisation lacks an owner, mandate, mechanism or process.

A roadmap/outcome disconnect establishes only that disconnect. It does not by itself establish:
- absence of a common evaluation mechanism;
- missing ownership;
- failed evidence-to-action process;
- unclear organisational mandate.

Cross-domain synthesis may connect claims, but the connection itself is a hypothesis unless directly evidenced.

## Stage 5 — Prioritise structural changes

Separate:
1. critical blockers;
2. foundational changes;
3. local improvements;
4. unresolved questions.

When the input contains symptoms but not mechanism evidence, the next step is a bounded evidence sample that can discriminate between the leading hypotheses. Select a small representative set of recent initiatives, priority changes, decisions, reviews or interface events and inspect only the evidence needed to test the suspected mechanism.

Do not require complete initiative cards, decision maps or action decisions for the whole portfolio before identifying the mechanism. A bounded sample is a test of hypotheses, not proof that the sample will be sufficient. State what the sample can discriminate, what result would support or weaken each hypothesis, and expand only if the evidence remains ambiguous.

Avoid producing a long transformation backlog from weak evidence.

## Stage 6 — Design only what is ready

When diagnosis is sufficient:
- use `governance-design` for governance-system changes;
- use `transformation-blueprint` for cross-domain sequencing and mobilisation.

## Output contract

Keep the answer compact. Reuse the same epistemic structure in every section.

### Executive diagnosis

Write 2–4 atomic claims. For each use:

`[status | confidence] claim — evidence: <specific input/evidence>; confidence because: <why this evidence is sufficient/limited>`

Do not write an unlabeled narrative summary that introduces new mechanisms.

### OAF heatmap

| Domain | Claim | Epistemic status | Confidence | Evidence / confidence rationale |
|---|---|---|---|---|

Use one claim per row. If an observed symptom suggests a causal mechanism or consequence, put that mechanism/consequence in a separate row with its own status and confidence.

### Leading hypotheses

List only hypotheses that materially change the next evidence step. For each state what evidence would strengthen or weaken it.

### Recommended next action

Define the smallest evidence sample that can test the leading hypotheses. State:
- what will be sampled;
- which hypotheses it can discriminate;
- what evidence would support/weaken each;
- that the sample may remain inconclusive and may need expansion.

Do not claim that a bounded sample will resolve the mechanism before seeing its evidence.

## Pre-finalization epistemic check

Before returning the answer, inspect every material sentence and every heatmap cell:

1. Can this claim be traced to a specific input statement or collected evidence? If yes, cite that basis and use `observed/supported`.
2. If not, is it a mechanism? Use `hypothesis`.
3. If not, is it a downstream effect? Use `implication`.
4. Does one sentence contain more than one epistemic type? Split it.
5. Does confidence apply to exactly one claim and have an evidence rationale? If not, rewrite it.
6. Does any specialist evidence-readiness gap describe what was not supplied or verified? Keep it as a review-state limitation unless organisation-level evidence proves absence; otherwise express organisational absence only as a hypothesis.
7. Does next action promise that a sample will decide the issue? Rewrite as a test that may remain inconclusive.

If any material claim cannot pass this check, do not finalize it as fact.

## Stop conditions

Stop when:
- the decision problem is narrow enough for one specialist skill;
- evidence is insufficient for cross-domain claims;
- additional OAF domains would add breadth but not decision value.

## Integrated report presentation
Render the report directly in the chat response by default. External HTML/PDF/Figma/deck/file output is allowed only when the user explicitly requests that artifact or format.

After diagnosis, call `report-composer` for one executive diagnostic report.

Default profile:
- executive diagnosis;
- domain findings;
- evidence-based heatmap only where dimensions are genuinely comparable;
- causal/dependency interpretation with inline map;
- highest-leverage gaps;
- next diagnostic/design gate;
- evidence and unknowns.

Use `visual-output-design` for local diagrams/heatmaps. Do not return a separate diagram pack that duplicates the diagnosis unless explicitly requested.
