# Consulting reference → Presentation OS semantic bridge (first implementation slice)

## Why
The previous CIO example generated technically openable but visually weak artifacts. A renderer/valid JSON alone cannot prove consulting-grade quality. This slice reuses the *verified historical source register* rather than re-auditing seven ZIPs or copying external text/code. References are **not** official McKinsey/BCG outputs; none of the community repos implies brand affiliation. Sources without redistributable permissions are reference-only.

## Actual implementation
- `consulting-reference-patterns-v1.json` holds pinned sources, license boundaries, six original slide-composition principles.
- `scripts/presentations/reference_style_bridge.py` maps canonical DeckSpec v1 `slide_id`, `role`, `claims` into a deterministic, inspectable layout plan with explicit reference IDs and revisions.
- `tests/presentations/test_reference_style_bridge.py` tests positive, no-pattern, missing-claim, contradicted-claim, duplicate-ID, invalid-status paths.
- Produces *only a semantic plan*: explicitly emits `render_status: NOT_RUN`, `editable_export_status: NOT_RUN`. It neither calls external skills nor imports unapproved helpers.
- No changes to the canonical deck schema, renderer, skill packaging or production channel.

## Usage
```bash
python -m unittest discover -s tests/presentations -p 'test_reference_style_bridge.py'
python scripts/presentations/reference_style_bridge.py path/to/canonical-deck.json --out /tmp/reference-plan.json
```

The `role` can be one of: `decision`, `options`, `capability`, `architecture`, `roadmap`, `kpi`. Unsupported roles yield NO_PATTERN rather than a fabricated style match. Claims with unknown status or malformed IDs are rejected; missing or contradicted evidence blocks confident selection.

## Known gaps and next gates
1. The design principles are independently authored hypotheses informed by the *repository-level audited corpus*. **They have not been extracted via a newly executed page-by-page visual examination**; therefore they do not constitute a validated BCG/McKinsey/Accenture slide benchmark.
2. Secure intake and execution of `openai/skills` slides candidate remains BLOCKED in #621; Marp Uncover remains only a candidate. This bridge does **not** call either.
3. Native PPTX rendering, visual comparison, geometry, editor roundtrip, repeatability across runtimes and human review remain NOT_RUN for this increment.
4. Next scope: validate pattern use against real exhibits from official public company reports, integrate into existing #611 theme and #612 exhibit pipeline, render 10-slide CIO golden fixture and run independent visual QA under #613. Do not claim end-to-end quality PASS until that occurs.

## Traceability
Source evidence: #450 / PR #508; external presentation candidates and intake blocker #621; parent Presentation OS #283; renderer reuse #608; theme #611; assets #612; cross-format QA #613; architecture IR #739.

**Acceptance in this change:** semantic plan and source-lineage implementation delivered; test execution CI/host to verify; real deck/visual score NOT_RUN.
