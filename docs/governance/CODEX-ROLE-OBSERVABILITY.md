# Codex role routing observability

Status: v1 repository protocol for recording Architect routing decisions in Codex. New sidecars use contract v1.1; existing v1.0 records remain readable. This records evidence visible to the coordinator; it does not add host telemetry or claim that unavailable host values were observed.

## Boundary

Codex owns the decision to delegate and the host call that starts a subagent. The Skills Factory Cloud Next adapter owns MCP tool calls inside that runtime. Its unsigned tool receipts identify tool calls and bind their input/output bytes; they do not report Codex subagent dispatch, effective model, reasoning effort, or the quality of model reasoning. Do not extend or interpret MCP receipts as agent telemetry.

The existing evaluation receipt remains the verdict for a skill/workflow case. A role decision record is a linked evidence sidecar, not a task tracker and not a runtime PASS. Keep GitHub Issue/PR as the work/status source of truth. Do not store prompts, transcripts, credentials, private rubrics, or sensitive tool logs in the sidecar. Use a safe reference and digest when evidence must remain private.

## Routing rule

Evaluate the task after repository inspection and before the first architecture-dependent decision or change. Record both invocation and skip decisions so the evidence set can include missed and unnecessary dispatches.

| Impact | Operational rule | Architect |
| --- | --- | --- |
| A0: routine, low-impact, easy to reverse | Existing deterministic operation; no material design choice | Skip |
| A1: local change using an established pattern and unchanged contracts | No material boundary, consumer, migration, security, or operations choice | Skip |
| A2: choice changes a component boundary, public/shared contract, or material dependency | Need alternatives and compatibility consequences | Invoke |
| A3: multiple components, data shape, migration, security boundary, or operational behavior | Need producer/consumer, rollout, and failure analysis | Invoke |
| A4: broad impact or hard rollback | Need explicit migration, rollback, and risk decision | Invoke |

For A2–A4, request `gpt-6.2-sol` with `high` reasoning effort, subject to host support and authorization. These are requested settings. Record effective model/effort only when the host exposes evidence; otherwise use `UNKNOWN` with a reason. Do not infer an effective model from a profile file, tool argument, or the quality of the response.

An escalation such as A1 → A3 creates a new linked decision at the newly observed signal; preserve the prior valid skip. A host refusal or unavailable role is a blocked/failed attempt, not a skip. Retries have unique attempt IDs linked to the original decision. A user-directed Architect invocation is labeled `USER_REQUEST` and is not counted as a natural-routing success.

## Evidence lifecycle

1. **Decide before dispatch.** Record the impact class, the concrete signal available at that time, safe evidence references, decision time/order, and the first dependent decision/action. Record `INVOKE` or `SKIP` and the reason.
2. **Record the host attempt separately.** For invocation, keep the requested profile/model/effort distinct from host-observed fields. Capture only identifiers and status actually returned by the host. Keep exact host event timestamps nullable; separately record coordinator observations before and after the call as bounds. Do not claim a worker start from an accepted request.
3. **Record completion and disposition.** Link the result using a safe reference and digest when available. Record the host-reported execution state separately from its exact timestamps; if the host omits start/end times, include a reason and the coordinator observation bounds. Record whether the coordinator adopted, adapted, or declined the recommendation and why. Keep pending, failed, cancelled, blocked, and unknown states distinct.
4. **Validate and link.** Validate the JSON sidecar with `python scripts/eval/role_decision_record.py validate`. Store it under `evals/results/role-decisions/` and link it from the relevant Issue/PR. Its `task_reference` may point to an existing evaluation receipt, but do not replace or repurpose that receipt's `execution.tool_trace_path`: that field remains the actual tool trace. A role sidecar is not a substitute for the trace and does not change evaluation PASS/FAIL rules. For a repository-local result artifact, validate the file digest; external/private references remain references unless their bytes are available to the validator.
5. **Review timing independently.** A reviewer first labels expected trigger and timing window from the pre-decision evidence, before inspecting the actual dispatch and outcome. `ON_TIME` means an accepted dispatch is proven to precede the first dependent action; `EARLY` means that dispatch preceded the action but the reviewer judges it earlier than needed; `LATE` requires evidence that the action preceded the decision or dispatch request; an acknowledgment observed after an action does not prove late dispatch. `MISSED` means a qualifying action is proven to follow a `SKIP`; `UNNECESSARY` means the reviewer finds an invocation unnecessary; `CORRECT_SKIP` requires explicit confirmation and no evidence that a qualifying action occurred. Use strict exact times or non-overlapping coordinator bounds. Tied, overlapping, missing, or incomparable timing evidence is `UNKNOWN`; do not infer timing from the final answer.

For natural A0/A1 work, an invocation assessed by an independent reviewer is `UNNECESSARY`; if that review has not happened or evidence is incomplete, use `UNKNOWN`. Do not treat the lack of a reviewer as a finding against the coordinator.

## Interpretation

Report decision correctness, host dispatch, task completion, effective model/effort observation, and recommendation quality as separate measures. A successful MCP call or a correct-looking answer is not proof that the Architect was invoked at the right time. A host-accepted dispatch is not proof of completion. A requested Sol High configuration is not proof that the host used it.

The v1 pilot is useful when sampled tasks include both skips and invocations, including cases independently found to have a missed trigger. Report the observable denominator and unknown count; do not turn unknown observations into a pass rate. Full host telemetry can replace unknowns only if the host later provides a supported, trustworthy receipt for actual spawn configuration and lifecycle.

## Contract scenarios

The validator and behavioral coverage must preserve these distinctions:

- A0/A1 skip: `SKIP`, no dispatch attempt, no Architect execution, and a reviewable reason.
- A2/A3/A4 invoke: decision recorded before the first dependent action; dispatch and completion proven separately.
- Escalation: preserve the initial decision and create a linked record at the new signal.
- Unavailable/denied host or invisible effective profile: preserve `INVOKE`; record the attempt result and `UNKNOWN` host values with reasons.
- Retry: one record per actual attempt, new attempt ID, same immutable decision ID and fields, explicit link to an earlier attempt; duplicate or conflicting terminal evidence is rejected.
- Missing or out-of-order chronology, a source mismatch found during review, missing disposition, or untrusted evidence reference: incomplete/unknown, never an inferred PASS.
- User-requested invocation: visible dispatch evidence, excluded from natural-trigger accuracy.
- Privacy: no raw prompt/transcript or secret-bearing trace; verify the digest of local result files without claiming that an unsigned digest authenticates the host. External/private result content is reported as not verified.
- Compatibility: accept v1.0 receipts under their original rules; v1.1 missing host timestamps require explicit reasons and must not be replaced with shell-clock estimates.
