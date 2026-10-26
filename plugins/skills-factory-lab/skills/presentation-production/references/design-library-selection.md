# Presentation Design Library — selection contract (v0.1)

After the evidence-backed ghost deck is set, but before authoring, inspect `assets/design-library/README.md`, `templates.json`, `fonts.json`, and `sources.json`.

1. Translate brief into `{audience,purpose,density,medium,brand_style_id?}`; use `python assets/design-library/select_design.py --brief brief.json` when an execution environment is available; otherwise apply the matching tags/rules transparently and state that script was not executed.
2. Choose a style on communication fit, not popularity or aesthetic alone. Take top recommendation as candidate, compare against brand constraints, audience accessibility and slide narrative. Keep the layout selection within slide-specific content/semantic exhibit needs; NEVER inject unsupported chart values or fabricate architectural relationships.
3. Do not retrieve or embed reference-only template files, images, logos or commercial fonts. Original layout recipes are safe as instructions, not a guarantee of asset rights. Rights reviews are per target/output.
4. Log `style_id`, `layout_id` per slide, palette, font fallback, manifest version, rationale, deviations, source reference URLs (only if actually consulted) and renderer/editability receipts in DeckRun.
5. If selector is missing/unavailable, follow existing `creative-direction.md` and mark design-library selection NOT_RUN. Do not gate all Presentation OS operation on this experimental library.
6. Release requires a controlled board-decision vs teaching/keynote evaluation, screenshots and editable-PPTX verification; selector ranking alone is not proof of visual quality.
