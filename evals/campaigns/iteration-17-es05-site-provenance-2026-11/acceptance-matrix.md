# Iteration 17 / ES-05 Site provenance UI acceptance matrix

Scope-lock ledger for #620. Every result begins NOT_RUN and must bind to one exact implementation source candidate. The existing owner-private Site and plugin identity are preserved.

| Row | Criterion | Surface / case | Planned evidence and pass condition | Candidate / artifact identity | Status |
| --- | --- | --- | --- | --- | --- |
| 17-01 | 620-A1 | Canonical source identity mapping | For every Lab skill/workflow, stable name+kind maps to exactly one canonical catalog record and source path; mismatch fails closed. | pending | NOT_RUN |
| 17-02 | 620-A1 | Generated catalog provenance contract | Generated catalog contains all existing provenance/license/review/source fields and registry digest from the same commit as Lab/adapter. | pending | NOT_RUN |
| 17-03 | 620-A2 | Five provenance states | OWN, EXTENDED, IMPORTED, COMPOSED, UNKNOWN have distinct labels/filters; unknown and missing remain explicit. | pending | NOT_RUN |
| 17-04 | 620-A2 | Unknown and partial metadata | Unknown never renders as OWN; absent upstream/license/review fields render as UNKNOWN/NOT_RECORDED without fabricated claims. | pending | NOT_RUN |
| 17-05 | 620-A3 | Source and upstream lineage detail | Detail shows exact canonical source SHA/path and valid upstream identity/pin/license evidence when present. | pending | NOT_RUN |
| 17-06 | 620-A3 | Components, modifications and orthogonal status | Component/dependency lineage, local changes and verification appear separately from maturity, channel availability, source status and trust/license. | pending | NOT_RUN |
| 17-07 | 620-A4 | Search and provenance/domain filters | Search, both filters, composition, reset, filtered count and empty result work on synthetic fixtures. | pending | NOT_RUN |
| 17-08 | 620-A4 | Keyboard and accessible interaction | Semantic labels/headings, keyboard focus/activation, status announcements and accessible detail controls pass. | pending | NOT_RUN |
| 17-09 | 620-A5 | Desktop layout | Catalog and detail fit desktop browser with no overflow or clipped controls; screenshot retained. | pending | NOT_RUN |
| 17-10 | 620-A5 | Mobile layout | Catalog, filters and details remain usable at mobile width without page-level horizontal overflow; screenshot retained. | pending | NOT_RUN |
| 17-11 | 620-A6 | Site UI and MCP list parity | Exact displayed catalog items and list_skills metadata match for stable identity and provenance on same candidate. | pending | NOT_RUN |
| 17-12 | 620-A6 | Runtime identity parity | runtime_info is verified and separately matches Site mirror revision, canonical source SHA and embedded Lab SHA. | pending | NOT_RUN |
| 17-13 | 620-A7 | Canonical source validators | Provenance registry/schema, catalog generator, repository validations and existing release contracts pass. | pending | NOT_RUN |
| 17-14 | 620-A7 | Site generation/build/contract tests | Cloud Next bundle/catalog freshness, adapter contracts, source sync, TypeScript, lint and Site build pass. | pending | NOT_RUN |
| 17-15 | iteration | Exact candidate read-only smoke | Search/filter/details and MCP list_skills run against exact candidate; preserve response/screenshot hashes; no persistence. | pending | NOT_RUN |
| 17-16 | iteration | Critical unchanged regressions | Two selected existing skill/workflow probes and all existing security/domain contracts remain green. | pending | NOT_RUN |
| 17-17 | iteration | Official private publication receipt | Official Site workflow deploys exact merged source privately; record source mirror SHA, canonical SHA, Lab SHA, actual Site version/deployment and native runtime receipts. | pending | NOT_RUN |

## N/A and deployment boundaries

- Production plugin publication, channel elevation, Site/plugin identity change and access/audience change are excluded. This is a private update to the existing owner-only Site after the user's previously explicit authorization.
- Actual live Site/MCP verification is required; a local build, merged PR or saved version alone is not acceptance.
- Runtime evidence must separately report canonical Skills Factory SHA, provider mirror SHA and embedded Lab SHA. Do not collapse these identities.
- External source/license claims remain those of the canonical registry; no automatic classification or license approval is allowed.

## Completeness and close gate

All frozen acceptance criteria map to passing rows on the final source candidate. Any FAIL, NOT_RUN, BLOCKED or REVIEW_REQUIRED row blocks closure unless an explicit reviewed disposition is permitted by repository governance. Preserve CI, browser screenshots, Site workflow result, native version/deployment and actual MCP receipts.
