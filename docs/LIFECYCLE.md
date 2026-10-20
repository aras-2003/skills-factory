# Skill Lifecycle and Operating Process

## 1. Lifecycle

```
IDEA
  -> OBSERVE REPEATABLE TASK
  -> DRAFT
  -> TEST
  -> CANDIDATE
  -> PILOT IN REAL WORK
  -> PRODUCTION
  -> MONITOR
  -> IMPROVE / DEPRECATE
```

## 2. Step 1 — Identify a skill candidate

Create a skill only when the same task is likely to occur repeatedly.

Capture:
- task name;
- trigger;
- current manual/ad-hoc approach;
- expected output;
- main failure modes;
- examples of good and bad outcomes.

Reject the candidate if a project instruction, checklist or deterministic script is sufficient.

## 3. Step 2 — Define the contract

Before writing long instructions, define:

### Trigger
What user/agent intent should invoke the skill?

### Preconditions
What must already be true?

### Inputs
Required and optional data.

### Output
Exact structure and level of detail.

### Stop conditions
When should the skill stop rather than continue researching?

### Escalation
When should another skill/workflow/human take over?

### Evidence rules
What claims require verification and what sources are acceptable?

## 4. Step 3 — Draft the minimum viable skill

Start with:
- frontmatter;
- purpose;
- use / do-not-use;
- procedure;
- output contract;
- 3–5 quality checks.

Do not add scripts, references or templates until a real case requires them.

## 5. Step 4 — Build tests

Minimum test set:
1. happy path;
2. insufficient input;
3. ambiguous input;
4. adjacent task that should NOT trigger the skill;
5. adversarial/edge case;
6. outdated or conflicting evidence case when relevant.

Each test should define:
- input;
- expected routing;
- required behaviors;
- prohibited behaviors;
- expected output properties.

## 6. Step 5 — Candidate review

A candidate should pass:

### Routing quality
Does it trigger for the right tasks and avoid nearby tasks?

### Procedure quality
Does following it materially improve consistency?

### Output quality
Is the result usable without manual restructuring?

### Evidence quality
Does it distinguish verified facts from interpretation?

### Efficiency
Does it avoid unnecessary research, context and steps?

### Composability
Can a workflow call it without special-case prompt engineering?

## 7. Step 6 — Real-work pilot

Use the candidate on 3–5 representative real tasks.

Record:
- where it worked;
- where the procedure was ignored or ambiguous;
- missing inputs;
- recurring failure modes;
- unnecessary steps;
- actual time/context saved.

Do not promote based on one impressive example.

## Controlled use and production promotion

A personal-beta continuation is a time-bounded exception for already-declared production components only. The matching readiness record must identify the component/version, evidence gap, limitation, named owner and expiry. The record's component/version fields bind the exception to that component; it cannot extend to another version or a wider audience. Missing runtime evidence remains `pending`/`NOT_RUN`; it is never a PASS. The exception cannot cover a known unresolved high-severity failure, create a new production promotion, or extend to changed behavior/version or a wider audience. Stop or re-review when its scope or expiry is reached.

For a new or changed production promotion, the machine-readable `policy` in `release/production-readiness.yaml` mirrors these hard gates: require current-version runtime evidence, reject historical summaries as current receipts, and forbid exceptions for known high-severity failures. The readiness validator fails closed if any required policy flag is missing or weakened.

A new or changed component follows the ordinary lifecycle gates. A candidate may be exercised in the Lab for evaluation, but candidate status and personal-beta use do not equal production readiness or authorize publication.

## 8. Step 7 — Production promotion

Promotion criteria:
- stable routing;
- representative tests pass;
- output contract is clear;
- no known high-severity failure mode remains;
- at least one real workflow uses it;
- owner and review date are defined;
- runtime behavior claims are backed by an exact-version evidence receipt, not only a historical summary;
- natural-routing evidence is separate from explicit-invocation behavior evidence.

If runtime access is unavailable, record NOT_RUN/pending. Do not translate unavailable evidence into PASS.

Production skills should be merged/promoted to the production branch only through review.

## 9. Step 8 — Maintenance

Review production skills when:
- underlying tools change;
- APIs/platform capabilities change;
- recurring output defects appear;
- source requirements change;
- user workflow changes materially.

Do not continuously rewrite stable skills just because a new prompt trick appears.

## 10. Deprecation

Deprecate when:
- the task no longer exists;
- another skill fully subsumes it;
- deterministic tooling replaces it;
- platform-native capability makes it redundant.

Document replacement/migration path.

# Workflow lifecycle

A workflow is promoted separately from its component skills.

Workflow validation must test:
- routing into the workflow;
- branch/stop conditions;
- failure of one stage;
- missing tool/connector;
- human approval boundary;
- final output consistency.

# Change process

Recommended Git flow:

```
feature/<skill-or-process>
  -> PR to main
  -> tests/review
  -> merge to main
  -> real-work validation
  -> promotion PR main -> production
```

Keep `production` intentionally smaller and more stable than `main`.

Branch membership and component maturity are different: builders filter by metadata and channel contracts. Review current production evidence in `release/production-readiness.yaml`.
