---
name: visual-output-design
description: 'Select and render one source-backed exhibit for a report, presentation
  or local interactive component. Route quantitative charts, diagrams, illustrative
  imagery, motion and interactive HTML to suitable specialized renderers while preserving
  evidence. Use beneath report-composer, report-document-architecture or presentation-exhibit-design;
  do not replace those workflows or invent data for visual balance.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.13.0
  maturity: candidate
  risk: low
  last_reviewed: '2026-10-09'
---

# Visual Output Design

## Purpose
Select and render one evidence-backed exhibit for an already-defined local information need. This shared exhibit specialist
is called by `report-composer` for chat, `report-document-architecture` for long-form documents, and
`presentation-exhibit-design` for slides. It does not own the structure of a full report, document, deck or full interactive site.

Preserve the source analysis, evidence, uncertainty and canonical data contracts while choosing the best visual medium available in the runtime. Follow `../report-composer/references/report-state-and-evidence-contract.md` for renderer/client-state semantics.

## Modality routing and finish
- Choose the medium from the reader job and target surface before choosing a tool: chart, diagram, table, illustration, motion/GIF or interactive HTML component.
- Use the most specialized available renderer for that medium. For diagrams use the diagram authoring capability; for illustrative assets use a suitable image/video generation capability; for actual slides use presentation authoring tools. Invoke these only when the requested visual needs that medium.
- Preserve one semantic `ExhibitSpec` across renderers: purpose, claim/evidence IDs, data or source asset, provenance/license, as-of context, labels/units, interaction, accessibility text and renderer receipt. A specialized renderer improves execution; it does not establish factual validity.
- Keep visual quality intentional: clear focal point, restrained palette, readable labels at target size, alignment/spacing, contrast, responsive behavior and accessible text alternative. Avoid decorative charts, generic stock-like illustrations, unnecessary motion and inconsistent visual language.

## Preconditions
- The underlying analysis/result already exists or can be produced by the calling workflow.
- Visualisation must not become a second analytical engine.
- Decision-relevant data must retain source/provenance and as-of context.

## Procedure
1. Identify the local decision/comprehension job supplied by the calling workflow or `report-composer`.
2. Read the requested `target_format` from the composition brief: `chat`, `web`, `docx`, `pdf`, `pptx` or another explicitly named format. The target owner controls layout and export; preserve one semantic ExhibitSpec while adapting its rendering and interaction to that format. Never promise web interactions in a PDF or editability in a flattened asset.
3. Decide whether a visual materially improves the result and whether the caller marks it as required by the visual floor.
4. Run `capability_preflight` against the capabilities actually exposed by the host runtime and return its status explicitly in the output:
   - inspect callable tools and host-native components actually documented and exposed in the current runtime;
   - bind the slot to a concrete renderer and classify it as static, hover-interactive, or control-interactive only when those behaviors are documented or observed;
   - do not invent a native `chart` call or response syntax because a platform is known to support charts elsewhere;
   - a quantitative renderer must deterministically encode supplied numeric series/categories;
   - when Skills Factory Cloud Next exposes `render_bar_chart` or `render_line_chart`, treat it as a concrete interactive inline MCP App renderer for a report visual slot. This low-level tool is called internally through this skill; it is not a standalone user-facing report workflow. Keep the chart in the same Chat conversation flow and do not request fullscreen.
   - route structural diagrams to a deterministic or editable diagram renderer, illustrative imagery/motion to an appropriate media generator, and slide-native exhibits to slide authoring. Do not use image generation for factual charts, and do not force one renderer to serve every modality.
   - `image_gen`, image viewing, generic media generation and Figma diagram/design capabilities do not qualify as quantitative data-chart renderers;
   - return `AVAILABLE`, `UNAVAILABLE`, or `UNKNOWN` for each requested interaction level, separately from ordinary static-renderer availability; include the concrete renderer/capability inspected and evidence or reason.
5. If the visual is optional and no deterministic renderer exists, use the truthful text/table fallback.
6. For a **required investment price/KPI visual**:
   - render verified data with the best concrete renderer available;
   - when a documented interactive component is callable, prefer it for the interaction the user asked for;
   - when only a static renderer is available, produce a static inline image and label it static;
   - if the user specifically requires selectors/filters and none are supported, mark that interaction feature `BLOCKED_NO_RENDERER` while keeping any useful static chart separate;
   - if a concrete renderer invocation fails, use `FAIL_RENDERER_INVOCATION`.
7. For other required visuals with no qualifying renderer, return `BLOCKED_NO_RENDERER`; do not claim successful rendering and do not let a table/text fallback satisfy the visual slot.
8. Build a semantic visual model from the supported analysis only:
   - headline/message;
   - entities/categories;
   - measures/units;
   - relationships/order;
   - time/as-of context;
   - uncertainty/status;
   - source/provenance references.
9. Select the narrowest suitable renderer using `references/tool-routing.md`.
10. Apply the design and integrity rules in `references/design-system.md`.
11. Prefer a renderer that can appear directly inside the chat response. Use an external-artifact renderer (HTML file, Figma file, PDF, deck) only when the user explicitly requested that output form.
12. Keep the visual synchronized with its surrounding report section: it must not imply a stronger conclusion than the written analysis.
13. Provide a compact text/table fallback when useful. If the chart renderer itself is unavailable, label the visual slot diagnostic and keep it `BLOCKED_NO_RENDERER`. If only the requested interaction controls are unavailable, mark that feature separately and keep a successfully rendered static image at `PAYLOAD_RENDERED`.
14. For interactive HTML, keep analysis data and presentation logic separated so the report can be regenerated from the same payload.

## Interaction honesty and investment chart layout

Classify the actual affordance, not the visual's appearance:
- **STATIC**: an image or chart with no user-operated interaction.
- **HOVER**: a documented native chart provides hover/tooltips, but the reader cannot change the series, metric or period.
- **CONTROLLED**: a real selector/filter/range control changes the displayed data view.
- **UNKNOWN**: the returned payload or runtime does not establish which interaction exists.

A control-interactive dashboard requires evidence that the control is part of the actual emitted component. A static PNG with a dropdown drawn into it is still STATIC. Do not call hover-only behavior a selectable/filterable dashboard. If the user asks to test controls, state what control was operated and what view changed only when that action was observed; otherwise say interaction was not verified.

For a multi-candidate investment report:
- render one shared price chart indexed to 100 only when two or more verified price series overlap in dates and use compatible adjustment definitions;
- label the base date, quote currency, price-adjustment/dividend basis, as-of date and sources; do not call price-only performance total return;
- if series are not comparable, chart separately or explain the precise blocked slots;
- use separate KPI charts for each company's thesis-driving metric and retain each unit;
- show a chronological line for at least three real dated observations; show two points as a direct period comparison, not a trend;
- do not fill missing periods, interpolate or collapse separate KPI dimensions into one score;
- prefer one shared indexed-price chart plus candidate-specific KPI charts, placed beside the relevant candidate narrative.

## Inline visual delivery integrity

A visual slot is complete only when a valid chart, widget, or image is emitted as a native visual element in the chat response and placed beside the relevant analysis.

- Never print, quote, or expose a data:image/...;base64,... payload in prose, a Markdown image URL, a code block, or a table. Do not stringify binary/image content.
- When a renderer returns an image content block, preserve it as the renderer's native image output; add only a short caption, as-of date, and provenance in text.
- Use a native interactive chart only through a real host-supported response mechanism. Do not invent a chart tool, widget call, or response syntax that the runtime does not expose.
- A valid static image is a useful inline visual when interactivity is unavailable, but label it static; do not claim hover, filtering, or interaction.
- If no actual inline visual can be emitted, mark the slot blocked/failed and show a concise diagnostic table. A URL, base64 string, or JSON payload printed as text is not a rendered visual.

## Hard stop: renderer output must be present

Do not report or caption a chart as completed based on a planned render, tool availability, numeric data, a tool-call attempt, or a chart specification. For every required slot:
- invoke the documented renderer that is actually available in this runtime;
- verify the result includes a native image/chart payload;
- include that returned visual payload in the user-facing response next to its analysis;
- only then describe the chart as present or state what it shows.

If the renderer returns no embeddable image/chart, or the response surface cannot include it, the slot is blocked/failed. Say so plainly, provide a compact diagnostic table if useful, and remove language such as “the chart shows”, “the chart captures”, “inline chart”, or “static chart” unless the visual itself is present. Never substitute a Markdown link, placeholder, caption, JSON, or encoded image text for the returned visual.

## Decision rules
- Prefer one strong visual over several decorative ones.
- For required investment-history visuals, use the best concrete renderer available. Prefer a documented interactive component when it is callable; otherwise render and label a static image. Do not infer a chart API from tool-list uncertainty.
- When another required visual has no suitable renderer, return `BLOCKED_NO_RENDERER`; text-only is not a successful substitute.
- Prefer the visual grammar in `references/design-system.md`: horizontal bars for ranked concentration, real time-series lines for performance, matrices for overlap/trade-offs, ranges for scenarios, KPI strips for a few metrics.
- Use a chart for quantitative comparison, trend, composition or relationship.
- Use a diagram for structure, flow, dependency, ownership or state.
- Use chat-native interactive components/widgets when available for linked views, filters, horizon switches or hover detail.
- Treat a host-native chart as available only when the current runtime documents or exposes a concrete callable mechanism; do not assume a widget API by name.
- Use interactive HTML only when the user explicitly requests HTML/a file or an external interactive artifact.
- Use Figma/FigJam only when the user explicitly requests an editable design/diagram artifact or when the calling task explicitly requires Figma output.
- Use Figma Slides/deck output only when the user explicitly requests a presentation/deck.
- Use generated imagery only for illustrative assets, never to encode factual quantities or organizational truth.
- Do not use ASCII art or punctuation-based pseudo-charts in professional decision reports.
- Do not expose raw Mermaid code fences to the user. Mermaid is acceptable only when the runtime renders it as an embedded visual; avoid Mermaid xychart when a better native chart/widget is available.
- Do not create a single composite score merely to simplify a visual when the underlying dimensions should remain separate.
- Never infer missing values, dates, hierarchy, weights or causal links just to make a chart or diagram look complete.
- For organizational or operating-model diagrams, encode only relationships, reporting lines, ownership and decision rights present in the source evidence. Mark absent or disputed links `UNKNOWN`/`UNRESOLVED`; never add a plausible reporting line, hierarchy, or accountability relationship to make the diagram look complete.
- In dashboard HTML, keep the source payload and its provenance separate from presentation code. Every displayed value must map to a supplied payload field or a reproducible transformation; presentation labels/statuses must not be written back as observed business data.
- Every emitted slot must explicitly label interaction as exactly `STATIC`, `HOVER`, `CONTROLLED`, or `UNKNOWN`. `CONTROLLED` requires a real, operated control that changed the view; an apparent selector or a static image is not sufficient.
- `capability_preflight` is a required step and output field even when no qualifying renderer is exposed. When unavailable, report that state and stop the render claim; do not invent a capability or silently skip preflight.

## Inputs
- analysis result or workflow synthesis;
- structured data where available;
- intended audience and decision;
- relevant sources/provenance;
- optional user preference for format/tool.

## Output contract
Return or render:
- **message**: one decision-relevant headline;
- **visual_type**: chart / diagram / interactive-component / figma-design / deck / none;
- **visual_payload**: structured data used by the renderer;
- **as_of**: date/time context when relevant;
- **provenance**: sources or canonical data references;
- **uncertainty**: what is estimated, missing or inferred;
- **fallback**: concise textual/table equivalent when rendering is unavailable.
- **capability_status**: AVAILABLE / UNAVAILABLE / UNKNOWN.
- **renderer_execution_status**: NOT_REQUIRED / NOT_ATTEMPTED / BLOCKED_NO_RENDERER / PAYLOAD_RENDERED / FAIL_RENDERER_INVOCATION.
- **client_display_status**: NOT_OBSERVABLE.

## Evidence requirements
- Every plotted factual value must come from user-provided data, canonical state, calculation or cited evidence.
- Derived values must be reproducible from the stated inputs.
- Scenario/estimate values must be labelled as such.
- Visual labels must preserve units, time period and denominator.

## Failure and uncertainty handling
- If the preferred interactive renderer is unavailable, use the next concrete renderer; a real static image remains a useful completed visual when it satisfies the request or fallback.
- Do not make an undocumented host-widget attempt when interaction capability is `UNKNOWN`. Use an exposed deterministic static renderer and state that control behavior could not be verified.
- If the user explicitly requires controls and the runtime exposes none, mark the control feature `BLOCKED_NO_RENDERER`; keep any successfully rendered static chart at `PAYLOAD_RENDERED`.
- Return a visual slot as `BLOCKED_NO_RENDERER` only when no suitable renderer for the visual itself is available. A table/text fallback remains diagnostic.
- If data are incomplete, show the gap or omit the visual element rather than fabricating it.
- Do not create a Figma/HTML/PDF/deck artifact unless the user explicitly requested that artifact class.
- If interactivity is unavailable, fall back to a static chart/table plus concise interpretation.

## Quality checks
- [ ] Visual choice matches the information structure.
- [ ] No new unsupported facts were introduced.
- [ ] Units, period, denominator and as-of context are visible where relevant.
- [ ] Sources/provenance remain recoverable.
- [ ] Visual and prose imply the same conclusion.
- [ ] The result is readable without relying on color alone.
- [ ] The visual is not decorative clutter.
- [ ] The renderer stays inside chat unless an external artifact was explicitly requested.
- [ ] A text fallback exists when the renderer is non-portable.
- [ ] Required quantitative visuals passed `capability_preflight` against an actual deterministic renderer.
- [ ] Media-generation or design tools were not misclassified as quantitative chart renderers.
- [ ] `BLOCKED_NO_RENDERER` cannot be reported as successful rendering.
- [ ] Tool success with a valid native image/chart payload is `PAYLOAD_RENDERED`, not proof of client display.
- [ ] No base64 image data or serialized visual payload leaked into user-facing text.
- [ ] Every required visual slot has an actual inline visual element, or an explicit blocked/failed state.
- [ ] Client display is always `NOT_OBSERVABLE` from the model unless explicit external evidence is supplied.
- [ ] Each slot has an explicit STATIC / HOVER / CONTROLLED / UNKNOWN classification and a completed capability preflight.
- [ ] Organization diagrams contain no unsupported hierarchy, reporting, ownership, or authority links.
- [ ] Do not emit `UI_CONFIRMED`, `UI_RENDER_UNCONFIRMED`, `VISIBLE` or `BROKEN` as model-owned facts.
- [ ] Do not describe a visual as visible/rendered "above" merely because the tool returned an image payload.

## References
- references/tool-routing.md
- references/design-system.md
