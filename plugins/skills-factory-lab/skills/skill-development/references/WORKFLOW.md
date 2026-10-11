# Skill Development Workflow

## Purpose

Create or materially change a skill using a repeatable engineering process that covers:
- need and scope;
- standards research;
- behavioral contract;
- authoring;
- static validation;
- routing tests;
- behavioral evals;
- regression analysis;
- security / surprise review;
- production readiness.

## Entry conditions

Use this workflow when:
- creating a new reusable skill;
- splitting or merging existing skills;
- materially changing trigger behavior;
- changing procedure/output contract;
- promoting a candidate to production.

Do not use the full workflow for cosmetic documentation-only edits.

## Stage 0 — classify the change

Classify as:
- **NEW** — new capability;
- **ROUTING** — description/trigger change;
- **BEHAVIOR** — procedure/output change;
- **RESOURCE** — scripts/references/assets change;
- **DOCS** — no behavioral effect.

For a repeatable, local-only change-class plan, run `python scripts/engineering/change_gate.py --change-class <NEW|ROUTING|BEHAVIOR|RESOURCE|DOCS> --path <changed-file> [--path <changed-file> ...] --output .tmp/change-gate.json`. The tool does not infer a safe DOCS classification from arbitrary Markdown, and its `PLAN_READY` is **only** an offline test plan, never a runtime PASS or authorization to publish.

This determines test depth. For a description-only `ROUTING` change, rerun positive, realistic near-miss and competing-skill routing cases; do not add output-format tests unless the contract also changed. `BEHAVIOR` changes require affected behavioral/regression cases. `RESOURCE` changes require direct resource/helper checks plus dependent flows. `DOCS` changes use static validation only unless implementation semantics changed.

## Stage 1 — specification

Invoke `skill-specification`.

Outputs:
- problem statement;
- why skill vs project instruction/script/workflow;
- trigger and non-trigger boundaries;
- required/optional inputs;
- preconditions;
- output contract;
- stop/escalation conditions;
- evidence/tool requirements;
- risk level;
- candidate examples.

At specification time, draft the first **test intent map** before writing the skill: one positive trigger, one plausible competing or near-miss route, and one expected failure/missing-evidence behavior. Mark each case `DESIGN_ONLY` until executable fixtures exist. Stage 5 finalizes the fixtures and assertions; this early map is **not** execution evidence.

Gate S1:
- the task is genuinely repeatable;
- scope is narrow enough to route reliably;
- boundaries with adjacent skills are explicit;
- deterministic logic is identified separately.

If gate fails: do not create a skill.

## Stage 2 — standards and reference check

Before authoring, check current authoritative guidance when standards may have changed.

Priority:
1. open Agent Skills specification;
2. OpenAI Skills documentation for ChatGPT/Codex/OpenAI runtimes;
3. Anthropic official Agent Skills repository / skill creator;
4. repository-local conventions;
5. third-party catalogs only as implementation inspiration.

Capture only practices that affect this skill.

Key expected conventions:
- directory-based skill package;
- required `SKILL.md`;
- YAML frontmatter with at least `name` and `description`;
- description expresses what the skill does and when it should trigger;
- detailed steps stay in the body;
- optional `scripts/`, `references/`, `assets/`;
- progressive disclosure: metadata -> SKILL.md -> supporting resources;
- avoid unnecessarily large SKILL.md; split deep reference material;
- user intent and explicit user instructions override generic skill guidance;
- tool dependencies do not replace explicit workflow instructions;
- inspect imported skill content for safety and unexpected actions.

Gate S2:
- no known conflict with current standard;
- runtime-specific assumptions are explicit.

## Stage 3 — authoring

Invoke `skill-authoring`.

Create:
```
skills/<domain>/<skill-name>/
├── SKILL.md
├── tests/
│   └── cases.yaml
├── references/   # only if needed
├── scripts/      # only if needed
└── assets/       # only if needed
```

Do not create empty optional directories.

Gate S3:
- skill can be understood and executed without hidden assumptions;
- output contract is testable;
- description can route independently of the body.

## Stage 4 — static and standards validation

Invoke `skill-validation`.

Check:
- valid package structure;
- naming/frontmatter;
- description quality;
- clear inputs/outputs;
- explicit do-not-use boundary;
- no duplicate responsibility;
- no hidden project-specific personal context;
- deterministic logic delegated where appropriate;
- referenced resources exist;
- security / lack-of-surprise;
- portability assumptions;
- line/complexity budget;
- no contradictory instructions.

Gate S4:
- no blocking issue;
- warnings have explicit disposition.

## Stage 5 — test design

Invoke `skill-test-design`.

Minimum suite for a new production candidate:
1. direct should-trigger;
2. indirect should-trigger;
3. incomplete input;
4. near-miss should-not-trigger;
5. competing-skill case;
6. edge/adversarial case;
7. conflicting or stale evidence case when relevant;
8. known regression case once defects exist.

Each case must include a self-contained prompt, required fixture, observable expected behavior, forbidden behavior, and a named competing route or explicit no-skill outcome where relevant. Generic positive examples do not establish routing quality; require at least one realistic near-miss and one plausible competitor. For an existing production skill, preserve this discrimination floor even when the overall regression suite is risk-scoped.

Create assertions on behavior, not exact prose.

Gate S5:
- tests discriminate good from plausible-but-wrong behavior;
- negatives are realistic near-misses, not trivial unrelated prompts.

## Stage 6 — behavioral evaluation

Invoke `skill-evaluation`.

For material changes:
- execute representative cases with candidate;
- compare to baseline (no skill) for new skills when useful;
- compare to previous version for modifications;
- evaluate routing and output separately;
- use blind comparison for subjective high-value skills when feasible;
- capture failure reason, not just pass/fail.

Gate S6:
- candidate improves or preserves intended behavior;
- no severe routing regression;
- no new high-severity failure mode;
- every required case has an execution state: `NOT_RUN` for queued/not-started, `BLOCKED` / `NOT TESTABLE` for unavailable prerequisites, and `PASS` / `FAIL` only after observation;
- every non-executed case has `outcome: null`, `evaluation.status: NOT_RUN`, and a specific `execution_state` (`no_steps`, `awaiting_runner`, `blocked`, or `not_executed`); compatibility remains `NOT_RUN` unless separately executed;
- a required unobserved case cannot be counted as a pass.

## Stage 7 — revision loop

If a gate fails:
1. classify the cause: routing / instruction / resource / tool / test;
2. change the smallest responsible component;
3. rerun affected tests plus regression suite;
4. do not weaken a valid test merely to make the skill pass.

Repeat until acceptance or abandon the candidate.

## Stage 8 — release review

Invoke `skill-release-review`.

Production promotion requires:
- contract complete;
- standards validation passed;
- representative tests passed;
- routing quality acceptable;
- no unresolved high-severity issue;
- version/maturity/owner metadata current;
- at least one real use case/workflow identified;
- human approval for production promotion.

## Stage 9 — promotion

Recommended Git flow:

```
feature/<skill-name>
  -> PR to main
  -> validation + eval evidence
  -> merge to main as candidate
  -> real-use pilot
  -> promotion PR main -> production
```

Production must remain smaller and more stable than main.

## Stage 10 — post-release

When a defect occurs:
- add the failing real case to regression tests first;
- reproduce;
- fix;
- rerun affected suite;
- update version when behavior changes.

Review a skill when:
- runtime behavior changes;
- tool/API dependency changes;
- routing collisions appear;
- repeated user correction appears;
- workflow no longer matches real work.

## Artifacts per production skill

Required:
- `SKILL.md`;
- test cases;
- reviewable change history;
- evidence that release gates were passed.

Recommended for high-value skills:
- eval results;
- golden cases;
- failure/regression log;
- changelog;
- generated catalog entry.

## Handoff per change

Always hand over the exact changed files/revision, change class, applied static gates and independently executed eval receipts, with explicit `NOT_RUN` for skipped runtime cases. Separate **implementation complete**, **locally validated**, **runtime validated**, and **release authorized**; none implies the next. State the smallest unresolved action rather than treating a passing plan or static CI as release approval.

## Core principle

Treat skills as versioned behavioral components, not prompt snippets.
