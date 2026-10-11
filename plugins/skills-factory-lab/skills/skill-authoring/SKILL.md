---
name: skill-authoring
description: 'Create or refactor an Agent Skill package from an approved skill specification.
  Use when writing SKILL.md, splitting instructions into references/scripts/assets,
  improving progressive disclosure, or aligning a skill with repository and current
  Agent Skills authoring conventions.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 1.0.1
  maturity: production
  risk: medium
  last_reviewed: '2026-10-09'
---

# Skill Authoring

## Preconditions

Require an approved specification or reconstruct one with `skill-specification` first.

## Current authoring principles

1. Use the open Agent Skills package model:
   - `SKILL.md` required;
   - `scripts/`, `references/`, `assets/` optional.
2. Frontmatter must contain at least:
   - `name`;
   - `description`.
   Parse and validate the final frontmatter; a body heading or generated catalog entry does not substitute for either field.
3. Treat `description` as routing metadata:
   - state what the skill does;
   - state when it should be used;
   - include recognizable user-goal language;
   - distinguish adjacent skills.
4. Keep detailed process and output requirements in the body.
5. Prefer imperative, executable instructions.
6. Explain decision rationale where it reduces brittle rule following.
7. Use progressive disclosure:
   - metadata is lightweight;
   - SKILL.md contains the core procedure;
   - deep references are loaded only when needed.
8. Keep SKILL.md concise enough to reason over reliably; move long domain material to references.
9. Use scripts for deterministic/repetitive logic.
10. Use assets for templates/resources used in outputs.
   - For substantial decision outputs, define a semantic report structure first with `report-composer`; let `visual-output-design` render only the local visual slots.
11. State tool order and missing-result handling explicitly when tools matter.
12. Preserve user agency: explicit user instructions override generic skill defaults unless higher-priority rules prevent it.
13. Follow the principle of least surprise: never hide destructive, external, privileged or security-sensitive behavior.
14. When the output is a substantial report, define report-composition affordances (sections, inline visual slots, progressive disclosure) and use `report-composer` above `visual-output-design`.
15. Keep full-report composition separate from visual rendering: `report-composer` owns reading flow; `visual-output-design` owns chart/diagram/component rendering.

## Required body sections

Prefer:
- Purpose
- Preconditions
- Procedure
- Decision rules
- Inputs
- Output contract
- Evidence requirements
- Failure and uncertainty handling
- Quality checks
- References

Use "Use when" / "Do not use when" in the body only as explanatory detail; primary routing conditions belong in the description.

## Resource split rules

Move content to `references/` when:
- it is long;
- only some executions need it;
- it varies by framework/domain;
- it is factual/reference material rather than procedure.

Move logic to `scripts/` when:
- exact arithmetic matters;
- repeated parsing/transformation is deterministic;
- schema/static validation is feasible;
- reproducibility matters more than model judgment.

## Output

Produce:
1. package tree;
2. complete SKILL.md;
3. necessary supporting resources only;
4. authoring notes listing assumptions and unresolved questions.

Do not declare the skill production-ready. Hand off to `skill-validation`.
