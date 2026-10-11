# Skills Factory workflow lifecycle audit — 2026-10-09

## Scope / authority

Skills Factory Cloud Next's verified embedded Lab **0.33.7** catalogs **70** components: **54 source SKILL.md packages** and **16 registered workflow entrypoints**. The 54 source skills were audited in [PR #285](https://github.com/aras-2003/skills-factory/pull/285). This companion audit covers all 16 workflow records from `workflows/runtime-registry.yaml`; it does **not** falsely apply the per-skill `tests/cases.yaml` rule to every workflow.

Reference method: packaged `skill-specification`, `skill-authoring`, `skill-test-design`, `skill-validation`, `skill-evaluation`, adapted for multi-skill orchestration with registry, dependencies, channel policy, stage and stop conditions.

## Deterministic source checks

- Registered workflow name, non-duplicated identity and canonical `WORKFLOW.md` path.
- Version, maturity, owner, risk and review metadata; channel availability.
- Required and optional dependencies as a contract.
- Stages/routing and output contract; precondition, evidence and stop/boundary cues.
- Local workflow suite presence (warning only: some workflows are covered by separate frozen runtime fixture registries).
- Exact machine-readable result row per registered workflow, `semantic_review: REQUIRED`, `runtime_evidence: NOT_RUN`.

No direct tool execution, routing test, browser inspection, packed artifact equality or model-based acceptance is performed. A lexical check does not certify workflow correctness. The unregistered `workflows/skill-development/WORKFLOW.md` is a build process artifact, **not a 17th packaged runtime workflow**; it must be validated separately on its own terms.

## Run and inspect

```bash
python scripts/engineering/audit_workflow_lifecycle.py --output .tmp/workflow-lifecycle-audit.json
python -m unittest discover -s scripts/engineering/tests -p 'test_audit_workflow_lifecycle.py'
```

CI uploads `skills-factory-workflow-lifecycle-audit` with the complete 16-row JSON and prints the warnings. Follow-up: review meaningful delegation gaps, source-vs-generated entrypoint parity, optional-dependency failure handling and exact-version runtime traces, separately from static PASS.

**Related issues:** [AUD-05 #290](https://github.com/aras-2003/skills-factory/issues/290), [AUD-02 #287](https://github.com/aras-2003/skills-factory/issues/287), [AUD-04 #289](https://github.com/aras-2003/skills-factory/issues/289).
