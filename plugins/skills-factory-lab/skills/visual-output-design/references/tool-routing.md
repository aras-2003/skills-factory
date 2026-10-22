# Visual tool routing

Choose the narrowest capable renderer. Tool availability varies by runtime; never claim a tool was used unless it actually ran.

## Capability preflight contract

Before satisfying a required visual slot, inspect the tools available in the current session and bind the slot to a concrete renderer capability.

A **qualifying deterministic data renderer** must:
- accept structured numeric/category/time-series data or an equivalent explicit chart specification;
- deterministically encode those supplied values into a rendered chart/visual;
- preserve labels, units and ordering without model-invented geometry;
- be invokable in the current runtime and embeddable in the intended response surface.

The following do **not** qualify as quantitative chart renderers:
- image generation or generic media generation;
- image viewing;
- Figma/FigJam diagram/design tools used as freeform drawing surfaces;
- text, markdown tables or ASCII/punctuation pseudo-charts.

Known bundled static renderer:
- MCP server: `skills-factory-runtime` (Lab/runtime deployments may expose it under another adapter name);
- tools: `render_bar_chart`, `render_line_chart`;
- these tools qualify for ordinary static quantitative visual slots only when exposed by the current runtime.
- they **do not qualify** for a slot that explicitly requires chat-native interactivity.
- a valid tool result proves renderer execution `PAYLOAD_RENDERED`; it does not prove client display. Client display is `NOT_OBSERVABLE` to the model.

Interaction classification is separate from renderer availability:

- `STATIC`: a rendered image/chart with no user-operated interaction.
- `HOVER`: documented native hover or tooltip behavior, with no data-view controls.
- `CONTROLLED`: a documented, callable selector/filter/range control that changes the displayed data view.
- `UNKNOWN`: the runtime or payload does not establish the interaction level.

A control-interactive chart is available only when the current runtime exposes a concrete, documented, callable component/API. Do not infer support from a product's general capabilities, mention of a `chart` widget, or JSON-shaped chart data. Tool enumeration alone may be supplemented by current official host documentation only if that documentation describes a callable mechanism for this session. Never invent response syntax or a mock control.

If the user specifically asks for controls but the runtime exposes only a static renderer, mark the **control feature** `BLOCKED_NO_RENDERER`; separately render and label a static chart when useful. Do not mark the entire visual blocked if a real static visual was emitted. When a native chart's hover behavior is documented but no selectors are available, classify it `HOVER`, not `CONTROLLED`.

`AVAILABLE`, `UNAVAILABLE`, or `UNKNOWN` must be recorded for the requested capability level. For unknown interaction capability, use an available concrete static renderer for the visual while reporting that the interactive capability was not established. Do not make a speculative widget attempt.

## Investment shortlist renderer choice

1. In normal Chat, use the exposed Cloud Next inline chart MCP App when the needed chart type is supported; its marks/series controls are documented above.
2. In other runtimes, use another real callable interactive renderer only when its controls and output behavior are documented in that runtime.
3. Otherwise use the bundled static `skills-factory-runtime` when exposed. Its `render_line_chart` and `render_bar_chart` tools produce static visuals, not filters or selectors.
4. If no deterministic chart renderer is callable, mark the visual slot `BLOCKED_NO_RENDERER` and give a compact table as diagnostic fallback only.

For the static fallback:
- when verified price series for at least two candidates overlap on comparable dates and use compatible adjustment definitions, plot each series indexed to 100 at the first common observation;
- label the base date, period, currency, price-adjustment/dividend basis, as-of date, and source; describe the result as indexed share-price movement, not total return unless dividends are included;
- keep KPI charts candidate-specific and units separate;
- use a line for at least three dated observations; show two observations as a paired bar/dot comparison and call it a period comparison, not a trend;
- do not smooth, interpolate, or silently omit missing periods. If common coverage is insufficient, use separate charts or state which exact slot is unavailable.

## Inline payload safety and display
- Never place data:image/...;base64,... or raw base64 in user-facing Markdown/text. Do not encode or stringify image blocks returned by a renderer.
- Preserve returned image content as an actual inline image block in the assistant response; put captions, source links, units, and as-of labels beside it.
- A static chart image is not interactive. Record its renderer class accurately and never describe it as an interactive dashboard.
- PAYLOAD_RENDERED means a native chart/image payload was produced and included in the response. It does not prove client display; keep client display NOT_OBSERVABLE.

## 1. Skills Factory Cloud Next inline interactive chart app
When the Cloud Next MCP exposes `render_bar_chart` or `render_line_chart`, use it as the shared interactive renderer for chart slots in normal Chat reports and presentation-of-results workflows. It accepts explicit structured data and returns a self-contained HTML/CSS/SVG MCP App. The app supports selecting marks and toggling line-series visibility. The renderer is an internal visual-output-design primitive coordinated by `report-composer`, not a separate skill, dashboard or report workflow. The component requests inline display; do not request fullscreen or create a parallel dashboard.

Use:
- `render_line_chart` for time-series results and `render_bar_chart` for categorical comparisons;
- one chart per analytical question;
- multiple series only when units and comparison are genuinely compatible;
- source-backed values, readable labels and explicit units;
- chart narrative/interpretation adjacent in the same chat report.

The widget appears in the host's inline app slot in the conversation flow. The host may not support inserting it at an arbitrary location inside a prose message; keep the relevant report text adjacent and do not claim otherwise. Client display still requires external UI observation.

## 2. Other native interactive chart components
Use another real callable interactive component only when its controls and output behavior are documented in the current runtime. Do not infer support from the product name, documentation for a different host, or JSON-shaped chart data.

## 3. Static native/MCP chart renderer
Use for:
- bar/ranked comparisons;
- line/time-series and normalized performance;
- pie only for a small, meaningful part-to-whole;
- scatter for numeric relationships.

Best for fast in-chat decision support. Prefer this over generating an image of a chart.

Do not use for:
- org charts;
- capability maps;
- process/decision flows;
- multi-panel dashboards requiring filters;
- arbitrary diagrams.

## 4. Figma / FigJam diagram
Use only when the user explicitly requests an editable Figma/FigJam artifact, or the calling task explicitly requires Figma output. Use a connected Figma diagram capability for:
- flowcharts;
- decision trees;
- state/sequence diagrams;
- entity-relationship diagrams;
- gantt-style plans;
- clear dependency/process/governance flows.

For org charts, operating-model maps, capability maps and other layouts that exceed the supported diagram grammar,
use an editable Figma design canvas rather than forcing the content into an unsupported Mermaid form.

## 5. Figma design
Use only when the user explicitly requests an editable Figma artifact. Use when:
- the output should be editable and executive-grade;
- a reusable visual language/design system matters;
- multiple panels, cards, grids, labels and annotations must be composed precisely;
- an org model, capability map, architecture view or one-page executive visual is a durable artifact.

Do not invoke it for a simple two-series chart that the native chart renderer can handle better.

## 6. Figma Slides / deck
Use only when the user explicitly requests a deck/presentation. Use for:
- board/executive presentations;
- multi-slide narratives;
- research readouts;
- transformation stories;
- investment committee / opportunity review packs.

A deck is a communication artifact, not the canonical analytical record.

## 7. Interactive HTML/CSS report
Use only when the user explicitly requests HTML, a downloadable file or an external interactive report. Use when the result benefits from:
- tabs or scenario switching;
- filters;
- hover/tooltips;
- linked views;
- dense multi-panel dashboards;
- reusable one-page cockpit/report;
- responsive presentation outside the chat thread.

Keep data in a separate structured payload from HTML/CSS/JS. Prefer simple, portable front-end code and avoid hidden calculations in the presentation layer.

## 7. Data/analytics tools
Use connected analytics tools for:
- SQL/aggregation;
- portfolio concentration;
- overlap/look-through;
- time-series preparation;
- statistical calculations.

Analytics tools calculate the visual payload; they are not the presentation layer and do not become canonical state.

## 8. Image generation / creative media
Use only for:
- illustrative concepts;
- moodboards;
- non-data hero imagery;
- visual metaphors when explicitly useful.

Never use generated imagery to represent exact quantitative data, organizational reporting lines, factual architecture,
or evidence-backed process state.

## Fallback order
1. native host `chart` widget for quantitative interactive charts when available;
2. another qualifying chat-native interactive structured renderer;
3. static `skills-factory-runtime` only for non-interactive slots or as diagnostic fallback;
4. for **optional** visuals: static markdown table + concise prose;
5. for **required visual-floor** slots with no qualifying renderer: `BLOCKED_NO_RENDERER` plus an optional diagnostic table/prose fallback;
6. external artifact renderer only when the user explicitly requested that artifact class.

Never create HTML/PDF/Figma/deck/file output merely because the preferred chat renderer is unavailable.

Do not fall back to punctuation-based pseudo-diagrams when a structured fallback is possible.
