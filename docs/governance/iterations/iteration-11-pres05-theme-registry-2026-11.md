# Iteration 11 — Presentation theme registry and layout grammar (PRES-05)

- State: ACTIVE (scope lock PR #637 merged at `23c6d29736ca59fbe71728ce7262b50aead9073c`; candidate development starts from this exact post-lock baseline).
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking issue / native Project iteration: #611 / NOT ASSIGNED OR VERIFIED (connected GitHub API cannot read or mutate native Iteration).
- Parent #283 remains open; this increment contributes reusable Marp themes/layouts only and does not satisfy native Figma Slides, client runtime, or full delivery acceptance.
- Previous terminal increment: Iteration 10 CLOSED / ACCEPTED in PR #636, merge `2ebd353277c5c2551ca345ee89cc9fab711c3d41`.
- Baseline main SHA: `2ebd353277c5c2551ca345ee89cc9fab711c3d41`.
- Scope lock tree commit: `bd5746eab94c40315698cf64c62a95af4ab36f24` (record + matrix in one tree, PR #637).
- Started at / closed at (UTC): 2026-11-11 18:35 UTC / pending.

## Frozen commitment

| Issue | Outcome / acceptance IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #611 | 611-A through 611-J | Versioned Marp theme/token registry; at least four visual styles plus simplified editable-safe theme; at least six semantic layout patterns; typography, grid, 16:9, responsive HTML; verified font licensing/fallback and attribution; contrast/readability tests; screenshot regression examples; Markdown-first source/theme/asset manifest preservation; deterministic repeated builds; exercise complex CSS limits in LibreOffice editable export with explicit fail-closed routing. | No renderer duplication; no protected third-party/brand template copying; no change to canonical DeckSpec v1; no Site/Lab registration or deployment; no production promotion; no user data or externally sourced factual exhibit; no closure of #283; no PRES-06 asset-generation pipeline or broader refactor. | #608 canonical DeckSpec v1 (merged/accepted in Iteration 09); #609 isolated Marp adapter (merged/accepted in Iteration 10); #610 format routing/editability contract (merged and its required CI green). Reuse existing adapter, fixture, screenshot and reopen harness. | M |

## Design and ownership boundary

Use the existing Marp adapter under `adapters/presentation-marp/`; extend its theme metadata and tests rather than adding another renderer or competing design token system. Preserve the Markdown source, theme identifier/version, asset manifest and exact pinned runtime receipt. Semantic layouts are named and validated against the registry. A theme that uses unsupported CSS must not be silently downgraded for editable export; the user must explicitly select the `sf-marp-editable-safe` theme.

Theme examples are original generic compositions. Do not copy recognizable protected brand templates. Contrast is checked against WCAG AA normal-text threshold (4.5:1) in tests. Fonts come from the pinned Debian package; record its exact license/attribution and platform fallbacks. No font files are redistributed.

### Pre-lock candidate handling

An unmerged branch, `iter10/pres05-theme-layout-registry`, contains an earlier unreviewed candidate snapshot created before this lock and before Iteration 10 had a terminal record. It is not an accepted implementation, its old commits and any prior test results do not count, and no PR was opened from it. After this scope-lock PR merges, transfer only the proposed file tree onto a new post-lock branch as a new candidate, review every changed file against this frozen scope, and rerun the complete matrix. This records the sequencing deviation; it does not relax acceptance or imply implementation is ready.

## Test and acceptance plan

All acceptance states begin NOT_RUN. Tests run after the full candidate development is frozen. Every verdict binds to the exact main candidate and retained artifact.

- 611-A: registry contract contains 4+ distinct visual styles and the editable-safe variant; stable IDs/versions, tokens, typography, grid, 16:9 intent, CSS complexity and editability metadata validate.
- 611-B: registry exposes at least 6 required semantic layout patterns, with alias compatibility and rejection of unknown layouts.
- 611-C: contrast calculations enforce >=4.5:1 for normal text; font package/version, license/attribution and explicit fallback chain are verified; no protected brand template/asset copied.
- 611-D: synthetic gallery exercises every layout and theme in desktop and mobile HTML; saved screenshots and responsive bounds demonstrate no clipping/overflow at tested viewports.
- 611-E: source Markdown, registry/theme version and asset manifest are preserved; two repeated pinned builds yield equivalent slide content/layout within the documented raster tolerance.
- 611-F: editable-safe CSS excludes unsupported grid/media/gradient features; unsafe progressive theme requested as editable returns an explicit blocked result without silent theme/output downgrade.
- 611-G: the safe theme produces an actual editable PPTX; reopen with LibreOffice, inspect native object counts and compare slide renders against HTML at the declared tolerance. Record limitations rather than claiming fidelity beyond evidence.
- 611-H: theme identity/version and layout identity are present in receipts; color/font fallback and invalid theme input cases fail clearly.
- 611-I: run existing adapter unit/security tests, canonical DeckSpec validation, base integration and the new theme regression workflow on the exact PR head.
- 611-J: run all required GitHub CI and post-merge Validate skills, Domain integrity, Site CI and Marp adapter workflow on exact final main; preserve artifact digest and URLs.

Required surfaces: deterministic local/CI renderer and LibreOffice reopen. Site runtime and deployment are reviewed N/A because this increment does not register or ship a packaged skill. The workflow's screenshot/artifact checks are CI evidence; they do not satisfy parent #283's native authoring/runtime acceptance.

### Regression selection

- Fixed sentinels: #609 all-mode output/reopen/security/fail-closed path; #610 routing and editability manifest contract; canonical DeckSpec validator.
- Rotating unchanged-domain probes: `report-composer` no-unsolicited-artifact and evidence-preservation; `visual-output-design` no-fabrication and capability-preflight.
- Expand coverage if theme changes touch adapter security, input parsing, canonical schema, packaging, or another renderer; do not reduce a failing required case.

## Closure rules

Iteration 11 cannot close with any required FAIL, NOT_RUN, BLOCKED, or REVIEW_REQUIRED row; no percentage threshold overrides a failed criterion. Closeout must identify exact final main SHA, complete matrix, artifacts/digests, all issue/PR status, and the explicit self-review. #611 can be closed only after these rows pass. #283 remains open until its separate native Figma/client runtime and full delivery evidence passes.
