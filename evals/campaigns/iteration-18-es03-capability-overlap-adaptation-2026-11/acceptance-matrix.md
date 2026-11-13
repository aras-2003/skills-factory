# Iteration 18 / ES-03 capability overlap and adaptation acceptance matrix

Scope-lock ledger for #618. Every row starts NOT_RUN and is bound to one exact candidate. The existing secure intake from #617 is the only accepted source pin/receipt producer. No candidate content is executed.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface/model/tools | Input/rubric hashes | Execution state | Verdict | Receipt/output/trace + run time | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18-01 | #618 / 618-A1 | Deterministic matcher: same-function duplicate cannot be imported as a derivative; recommends existing capability with evidence | Required | NOT_RUN | Offline matcher tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-02 | #618 / 618-A1 | Complementary capability fixture preserves a bounded EXTEND or COMPOSE path with facet-level evidence | Required | NOT_RUN | Offline matcher tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-03 | #618 / 618-A1 | Conflict fixture fails closed and escalates to human review without choosing a derivative automatically | Required | NOT_RUN | Offline matcher tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-04 | #618 / 618-A1 | Trigger, output, tools, dependencies, domain semantics and conflict are independently represented in the comparison report | Required | NOT_RUN | Offline contract tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-05 | #618 / 618-A2 | Adapter accepts only a secure-intake receipt bound to the immutable source and inventory digest; altered/stale input is refused | Required | NOT_RUN | Offline adapter tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-06 | #618 / 618-A2 | Adaptation proposal creates a portable package that passes repository SKILL.md/frontmatter/resource validation | Required | NOT_RUN | Package validation + CI | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-07 | #618 / 618-A2 | Progressive disclosure and runtime dependency behavior are explicit; missing or unsupported dependencies stop or escalate | Required | NOT_RUN | Adapter contract tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-08 | #618 / 618-A3 | Upstream source/license claims and exact pin remain distinct from local changes; UNKNOWN is never promoted by inference | Required | NOT_RUN | Provenance/lineage tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-09 | #618 / 618-A3 | Derivative and conflict proposals require a human review decision before a scoped PR proposal can be emitted | Required | NOT_RUN | Workflow/authorization tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-10 | #618 / 618-A3 | Proposal output binds decision, evidence, source pin, package digest and proposed change; generates no direct production write | Required | NOT_RUN | Offline integration tests | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-11 | #618 / 618-A4 | Positive direct and indirect prompts route to adaptation workflow; adjacent near-miss and existing-capability prompts do not | Required | NOT_RUN | Exact Lab candidate; Chat runtime if available | Frozen case/rubric hashes at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-12 | #618 / 618-A4 | Missing evidence, malformed receipt, stale source and tool/dependency failure remain explicit and fail closed | Required | NOT_RUN | Offline integration + runtime if applicable | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-13 | iteration / shared | No candidate instruction/script executes; no secret exposure, network request or write occurs during compare/adapt simulation | Required | NOT_RUN | Security/adversarial fixtures | Fixture digest at implementation | NOT_RUN | NOT_RUN | None | Owner |
| 18-14 | iteration / shared | Existing skill-development, skill-specification, skill-authoring, provenance and package contracts remain compatible; two unchanged-domain probes pass | Required | NOT_RUN | Full applicable CI and exact-main checks | Baseline and fixture hashes | NOT_RUN | NOT_RUN | None | Owner |
| 18-15 | iteration / shared | Exact candidate package identity and read-only runtime smoke are verified; Site MCP is N/A unless implementation changes the Site/runtime adapter | Required for Lab package behavior; Site MCP N/A unless diff changes it | NOT_RUN | Installed Lab/Chat where available; Site MCP applicability rechecked against diff | Candidate package digest; case hashes | NOT_RUN | NOT_RUN | None | Owner |

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Matcher/adapter deterministic tests | 10+ scenario assertions across rows 18-01–18-10, 18-12–18-13 | Once per PR revision and exact main | 0 | 0 | 10+ | 0 | NOT_RUN |
| Routing/behavior cases | At least 4: direct positive, indirect positive, adjacent negative, competing-capability conflict | At least one exact candidate execution; repeat critical conflicts 3 times if stochastic | 0 | 0 | 4+ | 0 | NOT_RUN |
| Shared integration/regression | All configured repo CI, package/provenance/security tests, two preselected unchanged domain probes | Each PR revision and exact main | 0 | 0 | CI pending | 0 | NOT_RUN |
| Runtime identity/smoke | One exact package identity and read-only invocation on each applicable installed surface | Exact candidate once; repeat only for flaky/critical behavior | 0 | 0 | Pending | Site MCP only if no Site/runtime adapter change | NOT_RUN |

Completeness gate: map every 618-A1–A4 criterion to observed evidence; no required FAIL/NOT_RUN/BLOCKED/REVIEW_REQUIRED at closure. The candidate must retain upstream license/source claims, exact intake receipt and change lineage; a generated proposal is never an authorization to merge or publish.
