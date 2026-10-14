# Skills Factory Architecture

## Objective

Build a portable, testable library of reusable AI procedures without duplicating project context.

The repository is a capability library, not a prompt dump.

## Layers

| Layer | Owns | Must not own |
|---|---|---|
| Project/context | goals, private/current facts, files, constraints | generic reusable method |
| Router/runtime | intent recognition, capability selection, tool authority | duplicated domain procedure |
| Skill | reusable method for one task | unrelated orchestration or personal profile |
| Workflow | sequence, gates, branching, dependency handling | duplicated specialist instructions |
| Script | deterministic calculation/parsing/validation | judgment-heavy reasoning |
| Connector/tool | external data/actions | reasoning policy |
| Eval harness | isolated input, evidence receipt, evaluator assertions | leaked answers/rubrics in executor context |
| Quality gate | source/package integrity and release checks | substantive domain result |

## Repository layout

```
skills-factory/
├── skills/
│   ├── career/
│   ├── commerce/
│   ├── oaf/
│   ├── meta/
│   └── ...other mixed-maturity source domains
├── workflows/
│   ├── runtime-registry.yaml
│   └── <workflow>/WORKFLOW.md
├── evals/
│   ├── runtime-fixtures.yaml
│   ├── routing/
│   └── results/
├── scripts/
│   ├── validate/
│   ├── package/
│   ├── eval/
│   ├── readiness/
│   └── catalog/
├── release/
│   ├── package.yaml
│   └── production-readiness.yaml
├── sites/
│   └── skills-factory-cloud-next/  # canonical Site/MCP source; host copy is a deployment mirror
├── docs/
└── CATALOG.md
```

Generated `plugins/` and `dist/` artifacts are outputs, not source editing targets.
The Cloud Next Site source is maintained in `sites/skills-factory-cloud-next/`. Its loadable MCP catalog and canonical source revision are generated from the exact Lab and repository commit used for the build. The provider-managed Site repository is a deployment mirror, not a second authoring source.

## Skill package

```
skills/<domain>/<skill-name>/
├── SKILL.md
├── tests/          # source-side behavioral definitions
├── references/     # runtime support when needed
├── scripts/        # deterministic helpers
└── assets/         # runtime templates/assets
```

Optional directories exist only when useful. Production runtime packagers use an explicit allow-list and exclude `tests/`, eval summaries and evaluator rubrics.

## SKILL.md contract

Routing metadata should answer:
1. what task the skill performs;
2. when to invoke it;
3. what nearby tasks route elsewhere.

Source metadata may contain repository-internal information. Exported portable SKILL frontmatter is intentionally reduced to the portable subset; nested execution/eval history remains repository-side.

Do not infer cross-runtime compatibility solely from successful YAML parsing. Runtime import/execution is a separate evidence claim.

## Workflow dependency contract

`workflows/runtime-registry.yaml` defines:
- workflow source;
- maturity/version;
- channel support;
- required execution dependencies;
- optional dependencies and explicit `on_missing` behavior.

Required missing dependencies block a supported package. Optional missing dependencies must narrow scope or stop the affected branch; an entrypoint must not simulate a specialist that is not available.

Execution dependency cycles are invalid. Ordinary references to another method are not automatically execution dependencies.

## Routing

1. Identify user intent.
2. Identify domain.
3. Check preconditions.
4. Select the smallest capability that fully addresses the task.
5. Load only required support.
6. Execute.
7. Apply control/review when risk warrants it.
8. Escalate to a workflow only when multiple stages/gates are needed.

Natural routing and explicit invocation are tested separately.

## Progressive depth

Do cheap gates before expensive work. Examples:
- discovery before known-product deep dive;
- sample/landed-cost validation before paid acquisition when those can falsify the thesis;
- eligibility before tender deep dive;
- evidence validation before high-impact recommendations;
- diagnosis before operating-model/governance redesign.

## Deterministic vs model logic

Use code for arithmetic, schemas, duplicate detection, digests, packaging, deterministic assertions and regression checks.

Use model reasoning for interpretation, ambiguity, qualitative trade-offs, counterarguments and synthesis.

**LLM interprets; code calculates and validates.**

## Evaluation integrity

Runtime cases separate:
- executor-only `.input.md`;
- evaluator-only `.rubric.yaml`.

The Lab packages only executor inputs. Evidence receipts record source/component identity, runtime/model, available catalog, actual output/trace and review result. If execution is unavailable, status is `NOT_RUN`, not PASS.

## Channels and provenance

Every built channel exposes a generated capability manifest and release provenance. Channel support is explicit; functionality absent from a channel is marked unavailable rather than implied.

### Surface profiles

The production package has three intentionally different runtime profiles:

| Profile | MCP transport | Intended surfaces | Mobile Chat |
|---|---|---|---:|
| `skills-only` | none | ordinary Chat Web/Mobile where the plugin/skill is exposed | yes, subject to account/surface availability |
| `remote` | HTTPS MCP | Chat Web, Desktop and Work | no MCP App support |
| `local` | bundled `stdio` | Desktop and Work with a local runtime | no |

The `skills-only` profile is the portability boundary. Its skills must be
usable with the model and the tools already provided by the host; they must not
require `mcp.json`, `.mcp.json`, filesystem access, a local CLI or Ollama.

The `remote` profile is an execution enhancement, not a prerequisite for the
methodology. It points to a separately deployed HTTPS MCP service and must not
bundle the local Python server. The `local` profile remains useful for local
repositories, shell execution and Ollama, but its availability is inherently
surface-specific.

This distinction prevents an unavailable local capability from making the core
skills unavailable. It also avoids claiming mobile MCP support that the host
does not provide.

Build outputs are staged, validated and atomically replaced. ZIP content is deterministic for the same source/content.

## Lifecycle and maturity

- `draft` — experimental source procedure;
- `candidate` — under representative testing;
- `production` — accepted for the declared scope;
- `deprecated` — retained for migration/history.

Maturity is a component property, not a branch-membership guarantee. Production readiness is reviewed in `release/production-readiness.yaml`.

A historical narrative PASS does not automatically prove a changed component version.

## Human approval boundaries

Human approval remains required for money commitments, external publication/messages, production-system changes, irreversible repository/release changes, branch-protection changes, license/distribution decisions and high-impact actions based on materially uncertain evidence.
