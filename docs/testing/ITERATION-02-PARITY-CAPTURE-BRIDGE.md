# Iteration 2 — exact Work/Site identity and client-flow capture bridge

Scope: #149, #250, #251, #253. This is an OFFLINE adapter, not a
Work/Desktop/browser driver, and never submits a provider request or returns PASS.

## Capture

Obtain from a **fresh, independently authorized** provider session:
1. The exact candidate **Lab** release-manifest.json (Lab source, release_id,
   decoded payload_content_sha256).
2. The raw `runtime_info` output from either Work Lab or Site MCP, as exported
   by the provider. For Site, retain both the Site worker source/release and
   the *embedded Lab* source/release/payload separately. Site's current
   response lacks the embedded Lab `release_id` and decoded payload digest;
   the bridge MUST BLOCK rather than infer either from top-level Site
   `release_id` or Lab ZIP `artifact_sha256`.
3. Four independently captured exact-version flow records:
   `routing`, `architecture-review`, `bar-chart`, `line-chart`. Each
   needs executed tool_trace_sha256, normalized semantic_result_sha256 and
   `observed_lab_source_revision`. Site additionally needs
   `observed_site_server_revision` from the server itself. Charts need
   `client_display_state: observed` from the real client.
4. An independently verifiable observation_source and timezone-aware date.

## Source-normalization command (no provider call)

```sh
python scripts/eval/iteration02_parity_capture_bridge.py \
  --candidate lab-release-manifest.json \
  --runtime-info raw-site-runtime-info.json \
  --flow-evidence observed-site-flows.json \
  --channel site --observation-source 'actual-provider-receipt-id' \
  --observed-at '2026-10-13T15:00:00+02:00' \
  --output .tmp/site-parity-observation.json
```

Repeat for Work (`--channel work` and its separately captured
runtime_info). Run `runtime_parity.py` on both normalized observations.
Do NOT consider `STRUCTURAL_MATCH_PENDING_INDEPENDENT_REVIEW` a behavioral
PASS: all files are user/caller supplied and this script authenticates
neither the client session nor the displayed pixels.

## Fail-closed paths

Old Site server source must not be substituted for Lab source.
Top-level Site release_id is worker identity, not embedded Lab version.
`lab_release.version` is not `lab_release.release_id`.
`artifact_sha256` is the ZIP, not decoded `payload_content_sha256`.
Missing channel support, absent approval, a non-executed flow, screenshot
not observed in Chat, or missing source trace is a STOP.

The existing tool only captures identity and data correspondence. Actual
provider integration requires runtime-exposed trace export and client/browser
observations after merge+Site staging, approved separately.
