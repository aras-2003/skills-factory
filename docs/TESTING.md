# Skill Testing and Quality Gates

## 1. Goal

Test skills as behavioral components, not as static prompt text.

The question is not "does the markdown look good?" but:
**does the agent reliably do the intended thing under representative inputs?**

## 2. Test layers

### Layer 1 — Static validation
Checks:
- required frontmatter exists;
- name follows naming convention;
- description is non-empty;
- required headings exist;
- internal links resolve;
- referenced scripts/assets exist.

### Layer 2 — Routing tests
Verify:
- correct task invokes the skill;
- adjacent task does not;
- description is specific enough for automatic selection.

### Layer 3 — Behavioral tests
Check expected behaviors:
- required analysis steps;
- evidence handling;
- uncertainty language;
- output schema;
- stop conditions.

### Layer 4 — Regression tests
Run previous failure cases after every material edit.

### Layer 5 — Workflow tests
Check interactions between skills, gates and human approvals.

## 3. Execution evidence states

Record execution state per case, separately from the overall evaluation decision:

- `NOT_RUN`: execution has not started; a queued workflow with no runner/steps is still NOT_RUN.
- `BLOCKED` / `NOT TESTABLE`: a required runtime, tool, permission or fixture is unavailable.
- `PASS` / `FAIL`: use only for assertions observed in an execution that actually ran.

For live-browser/API requirements, a passing case needs the actual tool trace, source URL or resource, check time and observed status. A plan or narrative claim does not prove the check. Required NOT_RUN/BLOCKED evidence blocks an overall PASS.

MCP tool receipts use a separate execution scope from the case/workflow state.
`tool_receipt.execution_state: executed` means that the MCP tool produced a
result. A routing result must still identify the child workflow as
`workflow_execution_state: not_executed`, with `workflow_executed: false`,
`outcome: null`, and a reason until the host actually runs it. For charts,
`artifact_state: rendered` records a returned, hashed payload;
`client_display_state: not_observable` must remain explicit unless the host
provides independent display evidence. Receipts contain unsigned SHA-256
digests for canonical inputs and outputs and are integrity aids, not signatures.

## 4. Suggested test-case format

```yaml
id: career-role-fit-001
skill: role-fit-analysis
case: strong-fit-with-missing-salary
input: |
  ...
expected:
  should_trigger: true
  must:
    - assess mandate and organizational scope
    - identify salary as unknown rather than inventing it
    - distinguish facts from inference
  must_not:
    - tailor CV
    - perform deep company research
  output:
    format: structured-decision-note
```

## 5. Evaluation dimensions

Score only for engineering/testing; do not expose numerical scores as a substitute for judgment in user-facing political contexts.

For ordinary skills, useful dimensions are:
- routing precision;
- task completion;
- factual grounding;
- instruction adherence;
- structure;
- concision;
- usefulness;
- robustness to missing data;
- context/token efficiency.

## 6. Golden cases

Maintain a small golden set of representative examples for each production skill.

A golden case contains:
- input;
- expected critical reasoning steps;
- expected output properties;
- known traps.

Do not require verbatim output matching for judgment-heavy tasks.

## 7. Red-team cases

High-value skills should include at least one red-team case:
- misleading user premise;
- conflicting sources;
- missing evidence;
- request outside the skill boundary;
- plausible but false data embedded in input.

## 8. Quality gate before production

A skill cannot be production-ready if:
- it cannot state when NOT to use it;
- its output contract is undefined;
- it invents missing values;
- it hides material uncertainty;
- it duplicates another skill;
- it requires excessive context for routine execution;
- it contains deterministic logic that should live in code.

## 9. Metrics to collect later

Once the library is used regularly, measure:
- trigger precision / false routing;
- correction rate;
- average number of manual follow-ups;
- workflow completion rate;
- test pass rate;
- production regression rate;
- approximate context cost;
- percentage of outputs accepted without restructuring.

These metrics matter more than raw number of skills.


## Iteration-level acceptance

Follow [Iteration delivery and quality gates](governance/ITERATION-DELIVERY.md) for frozen scope, the single active increment, exact-candidate test coverage, corrective work, failure severity and closure before starting the next iteration. Main integration after offline checks remains separate from runtime acceptance and production promotion.
