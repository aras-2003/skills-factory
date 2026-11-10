# Iteration 09 — PRES-02 acceptance matrix

Baseline source: `cfcb1c9b6f0f5ee512d7cbc44da98740198f9898`. Candidate and data-fixture hashes are populated when the implementation is complete and the test phase begins. This slice changes no runtime behavior; Site/client execution is not claimed.

| Row ID | Issue / criterion | Layer + case ID / definition | Required / N/A rationale | Candidate SHA + artifact digest | Surface/model/tools | Input/rubric hashes | Execution state | Verdict | Receipt/output/trace + run time | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 608-A | #608 / build-vs-reuse audit | Repository audit; source inventory table | required | pending | source review | pending | NOT_RUN | none | pending | owner |
| 608-B | #608 / versioned canonical model | Versioned schema for the existing artifact-contract DeckSpec/SlideSpec contract | required | pending | local Python + jsonschema | pending | NOT_RUN | none | pending | owner |
| 608-C | #608 / deterministic validator | Positive, malformed, missing-field, reference and compatibility fixtures | required | pending | local Python + jsonschema | pending | NOT_RUN | none | pending | owner |
| 608-D | #608 / example deck | Synthetic DeckSpec fixture validates | required | pending | local Python + jsonschema | pending | NOT_RUN | none | pending | owner |
| 608-E | #608 / round-trip fidelity | Numeric values, units, source identities, notes and links preserved exactly | required | pending | local Python unit tests | pending | NOT_RUN | none | pending | owner |
| 608-F | #608 / backward compatibility | Existing artifact-contract and presentation-slide-authoring semantic models map without silent data loss | required | pending | local Python unit tests | pending | NOT_RUN | none | pending | owner |
| 608-G | #608 / integration/regression | Existing Presentation and workflow contracts; Report Composer, Visual Output Design and unaffected probes | required | pending | local tests + GitHub CI | pending | NOT_RUN | none | pending | owner |
| shared-report | iteration / evidence boundary | `report-composer`: no-unsolicited-artifact + evidence preservation | required | pending | contract suite | existing source case IDs | NOT_RUN | none | pending | owner |
| shared-visual | iteration / evidence boundary | `visual-output-design`: no-fabrication + capability preflight | required | pending | contract suite | existing source case IDs | NOT_RUN | none | pending | owner |
| rotating-commerce | iteration / unchanged-domain probe | `economics-post-cac-reconciliation` | required | pending | regression suite | existing source case ID | NOT_RUN | none | pending | owner |
| rotating-investing | iteration / unchanged-domain probe | `monitor-analysis-without-write-authorization` | required | pending | regression suite | existing source case ID | NOT_RUN | none | pending | owner |
| runtime-site | iteration / runtime identity and smoke | No runtime artifact or behavior changes in this scope; do not infer an acceptance need | reviewed N/A | N/A | Cloud Next Site | N/A | not_executed | N/A | Justification: #608's schema/validator/example-deck contract is consumed offline; no runtime registration, adapter, prompt, packaging, or Site UI changes. Parent #283 runtime acceptance is tracked separately. | owner |

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Static source/model audit | 1 | 1 | 0 | 0 | 1 | 0 | pending |
| Schema/validator/round-trip tests | 5 | 1 per PR candidate | 0 | 0 | 5 | 0 | pending |
| Shared/rotating regression | 4 | 1 per PR candidate | 0 | 0 | 4 | 0 | pending |
| Cloud Next runtime | 0 | 0 | 0 | 0 | 0 | 1 | explicitly N/A for this source-only contract |

Completeness review: all seven #608 outcomes map to required rows. The parent #283 is deliberately not accepted/closed by this increment. No row is PASS until executed against the exact final candidate. If a runtime boundary changes, stop and re-scope rather than treating N/A as acceptance.

