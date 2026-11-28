# Contextual Design Pack — Presentation OS authoring handoff v1

## Purpose and ownership
At the boundary from approved ghost deck and exhibits to actual slide creation, assemble a **self-contained, versioned Design Pack** for the selected generator. This is a *transport representation*, not a second canonical DeckSpec, renderer, skill, or style library. The ghost deck, evidence ledger, approved brand, CreativeDirection, FormatRouteManifest and renderer constraints retain authority. Keep source IDs and uncertain claims intact.

## When to use / when not to use
- REQUIRED for a new deck or material visual redesign, including GPT/Claude/manual authoring or an isolated tool that cannot see chat history.
- For one-slide text edits, reuse the approved existing pack/style and transmit only the affected slide, constraints and affected tokens; do not rebuild a full deck.
- Do NOT synthesize a new brand, silently override an approved template, send confidential assets to an unauthorized service, or interpret a generated image as native editable content.

## Inputs
`DeckSpec{deck_id,revision,slides[]}`, evidence and source IDs, `CreativeDirection`, explicit brand tokens/assets/licences, target presentation profile, `FormatRouteManifest`, destination capability receipts, optional versioned original style/layout recipes.

## Contract: DesignPack v1 (serialize to JSON/YAML or explicit Markdown headings)
Required fields:
- `schema_version`, `deck_id`, `deck_revision`, `pack_id` and `source_refs` (canonical revisions/digests when known).
- `audience_goal`, `format`, `editability`, `privacy_boundary`, `language`.
- `story`: approved thesis, ordered slide IDs, action titles, role/claim, evidence IDs and explicit unknowns; **no invented evidence**.
- `creative_direction`: subject-specific thesis, emotional/visual arc, a signature beat, allowed references and anti-patterns.
- `design_tokens`: typography roles and fallbacks, palette semantic roles, contrast floor, grid/margins/spacing, shape/stroke/icon/image/chart grammar, source/footnote style. Record token origin (`BRAND|LIBRARY|DERIVED`) and any renderer-compatible substitutions.
- `slide_art_direction[]`: for each slide ID, visual objective, dominant exhibit or compositional idea, density, hierarchy, layout recommendation, rationale, allowed variation, references and intended pacing.
- `hard_constraints`: approved facts, data/units/source IDs, brand requirements, format/editability, legibility, rights, accessibility and target capabilities; cannot be creatively overridden.
- `creative_freedom`: optional arrangement, hierarchy emphasis, whitespace, graphical metaphor and composition within hard constraints. Never insist on identical templates merely to match a recipe.
- `destination_instructions`: a fully self-contained prompt derived for **one** chosen destination (or an implementation plan for deterministic native renderer) and its known constraints; no dependence on prior chat.
- `inspection_plan`: inspect montage and high-risk slides; source fidelity, overflow, contrast, substantive visual variation, native editability, export/reopen. Record receipts, not promises.

## Preparation
1. Preserve brand and truth constraints. Where no brand is supplied, derive restrained, legible tokens from audience/purpose; do not claim those are client branding.
2. Use `assets/design-library` as *advice* and select only content-fit patterns; avoid literal mandatory layout grids or cloned commercial templates.
3. For each slide, identify its information job and one primary composition. A layout may recur when the logic genuinely recurs, but avoid mechanically repeated card grids; novel layouts are acceptable if accessibility and target format allow them.
4. Produce one coherent full pack in the authoring context. Distinguish **global tokens** from per-slide visual direction. When sending the pack to a generator, include full tokens and only the approved slide data actually needed; don't repeat whole source documents or lengthy conversation history.
5. Choose **one** generator/renderer via the existing format preflight. If the generator is context-isolated, send the pack verbatim with the storyboard and explicit evidence links. If deterministic rendering is used, compile applicable tokens and layout rules into that renderer's existing model, report unsupported requests rather than inventing behavior.
6. Capture pack revision/digest if computation is available; record `NOT_COMPUTED` otherwise. Keep `pack_id`, selected style IDs, per-slide chosen layout IDs, destination and capability receipts in the run manifest.

## Prompt skeleton supplied to selected model
```text
ROLE: Presentation art director and slide author, not a source of business facts.
GOAL / AUDIENCE / OUTPUT: <from approved brief and FormatRouteManifest>
CANONICAL STORY: <ordered slide IDs, action titles, evidence IDs, unknowns>
DESIGN SYSTEM: <semantic tokens, typography, layout rules, accessibility, provenance>
ART DIRECTION: <creative thesis, arc, signature moment, slide-by-slide composition>
HARD CONSTRAINTS: <brand, factual integrity, privacy, source fidelity, editability>
CREATIVE FREEDOM: <allow original compositions within hard constraints; avoid repetitive layouts>
DESTINATION: <observed capabilities; tool-specific output/authoring instructions>
QUALITY: <render, inspect, critique, revise with actual receipts>
RETURN: <artifact IDs only when created, design-pack ID, mapping and verification states>
```

## Routing examples (instructional, not acceptance evidence)
**Positive:** executive transformation deck, approved evidence, editable PPTX required -> select verified native-editable route; transmit design tokens and per-slide compositions in one self-contained pack; use native shapes and actual charts, verify rendered pages and object editability. Do not silently switch to image-backed Marp PPTX.

**Near miss:** one typo in existing slide -> preserve the approved visual design, avoid regeneration of the full pack and deck. If user explicitly requests redesign, treat as a new pack revision instead.

**Failure:** a model tool offers beautiful slides but no verified native editability while requested output is editable PPTX -> mark `BLOCKED_CAPABILITY`, give no false delivery claim. A hypothetical quoted ROI value remains unverified; it must not appear as an established KPI chart.

## Quality/evaluation
Compare **A: baseline authoring workflow** vs **B: DesignPack-enabled authoring** with the **same versioned content and requested output**, on at least one executive deck and one teaching/technical deck. Use matched model/tool/runtime where possible, record tokens/time and actual renders. Score independently: narrative fidelity, slide-specific composition, visual consistency, legibility, supported factual claims, editability and export. Critical errors block acceptance; report `NOT_RUN` if a required model/renderer or independent visual reviewer is unavailable. Never call the design successful from this specification alone.
