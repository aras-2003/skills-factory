# ARC-07 CI fixture matrix

All rows use deterministic temporary Git repositories and a pinned full source commit. This is CI evidence for source extraction and export contracts; it is not a ChatGPT/Site runtime result.

| Case | Fixture path | Expected result | Test |
| --- | --- | --- | --- |
| OAF source → IR → candidate → static export | Synthetic capability map with typed owners/processes/apps and explicit ownership gaps | Exact source revision is verified; candidate and bundle preserve all node/relation IDs and counts; unknowns remain labeled | `test_oaf_source_ir_candidate_and_static_exports_share_exact_fixture` |
| Skills Factory source → IR → candidate → static export | 13 source skills and 7 workflow files, including a documented receipt gate | Exact source revision is verified; candidate and bundle preserve all IDs/counts | `test_skills_factory_source_ir_candidate_and_static_exports_share_exact_fixture` |
| Invalid source revision | Non-SHA revision supplied to OAF extractor | Reject before extraction | `test_invalid_source_revision_and_stale_evidence_fail_closed` |
| Stale evidence | Model revision differs from evidence revision | Canonical validator and source verifier reject | `test_invalid_source_revision_and_stale_evidence_fail_closed` |
| Unknown relation | OAF fixture includes unresolved ownership relations | Static SVG and text equivalent retain every unknown relation and its status | `test_unknown_edges_remain_explicit_in_svg_and_text_export` |
| Renderer unavailable | Pinned sandbox image is absent | Renderer fails closed; no partial HTML or success receipt is emitted | `test_renderer_failure_does_not_emit_success_receipt_or_partial_html` |
| Invalid export IR | Dangling relation endpoints | Export rejects before creating output | `test_invalid_ir_export_fails_before_any_artifact_is_created` |

The GitHub Actions checks on an exact PR head provide the candidate source version. The ARC-03 workflow separately runs the pinned sandbox renderer against the exact-source Skills Factory and OAF smoke cases and records its receipts.

Runtime classification for this CI package: `NOT_RUN`. Exact deployed Site/Lab identity, Chat tool invocation, and user-visible rendering require a separately authorized runtime session and must not be inferred from this test suite. No READY claim is made here.
