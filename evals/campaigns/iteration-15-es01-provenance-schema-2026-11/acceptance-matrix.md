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


## Candidate results — final exact-main candidate

The scope-lock table and planning totals above are historical. Results below are bound to implementation PR #662 and exact main candidate **bb255409fc0eabba494a17841d3528459aeb7201**. Follow-up PR #663 added the explicit repeated catalog-generation check required by 15-07; its exact-main checks passed on the candidate below.

- Canonical registry digest: **c22f94c64e39e03d592039000371dfc824304d447b32c8d3e87cdfcf6422cc11**.
- Source inventory digest: **a8e6a1d8874385614f98b4133b44bda563804e8fea20f7d8a30558ad22ee420e**; migration audit: 98 records (79 skills, 19 workflows), all explicitly UNKNOWN; external sources executed: false.
- Generated output SHA-256: CATALOG.md **0377975c99cb155e010671bc065fa55360c73c2cb1af75ab84071812a32c26c8**; docs/catalog.json **4c3c80b1bf9f23f51c8d955e2468151310e1cf6e59066075624dcbac51b3f62e**.
- Exact-main Lab build artifact: [run 43404821655](https://github.com/aras-2003/skills-factory/actions/runs/43404821655), artifact **skills-factory-lab-bb255409fc0eabba494a17841d3528459aeb7201**, SHA-256 **96be0ceffda710f3dd69ab83bae2b1a133cc9e65ba33e76a12d1dfe02b7c12a3**.
- PR implementation head **e17a3165d1739eb4e5dde6fb7d9956add0efa79c**; PR #662 checks passed. Reproducibility PR #663 head **876fcad82d5e0a6d79ede1910b02b144cae9b3b0**; PR checks passed.
- PR #662 checks passed, including [Skills Factory Site CI](https://github.com/aras-2003/skills-factory/actions/runs/43401805021). Exact-main checks all passed: [Validate Skills / full matrix](https://github.com/aras-2003/skills-factory/actions/runs/43404821673), [Domain Integrity](https://github.com/aras-2003/skills-factory/actions/runs/43404821698), [Lab build](https://github.com/aras-2003/skills-factory/actions/runs/43404821655), and [Pages deployment](https://github.com/aras-2003/skills-factory/actions/runs/43404820917). The Validate run includes source/registry/catalog, eval/packaging, security/capability, governance, domain/readiness/release, Lab/production artifacts and all optional package profiles.

| Row | Verdict | Candidate-bound evidence |
| --- | --- | --- |
| 15-01 | PASS | scripts/provenance/tests/test_catalog.py validates OWN, IMPORTED, EXTENDED, COMPOSED, UNKNOWN, a mixed-origin composition, and an external-base/local-change hybrid. Exact-main source/registry job passed. |
| 15-02 | PASS | Five contradictory or incomplete fixtures fail closed: OWN without evidence, malformed imported digest, undocumented EXTENDED changes, single-child COMPOSED, and UNKNOWN with an upstream claim. The five provenance tests passed on PR and exact main. |
| 15-03 | PASS | Projection tests preserve each composed child's own provenance; hybrid imports remain EXTENDED with upstream identity and documented local changes. Registry validation rejects dangling/self references, cycles and stale source hashes. |
| 15-04 | PASS | Migration audit reconciles every source at the locked revision: 79 skills + 19 workflows = 98, all UNKNOWN, without inferred ownership/license/attribution. migrate.py --check passed; the unit fixture compares two migrations and registry digests. |
| 15-05 | PASS | Catalog generation uses the canonical registry; source-contract CI generated both views and git diff --exit-code passed. Output hashes are recorded above; provenance remains separate from maturity and capability assessment. |
| 15-06 | PASS | Production and Lab manifests carry the same registry digest/projections; package validation and Lab/production artifact checks passed. Optional remote-MCP, skills-only and ChatGPT ZIP profiles also passed. Lab ZIP digest is recorded above. |
| 15-07 | PASS | Migration fixture compares two reconciliations and digests. Updated CI ran the catalog generator twice from the same clean checkout; both outputs had identical SHA-256, and generation left the registry and migration audit unchanged. Exact-main source job logged both successful generator runs. |
| 15-08 | PASS | PR and exact-main validation passed: source/schema, 92 repository validation tests, 5 provenance tests, campaign/packaging, security/capability, governance, domain/readiness, all package profiles, Lab build and Pages; PR Site catalog/Worker CI also passed. No Site application behavior changed. No secret, runtime execution or promotion path was added by this iteration. |

| Result | Count |
| --- | ---: |
| Required acceptance rows PASS | 8 |
| Required rows FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED | 0 |
| Registry inventory | 98 (79 skills, 19 workflows) |
| Valid provenance fixtures | 6 (including hybrid and mixed-origin composition) |
| Invalid provenance fixtures | 5 |
| Catalog generations compared | 2; byte-identical outputs |

### Resolved validation defects

| Finding | Resolution | Evidence |
| --- | --- | --- |
| Packaging assertion initially selected financial-modeling, which is candidate maturity and therefore absent from the production profile. | Select an actually included production skill and assert its provenance projection; update the Iteration 07 test-source hash pin only. | PR #662 final head and passing exact-main evaluation/packaging checks above. |
| Iteration 07 source pin became stale after the packaging assertion changed. | Refresh the single test-file digest; historical runtime/candidate evidence and deployment identifiers remain unchanged. | PR #662 final CI and final source-contract check. |
| First reproducibility workflow draft wrote checksums before creating .tmp. | Create the scratch directory before the two generation runs. | PR #663 head and successful exact-main source-contract check. |
