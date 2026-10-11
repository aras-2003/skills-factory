# Skills Factory lifecycle audit — 9 October 2026

## Authority and scope

- **Reference process:** Skills Factory Cloud Next, embedded Lab **0.33.7**, Lab source `a66f7cf40adbbfce31248c6f806016a4f27e93cb`. Read exact packaged instructions with `load_skill` for `skill-specification` (1.0.1), `skill-authoring` (1.0.1), `skill-test-design` (0.3.1), `skill-validation` (1.0.0), `skill-evaluation` (0.3.4), `skill-release-review` (0.3.0).
- **Repository baseline:** `main` at `a33154555ba317d20ccad615a5fb7ae93ea86c27` when inspection began. Cloud Next's Lab packaging reflects an **older source revision**; it is process guidance, not proof the GitHub main artifact is deployed.
- **Coverage:** all **54** `skills/**/SKILL.md` and **54** associated `tests/cases.yaml`. The other **16** installed workflow entrypoints and one unregistered skill-development workflow are **not** included in this per-skill source audit; create a separate workflow audit rather than silently claiming 70/70 behavioral compliance.
- **Execution:** deterministic source/fixture checks and GitHub CI only. No model routing, external connector, human usability or browser E2E execution; all are `NOT_RUN`.

## Process criteria and evidence

| Lab gate | What this audit can verify | What it cannot infer |
|---|---|---|
| Skill specification | One source package per named skill, frontmatter, identifiable user goal, description trigger cue | Real recurrence, user-accepted scope, superiority versus script/workflow |
| Skill authoring | Procedure/purpose/output layout, metadata, local references and SKILL.md size | Semantic correctness, portability across every provider, tool permissions |
| Test design | Existence of valid per-skill cases, unique IDs, positive and negative counts, examples of edge/failure prompts | Whether the cases are truly independent and discriminating in model execution |
| Skill validation | Existing schema, package, resource, security and catalog validators plus a separate lifecycle audit | Behavioral competence, actual tool discipline or security under live conditions |
| Skill evaluation | Frozen fixture contents and explicit `NOT_RUN` status | PASS/FAIL or candidate improvements without execution receipts/comparator |
| Release review | Presence of maturity/version/owner/risk metadata and CI packager checks | Exact deployed runtime identity, approval, promotion or production authorization |

## Findings on baseline

1. **Foundational validation exists.** All 54 source skills have `tests/cases.yaml`, and repository validators already cover frontmatter, package references, schema, basic routing polarity and some runtime fixture integrity. Do not rebuild these tools.
2. **Observed meaningful coverage gap:** five Meta skill suites (`skill-authoring`, `skill-specification`, `skill-test-design`, `skill-validation`, `skill-release-review`) had **zero `should_trigger: false` cases**. The adjacent `skill-evaluation` suite had one negative and the diagnostic skill only one positive. The other domains largely have one negative per skill.
3. **Remediation:** add self-contained, realistic adjacent-goal negative cases to each of the 54 suites, reaching at least two should-trigger and two should-not-trigger fixtures per skill. Use different nearby user goals, avoid revealing evaluator-only expectations in the executor input and retain all historic regression cases. An additional indirect positive is included for `skills-factory-diagnostic`.
4. **Structural/process audit:** `scripts/engineering/audit_skill_lifecycle.py` produces one machine-readable row per source skill, source/test path, source-version label, fixture counts, review warnings and `runtime_evidence: NOT_RUN`. Its limitations are part of the report; it does not convert a passing lexical test into release approval.
5. **Progressive disclosure candidates:** `report-composer` (~15.6k chars) and `visual-output-design` (~15.6k chars) exceed a conservative review threshold; assess conditional material for extraction to references *without removing safety stops*. This is a maintainability **review finding**, not an automatic authoring failure.
6. **Test-depth gap remains:** a few suites lack obvious missing/tool-failure/conflicting-evidence/adversarial prompts. These require human review against the individual skill's risk model; a keyword match alone is not proof of an adequate assertion.

## How to reproduce and read the result

```bash
python scripts/engineering/audit_skill_lifecycle.py \
  --output .tmp/skill-lifecycle-audit.json --fail-on-structural-blockers
python -m unittest discover -s scripts/engineering/tests -p 'test_*.py'
python scripts/validate/validate_all.py
```

On CI, the full **54-row per-skill JSON report** is preserved in the `skills-factory-lifecycle-audit` artifact attached to the PR workflow run. **The machine-readable report is the item-by-item record.** `STATIC_CHECKS_OK` means the deterministic signals found no flagged gaps, but `semantic_review: REQUIRED` still holds. `REVIEW_REQUIRED` demands a human or dedicated source inspection. `STATIC_BLOCKER` means structure/coverage is insufficient and the local source gate blocks.

## Verified exact-branch static result (CI)

After fixing a depth-limited discovery bug (the first audit scanned only 30 source skills), the re-run inspected **all 54** recursively. The final source-head `f040781391f48db5d1ec3a97086674b333a3171f` passed [Validate Skills](https://github.com/aras-2003/skills-factory/actions/runs/37997307546) and [Domain Integrity](https://github.com/aras-2003/skills-factory/actions/runs/37997307565).

- **54/54 inventoried** with both positive and negative fixtures; every suite now has at least two of each type.
- **0 deterministic structural blockers**.
- **29 `STATIC_CHECKS_OK`** (only means the source checks emitted no warning).
- **25 `REVIEW_REQUIRED`** (source/test quality signals need a reviewer).
- Finding signals (some may overlap): **20** heuristic robustness/edge-coverage flags; **3** routing-description trigger cues; **3** nonstandard procedural headings; **1** nonstandard purpose heading; **2** progressive-disclosure warnings. These are not 29 or 25 model quality PASS/FAIL verdicts.
- `runtime_evidence = NOT_RUN` for every row; `semantic_review = REQUIRED` for **all** 54.

### Exact named review queue from CI

| Review type | Skill names / next action |
|---|---|
| Description routing cues (3) | `investment-attention-triage`, `thesis-monitor`, `capability-map-review` — review trigger clarity and preserve scope boundaries before editing source. |
| Progressive disclosure (2) | `report-composer`, `visual-output-design` — move conditional material only with unchanged safety hard stops, see AUD-03. |
| Nonstandard headings (3 procedure, 1 purpose) | `skill-authoring`, `skill-release-review`, `skill-test-design` — verify semantic equivalence of `Current authoring principles`, `Review procedure`, `Design procedure`; treat heading mismatch as a **heuristic review**, not a defect by itself. |
| Robustness-case heuristic (20) | Refer to the complete JSON per-skill report from CI; triage severity by external tool/action risk, not simple keyword counts. |

Full 25-source review queue: `company-context-research`, `cv-gap-analysis`, `executive-role-evaluator`, `interview-brief`, `job-discovery`, `process-update`, `problem-demand-validation`, `acquisition-fit-review`, `supplier-viability-review`, `decision-journal-update`, `investment-attention-triage`, `investment-policy-design`, `investor-pattern-research`, `thesis-challenge`, `thesis-monitor`, `trend-theme-research`, `valuation-scenario-review`, `report-composer`, `skill-authoring`, `skill-release-review`, `skill-specification`, `skill-test-design`, `skills-factory-diagnostic`, `visual-output-design`, `capability-map-review`.

**High-severity related finding:** `thesis-monitor` source contained a canonical-store append instruction without a sufficiently explicit authorization gate. Separate [P0 Issue #291](https://github.com/aras-2003/skills-factory/issues/291) and [draft PR #292](https://github.com/aras-2003/skills-factory/pull/292) contain a source-level guard, but the old E2E campaign source-SHA pin intentionally blocks that PR from merging until an independently versioned campaign executes. Do **not** rewrite the historical baseline to green the check.

## Separate follow-up after the source PR

- Source review: risk-specific adversarial/tool-failure examples, meaningful competitor coverage and the difference between a shared domain term and a true user-goal collision.
- Refactor high-context packages where conditional sections can be split safely. Keep all hard stops and packaging integrity unchanged until regression evidence is satisfactory.
- Validate all **16 registered workflows** with an analogous, explicitly workflow-aware contract, not the per-skill fixture heuristic.
- Execute Lab/Chat/Site candidate-vs-baseline or previous-version tests on the exact revision and log the observed route, tool trace, sample size and failure severity. Evaluate and authorize promotion separately. Nothing here claims runtime PASS.
