# ARC-03 — shared pinned Archify rendering boundary

Issue #376, parent #373. Stacked change depends on ARC-02 PR #386.

The adapter at `scripts/architecture/archify_adapter.py` strictly gates HTML rendering on verified canonical provenance, a pinned checked-out Archify SHA and four actual upstream finalize gates. It writes only into a caller-selected fresh output directory and returns artifact digest + source identity and a forbidden-publication classification. There is no Site embedding or source writeback.

`offline_svg_fallback` generates a self-contained noninteractive SVG using escaped labels, no scripts, links or external assets. Its deterministic coordinates are not Archify and do not establish export parity. Unknown relationships are explicitly dashed.

**Security limitation:** Running an npm/Node subprocess with `ARCHIFY_UPDATE_CHECK_DISABLED=1` is not equivalent to OS-enforced network sandboxing. It must not receive confidential/untrusted input until an externally enforced filesystem, network and resource sandbox is installed. This is a source-level adapter, not a production runtime service. Publication of HTML on privileged origins is prohibited.

The `render` function requires an exact Git source commit and evidence references but does not prove the text supports the architecture claim. Generated HTML cannot be promoted to an authoritative model.

Test locally: `python3 -m unittest discover -s tests/architecture -p 'test_archify_adapter.py' -v`. Full GitHub Actions checks and a real cross-layer invocation are required before merge readiness.
