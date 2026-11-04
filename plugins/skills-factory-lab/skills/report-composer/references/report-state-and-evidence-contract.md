# Report state and evidence contract

This contract separates analytical completeness, renderer execution, client display and runtime evaluation.
The model must never collapse these into one inferred success status.

## 1. Analysis state

Allowed values:
- `COMPLETE`: all decision-critical claims required by the selected workflow are supported.
- `PARTIAL_EVIDENCE`: the report can still provide useful analysis, but at least one decision-critical comparison, attribution, policy check or thesis check is unavailable.
- `BLOCKED_ANALYSIS`: missing evidence prevents the core requested analysis from being performed truthfully.

This state is independent of chart delivery.

## 2. Renderer capability state

Allowed values:
- `AVAILABLE`
- `UNAVAILABLE`
- `UNKNOWN`

Capability state only says whether a qualifying renderer can be invoked.

## 3. Renderer execution state

Allowed values:
- `NOT_REQUIRED`
- `NOT_ATTEMPTED`
- `BLOCKED_NO_RENDERER`
- `PAYLOAD_RENDERED`
- `FAIL_RENDERER_INVOCATION`

`PAYLOAD_RENDERED` means the renderer returned a valid, verifiable image/chart payload.
It does not mean the client UI displayed it.

## 4. Client display state

The language model does not observe the end-user client rendering surface.

Allowed model-owned value:
- `NOT_OBSERVABLE`

Do not emit `UI_CONFIRMED`, `UI_RENDER_UNCONFIRMED`, `VISIBLE`, `BROKEN` or equivalent as model-owned facts.

Client display may be evaluated only by:
- an external test harness with client telemetry/screenshot evidence; or
- explicit user feedback about what is visible.

Do not infer client display from tool-call success, image payload success, placeholder creation or absence of an exception.

## 5. Runtime validation state

This belongs to the runtime evaluation harness, not ordinary report composition.

Allowed values:
- `PASS`: external evidence confirms the required client-visible output.
- `FAIL`: a required capability or invocation failed.
- `PENDING_CLIENT_VALIDATION`: a valid payload was produced but client display has not been externally verified.

The model may describe the renderer payload as ready, but must not claim runtime visual-floor PASS without external client evidence.

## 6. Evidence classes

Every decision-relevant factual claim should resolve to one of:
- `CANONICAL`: read from the configured canonical record store.
- `USER_PROVIDED`: supplied directly by the user or prompt.
- `EXTERNAL_VERIFIED`: verified against an external dated source.
- `DERIVED`: calculated reproducibly from identified inputs.
- `UNKNOWN`: support is insufficient.

For `DERIVED` claims, preserve enough inputs/formula to reproduce the result.

When the user asks for causes, patterns, findings or user behavior but supplies no
observations, dataset or source, do not invent an observation to make the report
feel evidence-based. State that the evidence was not supplied; classify the
underlying factual claim as `UNKNOWN`. Any possible causes may be offered only
as clearly labeled hypotheses or examples, never as observations, research
findings, or facts about the user's product. Do not write phrases such as
"available observation shows" unless the observation is actually present and
its source/provenance is identified.

A user-provided metric that cannot be reproduced from the visible inputs remains `USER_PROVIDED`; do not relabel it `DERIVED`.

## 7. Causal attribution gate

Claims such as:
- market-driven drift;
- trade-driven drift;
- thesis deterioration caused by a specific event;
- exposure changed because of a specific transaction or price move;

require evidence that distinguishes the candidate causes.

For portfolio drift attribution:
- current state alone is insufficient;
- current + prior snapshots can establish change, but not necessarily cause;
- transaction evidence plus comparable prior/current state, or an explicit canonical attribution record, is required to classify change as trade-driven vs market-driven;
- an empty, zero-row, incomplete or unavailable transaction query is not proof that no transaction occurred;
- if distinguishing causal evidence is missing, attribution is `UNKNOWN`.

Never infer market-driven drift, no-trade drift, or "no transaction occurred" merely because no transaction rows were observed. Describe the limitation as insufficient evidence to distinguish candidate causes, not merely as an empty transaction table.

## 8. Contradiction check

Before final output, check that:
- limitations do not contradict earlier claims;
- missing history is not followed by a historical attribution;
- unavailable policy is not followed by a policy-breach claim;
- unavailable thesis records are not followed by a thesis-status claim;
- user-provided metrics are not presented as independently verified or derived;
- renderer payload success is not described as client-visible success.

If a contradiction exists, weaken or remove the unsupported claim before composing the report.

## 9. Presentation rules

For normal reports:
- keep the analytical report useful even when evidence is partial;
- summarize missing canonical evidence once in a compact limitations section;
- do not repeat the same unavailable records in multiple sections;
- do not expose internal state-machine jargon unless diagnostic output is requested.

For runtime diagnostics, use:
- analysis_state
- capability_status
- renderer_execution_status
- client_display_status
- runtime_validation_status only when evaluated externally

Never invent status variants outside the enums in this contract.
