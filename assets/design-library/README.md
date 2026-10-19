# Design Reference Library — v0.1 (Presentation OS pilot)

Status: experimental, branch-only. **Not** an asset download service or an assertion of license clearance.

## Rules
1. Read the presentation-production workflow's creative-direction, quality and provenance contracts first. This library only supplies candidate art direction and layout grammar; it never determines facts, storyline, evidence, renderer availability or delivery status.
2. Use `sources.json` for discovery/reference only. `templates.json` includes original semantic layout recipes, not copied external slide assets. No scraping, hotlinking or redistribution by default.
3. A template may be instantiated only when `rights.mode = original_recipe`, or when an external asset has separately documented usage rights, attribution and redistribution conditions for the current purpose. `reference_only` must never be used as an editable asset.
4. Run `select_design.py` to rank candidates deterministically. Scores express match to brief, never measured output quality. Brief requires audience, purpose, medium and density. Explicit brand overrides recommendations; high-stakes decks constrain novelty.
5. After selection, preserve selected template/style/font IDs and selector rationale in deck run provenance. Capability preflight still governs which authoring/export adapter can run.
6. Do not bundle font binaries. Installed fonts must be checked in the target environment, including Polish characters and Unicode. `fonts.json` is advisory with links for license review.
7. Never present an external commercial template as owned. Editorial evaluation + real render/export parity gates remain mandatory.

## Pilot acceptance
- Board-decision brief defaults to restrained layouts, not keynote layouts.
- Training/keynote permits narrative/hero layouts, not dense leave-behind.
- Finance exhibits prefer data-first grammar.
- An incompatible target or rights restriction returns a warning rather than silently overriding the brief.
- Same brief and versioned manifest produce same ordered recommendations; provenance is recorded.
- No external copyrighted media or font binaries in repository.
