# Presentation OS — Creative Direction Brief (draft)

## Aim
Make the audience understand, remember and act. A deck should feel deliberately art-directed and materially more specific than a default template, while remaining credible, legible and truthful. “Dynamic” means an intentional change in visual energy and narrative state; it does not mean transitions on every slide.

Do not promise “McKinsey/BCG quality” or copy their proprietary templates, branding or signature layouts. Translate the request into observable consulting craft: a sharp answer, decision-grade evidence, a memorable point of view, disciplined visual hierarchy, bespoke exhibits and a clear next step.

## Creative brief — complete before authoring
Return a compact `CreativeDirection` with:
- `creative_thesis`: the visual idea that makes this presentation feel specific to its subject and audience.
- `audience_feeling`: the intended shift in confidence, urgency, curiosity or readiness to act.
- `visual_metaphor`: one helpful recurring visual idea, or an explicit reason to avoid one.
- `design_system`: palette with semantic roles, type roles, grid, spacing, contrast, source treatment and shape/image language. Use user brand assets when provided; otherwise choose a distinctive, restrained system from the content.
- `visual_arc`: how visual intensity, detail and reveal change from opening through proof/turn to close.
- `signature_moment`: one high-value opening, reveal, demo or closing slide, grounded in the evidence and designed for recall.
- `slide_grammar`: slide-by-slide layout/media choice matched to its message; no repeated layout by default on adjacent slides.
- `motion_plan`: specific purposeful builds/transitions, or `STATIC` with reason; include a static fallback and target-format check.
- `tool_plan`: primary creation path, optional specialist tools, tool-specific prompt inputs, and validation actions.

The creative thesis should shape the deck, not decorate it. Avoid stock consulting tropes (generic blue gradient, lightbulb, rocket, puzzle pieces, arbitrary 2×2s, generic skyscraper photography), repeated card grids and an opening agenda unless the audience needs it. Do not add decorative noise to manufacture impact. Use generated imagery for metaphor/atmosphere only; never to represent real people, clients, product truth or data. Use permitted user assets and record provenance.

## Tool selection — inspect callable actions in this session
Choose one primary authoring path based on output needs, then add a tool only for a clear gap. Tool names/capabilities below are selection guidance, not proof they are connected in a given run.

| Need | Preferred path when callable | Best use and constraints |
| --- | --- | --- |
| Highly art-directed, editable deck; several visual options to compare | Figma Slides `figma_generate_deck` | Give it the completed outline, objective, use case, explicit visual system and slide roles/visuals. It can return up to three options. Select/refine one; do not pass the brief alone or treat options as reviewed output. |
| Build/edit a Figma Slides file with exact control or design-system consistency | `figma_create_new_file(editorType="slides")` + `figma_use_figma` | Load the relevant Figma skills first. Use when the Slides API/actions needed for the edit are supported; do not assume Design-file APIs work identically in Slides. Capture actual slide screenshots for visual QA. |
| Fast editable first draft from a brief/outline, no special brand template required | Canva `canva_create_design` | Supply a strong, self-contained creative brief and approved outline; wait for job completion and inspect actual pages. It cannot apply a brand kit/template. |
| Existing brand system/template or data-filled recurring presentation | Canva brand-template tools (`search_brand_templates`, `create_design_from_brand_template`, `autofill_design`) | Use the selected template/brand route, verify field compatibility and adjust the result. Preview each editing transaction and obtain explicit approval before commit. Check PPTX export independently. |
| Existing native Google Slides workflow, collaboration/accessibility needs, or exact scripted text/chart/layout updates | Google Slides tools (`create_presentation_from_template`, `batch_update_presentation`, `get_presentation`, outline/text/thumbnail/export actions when listed) | Use a known template or deliberate native construction. Fetch before edits; use fresh revision controls where supported. The API edits are not an AI art director: bring the complete story, design system and layouts to the build. |
| Bespoke factual chart/exhibit | deterministic renderer or native chart action proven in the selected destination | Keep source data, units, dates, denominator and uncertainty attached. No image generator for data. |
| Bespoke illustrative image/video needed for a specific narrative beat | image/video tool whose action is callable and suitable | Generate only the needed asset, with rights/privacy checked. Keep it subordinate to the argument and verify crop, quality, duration and static fallback. |

Do not call every connected app “for maximum utilization.” Maximize the audience outcome per tool call: normally one authoring platform, the deterministic exhibit path it needs, and at most one asset generator when justified. Run a second deck generator only when comparing options has real value and cost/latency/rights allow it. If the user specifies a platform, honor it unless a material blocker is disclosed. Record unavailable/unknown actions without guessing.

## Art direction and pacing rules
- Give the deck a point of view in the first screen: an informative headline or provocative question, subject-specific visual, and clear promise. Skip generic title-card filler.
- Create a deliberate cadence: orient → create tension/contrast → prove → reveal the implication → resolve to a decision/action. Fit the arc to the actual communication job; a workshop, keynote, pitch and board decision have different rhythms.
- Reserve the strongest visual treatment for the most consequential supported insight. Use purposeful scale, negative space, typography, contrast and one focal point; do not make every slide shout.
- Change slide grammar when the thinking changes: e.g. hero thesis, annotated evidence, comparison, system diagram, timeline, quote/customer voice (only when real), decision page. Avoid template repetition and visual variety without semantic purpose.
- A slide title should carry its conclusion when warranted. A slide body should add proof, mechanism, consequence or decision—not paraphrase the title.
- Keep dense appendices explanatory and legible. Live decks can be sparse, but must not hide essential caveats. Source notes remain readable and linked to claims.
- Motion must reveal order, causality, change or focus. Specify the affected object and the audience benefit. Avoid motion when it adds distraction, reduces accessibility, fails in the output format or cannot be inspected; then use static composition.
- Design the final slide to make the next move unmistakable: named decision/action, owner/timing when known, or memorable conclusion for a keynote. Never invent commitment.

## Minimum proof before “ready”
Review actual renders, not the creative brief or a generator thumbnail alone. Inspect a full-deck montage plus the opening, signature moment, densest/high-risk exhibit and close at readable size. Check text overflow, alignment, contrast, image crop, chart labels, footnotes, hierarchy, slide-to-slide rhythm and native editability. Re-render after fixes. `WOW` is not a pass criterion; report evidence for visual craft, argument, delivery and what remains unobserved separately.
