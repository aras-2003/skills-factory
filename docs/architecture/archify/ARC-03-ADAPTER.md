# ARC-03 — Shared Archify adapter with an enforced renderer boundary

Issue #376; parent #373. Depends on the canonical IR from ARC-02 in main.

## Behavior

- Verifies canonical nodes, edges and source locators against the immutable Git commit before rendering.
- Converts the source model deterministically to pinned Archify JSON. A provenance index maps each rendered node/relation to its model ID, state and exact source references.
- Runs pinned Archify CLI and browser-check inside the Playwright container pinned by image digest `mcr.microsoft.com/playwright@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27`.
- Applies Docker `--network none`, read-only root/source/candidate mounts, separate output directory, dropped capabilities, no-new-privileges, non-root UID and CPU/memory/process limits. The renderer receives no host environment or credentials. Chromium is launched with its nested `--no-sandbox` flag because its own sandbox aborts under this runner's hardened container; containment therefore relies on the outer container boundary, including the runner's default seccomp profile.
- The in-container receipt checks network denial and mount flags. The host receipt records image digest, exact source revision, model digest, output hash and browser gate.
- Generated HTML remains untrusted and is never embedded or published by the adapter. Static SVG fallback is safe and noninteractive, but is not Archify export parity.

## Security boundary

CI pulls the immutable sandbox image before renderer execution and installs the pinned upstream dependencies with lifecycle scripts disabled. The renderer has no network, read-only access to the checked-out upstream and candidate, and write access only to the dedicated temporary output. Chromium's nested sandbox is disabled; the enforced boundary is the outer Docker container and its default seccomp policy, with no added capabilities and no privilege escalation. The boundary test runs in the same container as rendering and fails if any required mount flag or network denial is missing. This verifies the GitHub-hosted Linux runner configuration used by this workflow; it is not evidence for arbitrary deployments or runtime execution outside this wrapper.

The renderer uses a synthetic fixture. Source presence/locators prove provenance, not semantic truth. No production/private data, privileged-origin embedding, writeback or editable PPTX is in scope.

## Validation

- `python3 -m unittest discover -s tests/architecture -p 'test_*.py' -v`
- `python3 scripts/architecture/run_archify_adapter_smoke.py --upstream <exact-Archify-checkout> --output-dir <fresh-empty-directory>`
- CI stores `finalize-receipt.json`, `sandbox-receipt.json`, `provenance-index.json` and generated HTML as a short-retention artifact.
