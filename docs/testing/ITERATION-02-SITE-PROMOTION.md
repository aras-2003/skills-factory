# Iteration 02 / #259 — Site promotion and rollback preflight (NO DEPLOY)

The repository includes a read-only iteration02_site_promotion_preflight.py.
This deliberately produces no deployable command or credential; it does not
invoke the Site MCP, GitHub deployment endpoints, or Production.

## Independent inputs
1. Exact Lab release-manifest.json: source_revision, release_id, payload_content_sha256, channel=lab.
2. Fresh independently captured Site runtime receipt: attestation_status, offset-aware observed_at,
   observation_source and embedded lab_release with exact source/release/payload.
   Some Site outputs expose ZIP artifact_sha256, which MUST NOT be silently used as payload hash.
3. Immutable rollback artifact: SHA256, source_revision, release_id, payload_content_sha256,
   and immutable_artifact_reference. Branch or 'latest' is not an immutable rollback artifact.

Run the offline plan script with three JSON files:
python scripts/eval/iteration02_site_promotion_preflight.py --candidate-manifest candidate.json
  --observed-site observed-site.json --rollback-manifest rollback.json --output plan.json

PLAN_ONLY_REVIEW_REQUIRED is NOT proof of real Site readiness or installed version.
BLOCKED_INPUT means stop. The script always returns publish_performed=false,
rollback_performed=false and release_approved=false.

## Runtime acceptance and authorized promotion (separate actions)
- Owner approves release artifact SHA, channel/target, independent reviewer, rollback and test plan.
- Repository admin verifies branch protection, publisher permissions and provenance.
- Isolated Site/Chat smoke must capture raw tool/child traces and client-visible chart evidence.
- Actual publish uses designated authorized service outside this script; re-attest exact post-publish
  source/release/tool schema and collect failure/rollback receipts.
- R17 Production-only cases require their own explicit authorization. Never reclassify as Lab PASS.

This is a deterministic source guard for #259/#149/#253/#257, not their runtime PASS.
Actual publisher actions, rollback drill and exact-version client smoke remain NOT_RUN.
