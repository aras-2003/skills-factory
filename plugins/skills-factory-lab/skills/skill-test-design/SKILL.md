---
name: skill-test-design
description: 'Design and maintain routing, behavioral, edge-case, adversarial, and
  regression tests for an Agent Skill. Use after a skill draft exists, when changing
  its trigger or procedure, or when converting a real failure into a permanent evaluation
  case.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.3.1
  maturity: draft
  risk: low
  last_reviewed: '2026-10-09'
---

# Skill Test Design

## Purpose

Build a small, discriminating suite that tests the approved skill contract. Cases should reveal routing errors, missing behavior, unsafe actions and regressions; they should not merely echo instructions or reward one preferred wording.

## Inputs and scope

Identify:
- skill name/version and approved behavioral contract;
- description and neighboring skills that may compete;
- intended user, context, tools and action permissions;
- known incidents, high-impact failure modes and the acceptance decision the tests support.

If the contract is not agreed, clarify or flag that gap before encoding assumptions into tests. Use skill-specification for unresolved capability/scope questions.

## Design procedure

1. **Map contract to observables.** Turn each important requirement, prohibited behavior, boundary and stop condition into an observable expectation. Keep implementation preference separate from outcome.
2. **Separate test layers.**
   - **Routing:** should-trigger and should-not-trigger cases, including direct, indirect, realistic near-miss and competing-skill prompts.
   - **Behavior:** task quality and procedure under valid conditions.
   - **Robustness:** incomplete/ambiguous input, conflicting or stale evidence, tool failure/partial results, edge cases and adversarial content as relevant.
   - **Regression:** concrete previous failures, preserved as durable cases.
3. **Cover the change.** Description-only changes require positive and negative routing regression. Procedure/output changes require behavior coverage. Changes to tools, permissions, claims or external actions require failure and boundary coverage. Do not add unrelated tests without a risk-based reason.
4. **Choose cases for discrimination.** Use plausible prompts that separate the target skill from its closest alternatives. A negative should share enough domain vocabulary to be a real routing challenge. Avoid trivia and unrelated prompts.
5. **Write stable assertions.** Prefer semantic must/must-not expectations, required evidence or fields, explicit route, and required stop/action boundaries. Avoid exact wording, hidden reasoning, cosmetic preferences and tests that a vaguely on-topic answer could pass. Make every case executable without evaluator guesswork: include the exact user input, required fixture/setup, expected behavior, forbidden behavior, evidence source and a discriminating near-miss/competing route where routing is under test. Avoid generic expectations such as “be accurate”, “do research”, or “handle edge cases”.
6. **Set severity and evidence.** Mark which cases are smoke, routing, behavioral, regression or high-risk in the case ID/name or suite documentation. Keep high-risk failures visible; do not hide them inside an average.
7. **Validate the cases.** Ensure inputs are self-contained, expected outcomes are unambiguous, references/fixtures exist, case IDs are unique, and the schema is accepted by the repository validator.
8. **Define execution evidence.** For every criterion that requires an actual browser, API, runtime or external action trace, specify the observable receipt needed (tool trace, URL or resource, check time, and observed result as relevant). A plan or narrative claim is not execution evidence.
9. **Review for bias and leakage.** Do not disclose rubric-only facts to an unassisted executor when the evaluation claims to be unassisted. Avoid giving the model the answer in the prompt. Ensure negative cases do not test a different capability merely to make the target fail.
10. **Keep suites maintainable.** Remove duplicates only when they test the same distinction. Retain a regression while the failure mode remains relevant; document any retired case and reason. Re-run impacted cases when skill behavior or evaluator rules change.

## Execution evidence states

Design assertions so execution state cannot be mistaken for outcome:
- `NOT_RUN`: execution has not started, including a queued job with no runner/steps.
- `BLOCKED` / `NOT TESTABLE`: execution cannot test the criterion because a required runtime, tool or fixture is unavailable. Record which prerequisite is unavailable.
- `UNVERIFIED`: execution ran, but its evidence does not establish the criterion or the required status; name the missing/ambiguous evidence. Do not use this to describe a browser that was unavailable.
- `PASS` / `FAIL`: use only after observing sufficient evidence in an execution that actually ran. A listing status can be PASS/FAIL only after the page was inspected and an observed status was compared with the expected one.
- If a criterion explicitly requires checking a live source, a model explanation or stated plan cannot satisfy it. Define the trace, source/URL, check time and observed value needed to pass.

## Minimum production-candidate coverage

For a new production candidate, include at least:
- two positive routing cases with distinct realistic wording;
- two realistic negative/competing-skill cases;
- one incomplete-input or ambiguity case;
- one relevant edge/adversarial case;
- one tool/evidence failure case when the skill depends on tools or external facts;
- regression cases for each known material incident.

These are coverage floors, not a target case count. Use a smaller suite for a narrowly scoped change when it still covers every changed contract and risk; explain the rationale. Do not claim model behavior is proven by schema validation alone.

## Case format

Create or update tests/cases.yaml using the repository schema:
- unique id;
- case identifying the tested distinction;
- realistic input;
- expected.should_trigger;
- semantic expected.must;
- safety/routing expected.must_not where useful;
- optional output properties or fixtures only when supported and needed.

Each case should test one primary distinction. Keep criteria observable, concise and independently judgeable. Add suite-level documentation when tags, fixtures, thresholds or evaluation instructions need more detail; do not invent unsupported schema fields.

## Output

Return:
- the coverage map from contract/risk to case IDs;
- the required execution receipt and state for every runtime-dependent assertion;
- missing coverage and any accepted gaps;
- cases added/changed/retired with reasons;
- validation command/result;
- the smallest additional test needed, if a material gap remains.

Tests represent the intended contract, not whichever current implementation is easiest to pass.
