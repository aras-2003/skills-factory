# Repository Map and Naming Standard

This map records the current ownership boundaries in Skills Factory. Source files stay in their domain; packaging and channel-specific publishing consume them rather than maintaining another authored copy.

## Projects and source ownership

| Project / area | Canonical location | Ownership |
|---|---|---|
| Career capabilities | `skills/career/` | Executive role search, CV tailoring, interview and recruitment-process skills |
| Commerce capabilities | `skills/commerce/` | Product discovery, demand, competition, economics, sourcing, regulatory and acquisition review |
| Core capabilities | `skills/core/` | Shared general-purpose capability sources |
| Ecommerce capabilities | `skills/ecommerce/` | Ecommerce-specific source capabilities |
| Investing capabilities | `skills/investing/` | Investment policy, market attention, research, portfolio, security, sizing and monitoring |
| Learning capabilities | `skills/learning/` | Learning and capability-development sources |
| Meta capabilities | `skills/meta/` | Skill authoring, evaluation, testing and release governance |
| OAF capabilities | `skills/oaf/` | Organisational Architecture Framework specialist skills |
| Presentation capabilities | `skills/presentations/` | Presentation evidence, storyline, exhibits, review and authoring |
| Product research capabilities | `skills/product-research/` | Product and market research sources |
| Report capabilities | `skills/reports/` | Report architecture, authoring and review |
| Strategy and enterprise architecture | `skills/strategy-ea/` | Strategy and enterprise-architecture sources |
| Tender capabilities | `skills/tender/` | Tender and procurement sources |
| Web-design capabilities | `skills/web-design/` | Website and visual-design sources |
| Workflow definitions | `workflows/<workflow>/` and `workflows/runtime-registry.yaml` | The 19 registered multi-step workflows, channel support and dependencies |
| Host-independent runtime contract | `runtime/contracts/mcp-tools-v1.json` | Canonical MCP tool names and required argument sets, checked against both facades |
| Local Lab MCP implementation | `runtime/mcp/` | Python stdio/HTTP MCP server, skill catalog loader, investment routing and chart tools; packaged for Lab/local channels |
| Remote Cloud Next MCP adapter | `adapters/skills-factory-cloud-next/` | TypeScript HTTP MCP protocol, Cloud Next tool handling and adapter contract tests |
| Site application | `sites/skills-factory-site/` | Site UI, hosting configuration, styles, dependencies and Worker build |
| Channel package builders | `scripts/package/` | Production, Lab, ZIP, MCP profile and Site bundle builders |
| Validation and release automation | `scripts/` subdirectories | Catalog, capability, security, eval, governance, readiness and release checks |
| Evaluation definitions and evidence | `evals/` | Case inputs, evaluator-only rubrics, campaign locks, receipts and runtime status |
| Reusable skill template | `templates/skill-template/` | Starting structure for new skills; domain instructions remain in the individual skill source |
| Shared visual assets | `assets/` | Repository-owned assets, including skill icons |
| Cross-project governance tests | `tests/governance/` | Tests for repository automation and metadata synchronization |
| Architecture, standards and roadmap | `docs/` | System design, policy, release history, audits, backlog and product decisions |
| Generated catalog views | `CATALOG.md`, `docs/catalog.json` | Discovery outputs generated from canonical skill/workflow metadata |
| GitHub automation | `.github/workflows/`, `.github/actions/` | CI, release packaging and metadata-sync automation; composite setup action is shared across CI jobs |
| Repository agent guidance | `AGENTS.md`, `.agents/` | Repository-local engineering and tool instructions |
| Generated package output | `plugins/` and local `dist/` | Build outputs; never hand-edited as source |
| Provider Site checkout | External Sites-managed repository | Deployment mirror synchronized from merged canonical Site source |

The two MCP facades now check against the same tool contract and load the same source-bound capability catalog. Their transport and rendering implementations remain language-specific: the Cloud Next facade emits SVG while the local Python renderer emits PNG. Contract parity does not by itself prove identical runtime behavior; adapter-specific tests and behavior checks remain required. The canonical argument contract is the first shared runtime boundary, while moving additional deterministic behavior into a shared implementation is a later migration decision.

## Build and test flow

```text
skills + workflows + runtime source
                 │
                 ├── Lab builder ── local Python MCP package
                 │        └──────── generated capability catalog
                 │
                 ├── Cloud Next adapter + the exact Lab artifact
                 │        └── Site builder ── hosted HTTP MCP + Site UI
                 │
                 └── production / skills-only / remote-MCP / ZIP builders
```

`ci-validate.yml` fans independent checks and package profiles out after a source-revision preflight. It builds the Lab and production artifacts once within that workflow run, then the runtime-handoff job consumes those exact artifacts. `ci-site.yml` is a separate status context for the Site provider workflow and currently builds its own Lab artifact because GitHub Actions artifacts are scoped to one workflow run. Removing that second build requires a deliberate branch-protection/status migration or a supported cross-workflow artifact handoff.

## Workflow and job names

Workflow files follow `<class>-<subject>.yml`:

| Class | Use | Current workflows |
|---|---|---|
| `ci-*` | Required pull-request validation | `ci-validate.yml`, `ci-site.yml`, `ci-domain-integrity.yml`, `ci-eval-integrity.yml` |
| `release-*` or `package-*` | Build or promote channel artifacts | `release-lab-plugin.yml`, `release-production-plugin.yml` |
| `maintenance-*` | Scheduled source synchronization | `maintenance-project-metadata.yml` |

Workflow and required-check display names are stable interfaces to branch protection. Rename a workflow file only when useful, preserve `name:` and required job display values, and audit branch rules before changing either. Within the parallel validation graph, use `CI / <Responsibility>`; final aggregate gate retains the existing `Validate skills / validate` context. Optional artifact names use `sf-<artifact>-<profile>-<full-source-sha>` so outputs cannot be confused across commits.

New project families belong under the existing owner (`skills/<domain>/`, `workflows/<workflow>/`, `adapters/<adapter>/`, `sites/<site>/`, `runtime/<layer>/`) rather than creating peer roots such as `projects/` or `apps/` that duplicate these responsibilities.

The current 19 workflow packages are grouped by owner:

- Commerce: `commerce-opportunity-review`, `commerce-product-deep-dive`.
- Investing: `investment-attention-review`, `investment-opportunity-hunter`, `investment-os-review`, `investment-portfolio-observation`, `investment-portfolio-review`, `investment-security-review`, `investment-theme-discovery`.
- OAF: `oaf-enterprise-architecture-review`, `oaf-enterprise-change-review`, `oaf-governance-redesign`, `oaf-health-check`, `oaf-operating-model-redesign`, `oaf-strategy-execution-reset`, `oaf-transformation-design`.
- Cross-domain production and engineering: `presentation-production`, `report-production`, `skill-development`.
