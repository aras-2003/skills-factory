# Iteration 15 / ES-01 acceptance matrix

Scope-lock ledger for #616. Every row is **NOT_RUN** at lock. Bind every result to the exact candidate SHA, source inventory, artifacts and test surface. Do not infer implementation or execution from schema design or static inspection.

| Row | Criterion | Surface / case | Planned evidence and pass condition | Candidate / artifact identity | Status |
| --- | --- | --- | --- | --- | --- |
| 15-01 | 616-A1 | Canonical schema positive fixtures | OWN, IMPORTED, EXTENDED, COMPOSED, UNKNOWN and mixed-origin composition fixtures validate against the versioned schema. | Pending | NOT_RUN |
| 15-02 | 616-A1/A2 | Schema negative fixtures | Missing/contradictory required fields, malformed immutable digest, and unsupported provenance/license combinations fail with actionable errors; no inferred OWN or SPDX claim. | Pending | NOT_RUN |
| 15-03 | 616-A2 | Lineage preservation | Imported/extended upstream and local change lineage plus all composed child origins/revisions survive parse, migration, serialization and generation. | Pending | NOT_RUN |
| 15-04 | 616-A3 | Complete source inventory and migration | Every skill/workflow on the locked baseline is represented and classified or explicitly UNKNOWN; before/after counts and migration report reconcile; source behavior and unrelated metadata remain intact. | Pending | NOT_RUN |
| 15-05 | 616-A4 | Catalog projections | CATALOG.md and docs/catalog.json are generated from canonical source metadata; taxonomy, unknown states and lineage projections agree without mixing maturity/channel/security/license. | Pending | NOT_RUN |
| 15-06 | 616-A4 | Lab/production and release projections | Capability and release manifests consume the same canonical schema; consumer contract/version compatibility is demonstrated on packaged output. | Pending | NOT_RUN |
| 15-07 | 616-A5 | Deterministic clean build | Two clean migration/generation runs from identical inputs produce byte-identical source-independent outputs and hashes; generation does not modify source records. | Pending | NOT_RUN |
| 15-08 | 616-A6 | Shared regressions and CI | Catalog-to-package identity and provenance orthogonality sentinels pass; affected existing validators/packaging/domain integrity and exact-main workflows pass; no secrets or external execution paths are introduced. | Pending | NOT_RUN |

## Inventory and execution totals

| Layer / surface | Required distinct scenarios | Planned executions / repetitions | Executed PASS | Executed FAIL | NOT_RUN / BLOCKED / REVIEW_REQUIRED | Reviewed N/A | Evidence compatibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Schema/parser fixtures | 6 positive incl. hybrid; at least 4 negative | one suite per candidate plus PR and exact-main CI | 0 | 0 | All | 0 | Pending exact source schema/test revision |
| Inventory/migration | Complete locked skill + workflow inventory | one migration report plus clean repeat | 0 | 0 | All | 0 | Pending baseline and inventory digest |
| Catalog and manifests | 4 derived output families | 2 clean generation runs; PR and exact-main package checks | 0 | 0 | All | 0 | Pending exact candidate and output hashes |
| Shared regressions | 2 fixed sentinels + 2 rotating unchanged-domain probes | 1 coordinated validation lane, each case individually receipted | 0 | 0 | All | 0 | Pending candidate and receipts |

Completeness review: every frozen criterion maps to rows 15-01–15-08; all rows are required. No runtime N/A is used to waive static/package consumers. Final closure requires every required row PASS on compatible candidate evidence, exact-main checks, complete issue reconciliation, and no unresolved blocking defect.
