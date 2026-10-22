---
name: report-composer
description: 'Compose one integrated decision report from an already-supported workflow
  result by interleaving narrative, evidence, decisions and contextually placed visual
  slots. Use when the user needs a coherent report where charts, diagrams, interactive
  components or Figma outputs appear inside the relevant sections instead of as a
  separate parallel artifact.

  '
metadata:
  owner: arkadiusz-kamrowski
  version: 0.12.1
  maturity: candidate
  risk: low
  last_reviewed: '2026-10-15'
---

# Report Composer

## Purpose
Turn a completed analysis into one coherent decision report rendered **in the chat response by default**. The report structure is primary; visuals are embedded where they improve the reader's understanding of the surrounding argument.

Do not create a second "visual report" beside the chat answer. Do not create an HTML/PDF/Figma/deck/file unless the user explicitly requests an external artifact or file format.

## Preconditions
- The underlying analysis has already been produced by the calling workflow.
- Evidence, uncertainty and canonical state boundaries are already known.
- The composer may reorganize presentation, but must not silently change analytical conclusions.

## Procedure
1. Identify the audience, decision and minimum report depth. For a narrow factual or explanatory request, answer directly at the requested depth; do not expand it into an integrated investment report, dashboard, candidate ranking, or additional analysis unless the user asks or a required evidence gate needs it.
2. Apply `references/report-quality-standard.md` and `references/report-state-and-evidence-contract.md` as mandatory contracts.
3. Build the evidence ledger before presentation:
   - classify each decision-relevant claim as CANONICAL / USER_PROVIDED / EXTERNAL_VERIFIED / DERIVED / UNKNOWN;
   - require reproducible inputs for every DERIVED claim;
   - run the causal-attribution gate before stating why something changed.
4. Run `capability_preflight` before finalising each visual-floor slot:
   - inspect tools and host-native components actually documented and exposed by this runtime;
   - bind the slot to a concrete, callable renderer; never infer a widget API from a product name or create response syntax that is not documented;
   - distinguish deterministic static image/chart renderers from components with documented hover or user-operated controls;
   - route each visual slot through the medium-specific renderer selected by `visual-output-design` (numeric chart, structural diagram, illustration/motion, or interactive UI). Use specialized generation/design tools where they improve the requested output quality, without letting them invent evidence or duplicate the report;
   - do not count `image_gen`, image viewers, generic media generation, or Figma diagram/design tools as quantitative chart renderers;
   - record renderer availability as `AVAILABLE`, `UNAVAILABLE`, or `UNKNOWN`;
   - when interactive capability is unknown or absent, use a real static renderer for the visual and explicitly state that interaction is unavailable; do not simulate an interactive-renderer attempt.
   - in normal Chat, recognize the Skills Factory Cloud Next interactive chart MCP tools as concrete inline renderers when exposed. They are implementation primitives for this composition layer, not a separate user-facing skill or report. Keep chart content in the report flow; do not launch a parallel dashboard or fullscreen view.
5. Select a report profile from `references/report-profiles.md` or derive a minimal equivalent.
6. Build a semantic report model containing ordered sections:
   - section purpose;
   - narrative block;
   - evidence block;
   - decision/implication block;
   - optional inline visual slots;
   - requested target format and any target-specific interaction/editability requirements;
   - section-level provenance and uncertainty.
7. Decide visual placement by reading flow, not by asset type:
   - put the visual immediately after the claim/context it helps explain;
   - put interpretation immediately after the visual;
   - avoid collecting unrelated visuals into a separate appendix/dashboard unless the user explicitly asks.
8. For each visual slot, call `visual-output-design` with:
   - the local section question;
   - only the relevant supported data;
   - required renderer capabilities;
   - as-of context and provenance.
9. For required chartable visuals in normal Chat, invoke the exposed Cloud Next `render_bar_chart` or `render_line_chart` through `visual-output-design` using verified chartable data. The renderer produces an inline interactive app (mark selection; line-series toggles). Place the report narrative and interpretation adjacent to the chart in the same conversation flow. Use another documented inline renderer when Cloud Next is unavailable; otherwise render a static image. If the user explicitly requested interaction and none is available, mark the interaction feature blocked while still including any useful static visual.
10. For each explicitly requested external format, keep one source-backed `ExhibitSpec` but route production and QA through that format's owner. Record `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`, or `UNVERIFIED` separately for each artifact, with an actual artifact reference and format-specific review evidence. A successful chart-renderer call or generated download link is not artifact QA. Until an artifact has been opened/rendered and reviewed through its format-specific QA path, describe it as generated but `UNVERIFIED`, not ready or complete. Record interaction/editability loss per target.
11. Choose output target from actual renderer execution:
   - **chat-native report** when required visual slots have a qualifying renderer and a valid payload was produced;
   - **chat-blocked** when no qualifying renderer exists or invocation fails;
   - **external artifact** only when the user explicitly asks for one.
   Client-display success is never inferred from a tool receipt alone. A valid payload is `PAYLOAD_RENDERED`; client display remains `NOT_OBSERVABLE` unless a separate browser/UI test or user observation confirms it. Record that external evidence in the runtime evaluation rather than rewriting the tool receipt.
12. A blocked report may still include a compact table/matrix so the user can inspect the data, but that fallback is diagnostic only: it does **not** satisfy the required visual slot and must carry `BLOCKED_NO_RENDERER` (or `FAIL_RENDERER_INVOCATION` when a qualifying renderer was discovered but failed).
13. Preserve progressive disclosure:
   - lead with the decision and minimum evidence;
   - keep detail near the section it supports;
   - move exhaustive evidence tables or appendices later.
14. Keep receipts, source notes and material limitations in the same report, not in a disconnected parallel artifact.
15. Run the contradiction check from the state/evidence contract before final output.
16. Never silently convert a required visual-floor slot into successful renderer execution. If no qualifying renderer exists or invocation fails, surface that execution state explicitly. Do not silently move the report into an HTML/PDF/Figma/deck artifact. Create an external artifact only when the user explicitly requested one.

## Visual coverage and dashboard contract

- For each required slot, track slot_id, renderer class, execution state, whether a native visual element was included inline, and its adjacent provenance/caption.
- In a detailed opportunity report, create a compact in-chat shortlist dashboard after the executive summary/radar. Show only decision-useful fields such as candidate, status, key change, valuation/expectation risk, portfolio fit, and next gate. Use a readable table or cards; do not call it interactive unless it is.
- Place candidate-specific price/KPI visuals inside the corresponding candidate section. Share a chart only when the compared series use compatible definitions, units, and periods.
- Before finalising, compare required slots with actual inline visual elements. A slot is not complete just because data were gathered, a tool was detected, a tool call was attempted, or a payload was mentioned in prose.
- Never expose data:image/...;base64,..., raw base64, serialized image blocks, or chart JSON in user-facing text/Markdown. Preserve returned media as an actual inline image or native chart element. If the runtime cannot emit it, state the slot's blocked/failed status and retain a compact table fallback.
- Prefer the best usable in-chat visual available. State whether it is static, hover-interactive, or control-interactive only when that behavior is documented or observed; label static images as static.

### Investment shortlist visual layout

- Put the compact candidate dashboard near the top, then keep each KPI visual beside its candidate analysis.
- When at least two candidates have verified price series with a common window and compatible adjustment definitions, create one shared price-comparison line chart indexed to 100 at the first common date. State the window, currency basis, price adjustment, dividend treatment and provenance. Treat it as a share-price comparison, not total return, unless dividends are included.
- If price series do not share a comparable window or adjustment basis, do not combine them. Use separate small charts or a diagnostic table and identify the missing/unequal coverage.
- Use candidate-specific KPI charts. Never plot different KPIs or units on a shared axis.
- Use a line only for a genuine chronological sequence. With two observations, use a paired bar or dot comparison and call it a two-period comparison, not a trend. Do not interpolate missing quarters.
- For static renderers, keep the chart visually clean: short title, period labels, units, readable scale and a brief interpretation. Prefer a shared indexed-price visual plus one compact KPI visual per detailed candidate over multiple repetitive chart variants.
- Do not promise dynamic controls as the improvement path when the runtime exposes only static rendering. List unavailable selectors/filters plainly; never make a static image look like an interactive widget.

## Hard stop: no phantom visuals

A required visual is not complete because the report describes it, refers to “the chart”, names a chart type, or says an image is static. It is complete only when the current run has returned an actual chart/image payload and that payload is included as a native visual element in the response.

Before drafting any caption or sentence that says what a chart “shows”:
1. Call the concrete renderer for that slot with the verified values and source context.
2. Confirm that the tool returned an image/chart payload, not only a URL, text, or JSON specification.
3. Include the returned payload as an actual inline image/chart beside the relevant analysis.
4. Confirm the final response contains the visual element itself. If you cannot include it, remove all wording that implies the visual exists and mark the slot `FAIL_RENDERER_INVOCATION` or `BLOCKED_NO_RENDERER`, with a compact diagnostic table.

Do not claim “three charts”, “static charts”, or similar visual inventory unless each counted chart is actually included inline. A chart tool call with no returned image, and an image returned only as encoded text, both fail this gate. Keep payload data out of user-facing text.

## Inline visual slot contract
Each slot must define:
- **slot_id**
- **purpose**
- **placement_after**
- **renderer_class**: native-chart / static-image / native-widget / table / structured-chat / interactive-html / figma-diagram / figma-design / deck / none
- **payload**
- **interaction_level**: STATIC / HOVER / CONTROLLED / UNKNOWN
- **interaction**: e.g. none, 3m/6m/12m, scenario toggle, filter
- **as_of**
- **provenance**
- **uncertainty**
- **fallback**
- **capability_status**: AVAILABLE / UNAVAILABLE / UNKNOWN
- **renderer_execution_status**: NOT_REQUIRED / NOT_ATTEMPTED / BLOCKED_NO_RENDERER / PAYLOAD_RENDERED / FAIL_RENDERER_INVOCATION
- **client_display_status**: NOT_OBSERVABLE
- **inline_visual_included**: YES / NO

## Decision rules
- The report is the product; visuals are evidence-bearing components inside it.
- Apply the default quality standard without requiring the user to spell out formatting, section limits, chart preferences or receipt compactness in the prompt.
- Prefer concise executive hierarchy: 3–5 opening points, a small number of detailed entities, selective visuals and a 3–5 item decision queue unless the task genuinely requires more.
- Apply the visual-floor rule from the quality standard: material chartable data create a required visual slot. If a qualifying renderer is absent, the report is blocked rather than silently accepted as text-only.
- Do not make a dashboard merely because several metrics exist.
- Do not repeat the same content in prose and a separate visual artifact unless repetition materially aids the decision.
- Use interactive controls only when the alternative views answer a real decision question.
- For company price/performance context, a shared indexed comparison is useful when comparable, verified time-series data exist; do not imply range switching unless real controls are available.
- A visual may summarize but must not strengthen, rank or score beyond the underlying analysis.
- Prefer native chat renderers for normal report delivery. Use Figma/HTML/PDF/deck renderers only when the user explicitly requests an editable or external artifact/file.
- Canonical READ/WRITE receipts remain explicit and auditable.

## Output contract
Return one semantic report with:
- **report_title**
- **decision_headline**
- **analysis_state**: COMPLETE / PARTIAL_EVIDENCE / BLOCKED_ANALYSIS
- **target**: chat-native / chat-blocked / external-artifact-requested
- **sections[]**
  - heading
  - narrative
  - evidence
  - visual_slots[]
  - interpretation
  - decision_or_next_step
  - provenance
  - uncertainty
- **runtime_diagnostic** only when requested or useful:
  - capability_status
  - renderer_execution_status
  - client_display_status: NOT_OBSERVABLE
- **format_statuses[]** for explicitly requested external formats only:
  - format
  - artifact_reference
  - creation_status
  - qa_status: NOT_RUN / PASS / FAIL / BLOCKED / UNVERIFIED
  - qa_evidence
  - interaction_or_editability_losses
- **receipts**
- **limitations**
- **appendix** only when needed

Do not emit `report_status: PASS` for ordinary report composition. Runtime visual PASS/FAIL belongs to an external evaluator with client evidence.

## Evidence requirements
- Every factual visual slot inherits the evidence standard of the calling workflow.
- Values must retain units, periods and denominators.
- Derived analytics must remain identifiable as derived.
- Missing evidence stays visibly missing.

## Failure and uncertainty handling
- Track renderer availability separately from interaction level. If only interactive capability is unknown or unavailable, render a useful static visual when possible and mark the requested controls blocked/unknown; reserve `BLOCKED_NO_RENDERER` for the missing visual renderer itself.
- If renderer invocation fails, use `FAIL_RENDERER_INVOCATION`.
- If the renderer returns a valid payload, use `PAYLOAD_RENDERED`; do not infer whether the client displayed it.
- If decision-critical evidence is missing but useful analysis remains possible, use `analysis_state: PARTIAL_EVIDENCE`.
- If the core requested analysis cannot be supported, use `analysis_state: BLOCKED_ANALYSIS`.
- Never generate an external file merely as a fallback.

## Quality checks
- [ ] The output is one coherent report in chat by default, not text plus a duplicate dashboard or unsolicited file.
- [ ] Visuals appear where the surrounding narrative needs them.
- [ ] Every required slot is covered by an actual inline visual element or is explicitly blocked/failed.
- [ ] A discovery report includes a compact in-chat shortlist dashboard when several candidates are compared.
- [ ] No raw base64/data URI or serialized chart payload appears in user-facing text.
- [ ] Every visual has local interpretation and provenance.
- [ ] No visual exists only for decoration.
- [ ] The same conclusion is preserved across text and visual rendering.
- [ ] Interaction level (STATIC / HOVER / CONTROLLED / UNKNOWN) matches the emitted component and observed/documented behavior.
- [ ] Interaction controls correspond to real supported alternate views.
- [ ] No external artifact/file was created unless explicitly requested.
- [ ] Each explicitly requested external artifact has its own creation status and format-specific QA evidence; unreviewed artifacts remain UNVERIFIED.
- [ ] The report remains readable on narrow/mobile layouts.
- [ ] Receipts and limitations remain visible.
- [ ] `capability_preflight` was run for every required visual-floor slot.
- [ ] Text/table fallback never converts `BLOCKED_NO_RENDERER` into renderer success.
- [ ] Renderer success is reported only as `PAYLOAD_RENDERED`; client display remains `NOT_OBSERVABLE`.
- [ ] No `UI_CONFIRMED`, `UI_RENDER_UNCONFIRMED`, `PASS_WITH_LIMITATIONS` or invented status appears.
- [ ] Every derived metric is reproducible from identified inputs.
- [ ] User-provided but non-reproducible metrics remain labelled USER_PROVIDED.
- [ ] Causal claims pass the causal-attribution gate.
- [ ] Limitations do not contradict earlier claims.

## References
- references/report-quality-standard.md
- references/report-state-and-evidence-contract.md
- references/report-profiles.md
- references/composition-rules.md
