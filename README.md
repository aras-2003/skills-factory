# Skills Factory

Reusable AI capability library for repeatable work across projects.

## Operating model

- A **Project** stores long-lived context and project-specific constraints.
- A **Skill** stores one reusable procedure.
- A **Workflow** composes skills with gates and stop conditions.
- **Scripts** calculate and validate deterministic logic.
- **Runtime packages** expose channel-specific capabilities; each package's generated manifest is the exact runtime allow-list.
- GitHub source is authoritative; generated plugins/ZIPs are build outputs, not editing targets.

Rule: **LLM interprets; code calculates and validates.**

## Public repository governance

The owner has chosen a **personal / proprietary toolkit**, with **no general third-party reuse license grant**. Public visibility does not itself grant redistribution or relicensing rights; applicable law, GitHub platform rights and third-party licenses remain unaffected. Read the [distribution decision](docs/DISTRIBUTION-LICENSE-DECISION.md), [governance decision record](docs/governance/PUBLIC-REPOSITORY-REVIEW.md), [security reporting policy](SECURITY.md), and [contributor workflow](CONTRIBUTING.md). Ownership routing in `.github/CODEOWNERS` does not by itself establish independent review or GitHub branch protection.

## Visual catalog

Browse skills by domain and maturity in the [Skills Factory catalog](https://aras-2003.github.io/skills-factory/). The catalog is generated from the source metadata in `SKILL.md`.

## Expansion roadmap

The [Skills Factory expansion roadmap](docs/roadmap/2026-10-05/README.md) is a dated analysis with **90 historical IDs**, preserved in `BACKLOG.json`. Active tracking and PR evidence are maintained in [GitHub Issues](https://github.com/aras-2003/skills-factory/issues) and viewed through [Project #1](https://github.com/users/aras-2003/projects/1). **Full Project-field and historical-source cutover remain unverified**; see the [readiness record](docs/governance/BACKLOG-CUTOVER-READINESS.md). Do not update the historical JSON to simulate current task status.

## Current source domains

- `skills/career/` — executive role/company/CV/interview workflows
- `skills/commerce/` — product discovery, demand, competition, economics, sourcing, acquisition and regulatory screening
- `skills/oaf/` — Organisational Architecture Framework specialists
- `skills/meta/` — skill engineering/control skills
- `skills/investing/` — personal Investment OS: market attention, research, portfolio, sizing, monitoring and learning
- `skills/core/`, `skills/ecommerce/`, `skills/learning/`, `skills/product-research/`, `skills/strategy-ea/`, `skills/tender/`, `skills/web-design/` — additional source domains at mixed maturity

- `sites/skills-factory-cloud-next/` — canonical source for the Skills Factory Cloud Next Site and MCP Worker; its embedded Lab catalog and source attestation are generated from this repository during build.

The Skills Factory repository is the single authoring source for skills, workflows, build scripts, and the Cloud Next Site. Site hosting retains a separate provider-managed Git mirror for deployment only. Update Site code through reviewed changes here, then synchronize the merged source with the official Sites workflow; do not author code fixes directly in the provider mirror.

The source tree is not the runtime allow-list.

Current source catalog: **64 skills**, including ten **draft** Presentation/Report OS components, and 19 workflow definitions. Lab 0.35.1 and its bundled MCP expose every source skill and workflow regardless of maturity for isolated testing. Presentation/Report OS, skill-development and report-production remain draft; their Lab exposure does not promote them to the production plugin. The production plugin continues to use its explicit maturity and channel allow-list. Other domain README files describe design/backlog intent unless stated otherwise.

## Branches, maturity and installed capability

These are separate concepts:

- `main` — development source branch.
- `production` — promoted source/release branch. It can contain source components of mixed maturity because branch history is promoted as a repository change set.
- `metadata.maturity` — component-level lifecycle state used by builders.
- generated `capabilities.json` — actual capability availability for a built channel/version.
- generated `release-manifest.json` — package version, source revision and provenance.
- `CATALOG.md` — generated source catalog, useful for discovery but not a substitute for a channel manifest.

Do not infer installed availability from branch membership alone.

## Delivery channels

Production builders currently support:

1. **Plugin channel** — production skills plus workflow entrypoints allowed by `workflows/runtime-registry.yaml`.
2. **Lab channel** — isolated evaluation package containing every source skill and registered workflow regardless of maturity, plus executor-only eval inputs. Do not enable it in the same runtime session as the production plugin.
3. **ChatGPT ZIP channel** — individual production skill ZIPs. Workflow availability is declared explicitly in the channel manifest; unsupported workflows are not silently implied.
4. **Chat/mobile-safe plugin profile** — the same production skills without a bundled MCP server. This is the portable profile for ordinary Chat surfaces where local MCP cannot run.
5. **Cloud MCP plugin profile** — the same production skills with an externally hosted HTTPS MCP endpoint. This profile is for supported web/desktop/Work surfaces; it is not the mobile runtime.

Runtime packages use an allow-list: `SKILL.md`, required `references/`, `scripts/` and `assets/`. Test definitions, eval summaries and evaluator rubrics stay outside production runtime payloads.

## Lifecycle

`idea -> specification -> authoring -> static validation -> isolated evaluation -> candidate -> real-use evidence -> release review -> production -> monitor`

Details:
- `workflows/skill-development/WORKFLOW.md`
- `docs/LIFECYCLE.md`
- `docs/TESTING.md`
- `docs/RUNTIME-EVALS.md`
- `release/production-readiness.yaml`

A narrative historical PASS is not a current-version runtime receipt. When runtime evidence is unavailable, record `NOT_RUN`/pending rather than assuming success.

Current runtime validation campaign: `runtime-validation-2026-10-r16`, pinned to behavior source `89db15ef94cf38a35117ec02b8c60928ef72654d`, with 44 core cases plus 3 supplemental routing regressions. R1–R15 remain historical and bound to their original source revisions. R16 validates inline report visuals and bounded research-state persistence; it does not execute the three draft skill-lifecycle targets. Lab 0.33.1 packages separate executor inputs for `skill-test-design`, `skill-evaluation` and `skill-release-review`; these require their own runtime evidence before promotion. Static/package checks do not imply runtime PASS.

## Quality and build

Required PR validation is defined in `.github/workflows/validate-skills.yml` and covers:
- source/static contracts;
- skill-source static security scan and scanner mutation tests;
- validator mutation tests;
- eval input/rubric isolation;
- active runtime campaign definition, imported evidence validation and offline campaign regressions;
- package safety/reproducibility;
- catalog freshness;
- production plugin, Lab and ChatGPT ZIP builds plus artifact validation;
- deterministic Commerce unit-economics tests.

The Site source has a dedicated PR gate in `.github/workflows/validate-cloud-next-site.yml`: it generates the embedded MCP catalog from the same commit's Lab build, typechecks, runs contract and source-sync tests, lints and builds the Worker. It does not upload test artifacts.

Generated artifacts are built atomically and include source provenance.

## Chat, web and mobile portability

The repository treats skills and MCP as separate runtime capabilities:

```
source skills/workflows
        │
        ├── skills-only profile  ── Chat Web / Chat Mobile where plugins or skills are exposed
        ├── cloud profile        ── Web / Desktop / Work + remote HTTPS MCP
        └── local profile        ── Desktop / Work + bundled stdio MCP
```

The mobile-safe profile deliberately contains no `mcp.json`, `.mcp.json` or local
MCP executable. It can therefore be installed without depending on a local
machine. MCP Apps are currently web-only in ChatGPT; mobile access must use the
skill-only path or the separate mobile Work/Codex remote-control experience.

Build examples:

```bash
python scripts/package/build_plugin.py --runtime-mode skills-only --output .tmp/chat-mobile
python scripts/package/build_plugin.py --runtime-mode remote \
  --remote-mcp-url https://<your-host>/mcp --output .tmp/chat-web
python scripts/package/build_plugin.py --runtime-mode local --output .tmp/desktop
```

Do not put a local `stdio` MCP server in the mobile-safe artifact. Do not treat
the presence of a generated package as proof that a ChatGPT account or surface
has enabled plugins; that remains an installation and product-availability gate.

## Key docs

- Cloud Next source ownership: `docs/SITE-CANONICAL-SOURCE.md`

- Architecture: `docs/ARCHITECTURE.md`
- Remote MCP deployment: `docs/REMOTE-MCP.md`
- Lifecycle: `docs/LIFECYCLE.md`
- Testing: `docs/TESTING.md`
- Iteration delivery and closure: [quality gates](docs/governance/ITERATION-DELIVERY.md)
- Runtime evals: `docs/RUNTIME-EVALS.md`
- Static skill security scan: `scripts/security/README.md`
- Active R16 runbook: `evals/campaigns/runtime-validation-2026-10-r16/RUNBOOK.md`
- Channel usage: `docs/GPT-USAGE.md`
- Branch-rules proposal: `docs/GITHUB-BRANCH-RULES-PROPOSAL.md`
- Distribution/license decision: `docs/DISTRIBUTION-LICENSE-DECISION.md`
- Generated catalog: `CATALOG.md`
