import { z } from "zod";
import { LAB_RELEASE, DRAFT_RELEASE, RUNTIME_RELEASE, SKILL_CATALOG } from "./skill-catalog";
import { CANONICAL_SOURCE_REVISION, ROUTING_CONTRACT_BLOB_SHA } from "./canonical-provenance";
import { CHART_UI_URI } from "./chart-ui";

export const SOURCE = {
  repository: "https://github.com/aras-2003/skills-factory",
  github_main_revision: CANONICAL_SOURCE_REVISION,
  routing_contract: "workflows/investment-os-review/WORKFLOW.md",
  routing_contract_blob_sha: ROUTING_CONTRACT_BLOB_SHA,
  channel: "private Cloud Next Site sourced from Skills Factory",
  synchronization: "generated from the complete Skills Factory Lab artifact built from this canonical repository revision; evaluator fixtures excluded",
  lab_release: LAB_RELEASE,
  draft_extension: DRAFT_RELEASE,
  runtime_release: RUNTIME_RELEASE,
};
export const SKILLS = SKILL_CATALOG.map((skill) => skill.name);
const text = z.string().trim().min(1).max(160);
const label = z.string().trim().min(1).max(80);
const number = z.number().finite().min(-1e12).max(1e12);
export const schemas = {
  runtime_info: z.object({}).strict(),
  list_skills: z.object({}).strict(),
  load_skill: z.object({ skill_name: z.string().trim().min(1).max(160) }).strict(),
  route_investment_request: z.object({ user_request: z.string().trim().min(1).max(8000) }).strict(),
  render_bar_chart: z.object({ labels: z.array(label).min(1).max(60), values: z.array(number).min(1).max(60), expected_points: z.number().int().positive(), title: text, unit: z.string().trim().max(30), horizontal: z.boolean() }).strict().superRefine((v, ctx) => {
    if (v.labels.length !== v.values.length) ctx.addIssue({ code: "custom", message: "labels and values must have equal lengths" });
    if (v.labels.length !== v.expected_points || v.values.length !== v.expected_points) ctx.addIssue({ code: "custom", message: "received chart data length does not match expected_points; refusing partial render" });
  }),
  render_line_chart: z.object({ x_labels: z.array(label).min(2).max(100), series_names: z.array(label).min(1).max(8), series_values: z.array(z.array(number).min(2).max(100)).min(1).max(8), expected_x_labels: z.number().int().positive(), expected_series: z.number().int().positive(), expected_points_per_series: z.number().int().positive(), title: text, unit: z.string().trim().max(30) }).strict().superRefine((v, ctx) => {
    if (v.series_names.length !== v.series_values.length) ctx.addIssue({ code: "custom", message: "series_names and series_values must have equal lengths" });
    if (v.series_values.some(s => s.length !== v.x_labels.length)) ctx.addIssue({ code: "custom", message: "every series must match x_labels length; missing values are not inferred" });
    if (v.x_labels.length !== v.expected_x_labels || v.series_names.length !== v.expected_series || v.series_values.length !== v.expected_series || v.series_values.some(s => s.length !== v.expected_points_per_series)) ctx.addIssue({ code: "custom", message: "received chart data shape does not match expected counts; refusing partial render" });
  }),
};
// Some connected clients retain an older tool schema and truncate arrays before
// forwarding calls. Required expected_* counts make this detectable server-side:
// missing counts (stale clients) and shortened arrays fail closed before rendering.
const str = { type: "string", minLength: 1, description: "Nonempty title; server rejects titles longer than 160 characters." };
const labelsSchema = (min: number, max: number) => ({ type: "array", minItems: min, description: `Server rejects more than ${max} labels; no truncation.`, items: { type: "string", minLength: 1, description: "Server rejects labels longer than 80 characters." } });
const numbersSchema = (min: number, max: number) => ({ type: "array", minItems: min, description: `Server rejects more than ${max} values; no truncation.`, items: { type: "number", minimum: -1e12, maximum: 1e12 } });
const expectedCount = (description: string) => ({ type: "integer", minimum: 1, description });
const unitSchema = { type: "string", description: "Server rejects units longer than 30 characters." };
const annotations = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false };
export const TOOLS = [
  { name: "runtime_info", description: "Return this Site Worker's deployment attestation and the embedded Skills Factory Lab release. Missing platform identity is reported as unattested. Read-only; does not execute a skill.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations },
  { name: "list_skills", description: "List every skill and workflow in the source-bound Lab artifact irrespective of maturity, including kind, version, maturity and content digests. Read-only; does not execute a skill.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations },
  { name: "load_skill", description: "Load the exact packaged SKILL.md instructions and allow-listed supporting references for one Lab skill or workflow by name, irrespective of maturity. Eval fixtures are excluded. The host model executes the loaded instructions; this MCP does not claim to perform model reasoning itself.", inputSchema: { type: "object", properties: { skill_name: { type: "string", minLength: 1, maxLength: 160 } }, required: ["skill_name"], additionalProperties: false }, annotations },
  { name: "route_investment_request", description: "Call before substantive investment analysis to route a Polish or English request through Investment OS. Preserve the returned routing_receipt, then call load_skill for the exact child_workflow and execute its instructions. Routing alone does not execute a workflow, read portfolio data, trade or provide recommendations. Ambiguous requests return clarification_required: load the front door, then ask the clarification question before analysis; do not silently substitute another specialist.", inputSchema: { type: "object", properties: { user_request: { type: "string", minLength: 1, maxLength: 8000 } }, required: ["user_request"], additionalProperties: false }, annotations },
  { name: "render_bar_chart", description: "Internal report visual renderer: use from report-composer/visual-output-design to embed an interactive chart in a chat-native report or presentation of results; do not create a separate dashboard. Direct invocation is for an explicit chart-only request. Renders an inline interactive HTML/SVG bar chart exclusively from explicitly supplied finite JSON numbers, including zero and negatives. labels and values must match. Supply expected_points equal to both array lengths; the server rejects missing or mismatched counts so stale connectors cannot silently truncate data. Maximum 60 points, 80 characters per label, 160 per title and 30 per unit. No fetching, inference, totals, advice or persistence. MCP Apps hosts show a clickable chart; structuredContent preserves the exact SVG and data for other clients.", inputSchema: { type: "object", properties: { labels: labelsSchema(1, 60), values: numbersSchema(1, 60), expected_points: expectedCount("Required: original number of labels and values before connector transport; server rejects a mismatch."), title: str, unit: unitSchema, horizontal: { type: "boolean" } }, required: ["labels", "values", "expected_points", "title", "unit", "horizontal"], additionalProperties: false }, annotations, _meta: { ui: { resourceUri: CHART_UI_URI }, "openai/outputTemplate": CHART_UI_URI, "openai/toolInvocation/invoking": "Rendering interactive chart", "openai/toolInvocation/invoked": "Interactive chart ready" } },
  { name: "render_line_chart", description: "Internal report visual renderer: use from report-composer/visual-output-design to embed an interactive chart in a chat-native report or presentation of results; do not create a separate dashboard. Direct invocation is for an explicit chart-only request. Renders an inline interactive HTML/SVG line chart exclusively from supplied finite JSON numbers. series_values is series-major: one numeric array for each series_name, each matching x_labels. Supply expected_x_labels, expected_series and expected_points_per_series from the original input; mismatches fail closed so stale connectors cannot silently truncate data. Maximum 100 points and 8 series; labels 80 characters, title 160 and unit 30. x_labels are categorical, equally spaced, with no date interpretation. No missing-value inference, fetching, advice or persistence. MCP Apps hosts show a clickable chart with toggleable series; structuredContent preserves the exact SVG and data for other clients.", inputSchema: { type: "object", properties: { x_labels: labelsSchema(2, 100), series_names: labelsSchema(1, 8), series_values: { type: "array", minItems: 1, description: "Server rejects more than 8 series or 100 values per series; no truncation.", items: numbersSchema(2, 100) }, expected_x_labels: expectedCount("Required: original number of x_labels before connector transport."), expected_series: expectedCount("Required: original number of series before connector transport."), expected_points_per_series: expectedCount("Required: original number of values in every series before connector transport."), title: str, unit: unitSchema }, required: ["x_labels", "series_names", "series_values", "expected_x_labels", "expected_series", "expected_points_per_series", "title", "unit"], additionalProperties: false }, annotations, _meta: { ui: { resourceUri: CHART_UI_URI }, "openai/outputTemplate": CHART_UI_URI, "openai/toolInvocation/invoking": "Rendering interactive chart", "openai/toolInvocation/invoked": "Interactive chart ready" } },
];
export type SiteVersionMetadata = {
  id?: string | null;
  tag?: string | null;
  timestamp?: string | number | null;
  source?: "cloudflare_version_metadata" | "site_environment";
};
let toolSchemaDigestPromise: Promise<string> | undefined;
async function getToolSchemaDigest() {
  toolSchemaDigestPromise ??= (async () => {
    const schema = TOOLS.map(({ name, inputSchema }) => ({ name, inputSchema }));
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(schema)));
    return `sha256:${Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
  })();
  return toolSchemaDigestPromise;
}
const safeSkillName = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
export async function runtimeInfo(metadata?: SiteVersionMetadata) {
  const siteTag = typeof metadata?.tag === "string" && /^[a-f0-9]{40}$/i.test(metadata.tag) ? metadata.tag : null;
  let deployedAt: string | null = null;
  if (metadata?.timestamp != null) {
    const parsed = new Date(metadata.timestamp);
    if (Number.isFinite(parsed.getTime())) deployedAt = parsed.toISOString();
  }
  const schemaDigest = await getToolSchemaDigest();
  const attested = typeof metadata?.id === "string" && metadata.id.length > 0 && siteTag !== null && deployedAt !== null;
  return {
    ...SOURCE,
    release_id: metadata?.id || "unattested",
    source_revision: siteTag || "unattested",
    canonical_source_revision: CANONICAL_SOURCE_REVISION,
    software_release: { version: LAB_RELEASE.version, release_id: LAB_RELEASE.release_id, source_revision: LAB_RELEASE.source_revision },
    routing_contract_blob_sha: ROUTING_CONTRACT_BLOB_SHA,
    channel: "site",
    capability_contract_version: "site-mcp-v2",
    tool_schema_digest: schemaDigest,
    deployed_at: deployedAt || "unattested",
    attestation_status: attested ? "verified" : "unattested",
    identity_source: attested ? (metadata?.source || "cloudflare_version_metadata") : "unattested",
    capabilities: TOOLS.map((tool) => tool.name),
    execution_mode: "host_model_executes_loaded_instructions",
  };
}
export function listSkills() {
  return { evidence_boundary: { scope: "Packaged capabilities only; not historical backlog or GitHub Project membership/acceptance.", reconciliation: "For a source/backlog count mismatch, request the exact source revision and both ID sets. Report only verified set differences; counts alone cannot identify the missing ID. Keep source mapping, live Project fields/dependencies and runtime acceptance separate.", unverified_revision: "If a required source revision is unavailable, mark that comparison BLOCKED_SOURCE_REVISION and ask for it; never guess the authoritative version." }, ...RUNTIME_RELEASE, lab_release: LAB_RELEASE, draft_extension: DRAFT_RELEASE, skills: SKILL_CATALOG.map((skill) => { const { instructions, reference_files, ...metadata } = skill; void instructions; void reference_files; return metadata; }) };
}
export function loadSkill(skillName: string) {
  if (!safeSkillName.test(skillName)) throw new Error("Invalid skill name");
  const skill = SKILL_CATALOG.find((item) => item.name === skillName);
  if (!skill) throw new Error("Unknown skill");
  return { ...skill, source_revision: LAB_RELEASE.source_revision, execution_mode: "host_model_executes_loaded_instructions" };
}
const routes = ["investment-portfolio-observation", "investment-portfolio-review", "investment-security-review", "investment-opportunity-hunter", "investment-theme-discovery", "investment-attention-review", "investment-policy-design", "historical-decision-replay", "technical-structure"] as const;
export function routeInvestment(userRequest: string) {
  const editingOnly = /^(?:fix|correct|proofread|edit)\s+(?:(?:only|just)\s+)?(?:the\s+)?(?:punctuation|grammar|spelling)\b/i.test(userRequest.trim());
  const s = userRequest.normalize("NFD").toLowerCase().replace(/[\u0300-\u036f]/g, "").replace(/ł/g, "l")
    .replace(/\b(?:do not|don't|not|without|nie)\b[^.!?;,\n]*/g, "");
  const explicit = routes.filter(r => s.includes(r));
  const explicitReplayIntent = /historical decision|decision replay|replay.*(decision|portfolio|rule)|walk.forward|out.of.sample|as.of snapshot|decision date|rebuild.{0,40}(thesis|portfolio|exposure)|odtworz.{0,30}(decyz|portfel|tez)/.test(s);
  const replay = explicitReplayIntent || /published.{0,30}after.{0,30}decision|historical.*(portfolio|thesis|holding)|history.*(portfolio|exposure)|historyczn.{0,30}(decyz|portfel|tez)/.test(s);
  const technicalStructure = /technical structure|dow theory|ops\s*[/＆&]\s*opd|ops\s+opd|adjusted ohlcv|price structure|swing high|swing low|trend invalidation|pivot confirmation|struktura cen|potwierdzon.{0,30}swing|zanegowan.{0,30}trendu/.test(s);
  const systemicRisk = /systemic|cross.asset|credit spread|liquidity signal|market breadth|risk.off|ryzyko systemowe|sygnal.{0,20}plynnosc/.test(s) && /risk|signal|indicator|exposure|liquidity|spread|ryzyk|sygnal|plynnosc/.test(s);
  const portfolio = /portfel|portfolio|holdings|pozycj|positions|allocat|alokac|udzial|weights/.test(s);
  const risk = /ryzyk|risk|koncentrac|concentrat|dywers|diversif|overlap|naklad|rebalans|rebalanc|restruktur|restructur|strukture|structure/.test(s);
  const policy = /polityk|policy|zasady|rules|limit|target bands|sizing constraints/.test(s);
  const observation = /zmien|zmian|chang(?:e|es|ed|ing)|happening|dzieje|observ|obserw|watch|monitor|drift|dryf/.test(s);
  const event = (/give attention|attention next|next research|research next|attention review/.test(s) && /(?:\b(?:thesis|theses)\b|\btez(?:a|y|e|ę|ą|ie)?\b|holding|portfel|portfolio|watchlist)/.test(s)) || /news|wiadomosc|wydarzen|event|informacj|wynik|earnings/.test(s) && /(?:wplyw|impact|matter|znaczen|\b(?:thesis|theses)\b|\btez(?:a|y|e|ę|ą|ie)?\b|holdings|portfel|zmienia|watchlist)/.test(s);
  const opportunity = /watchlist screen|screen my watchlist|screen watchlist|preview the screen|preview-only screen|screen these candidates|okazj|opportunit|kandydat|candidates|research next|badac dalej|szukaj spolek|znajdz spolk|find.*(stocks|securities)/.test(s);
  const explicitCandidateDiscovery = /(?:find|scan|discover|screen|szukaj|znajd|znalez|selekcj).{0,100}(?:stocks|securities|spolk|kandydat|candidates)/.test(s);
  const theme = /temat.*inwest|investment theme|trend|value chain|lancuch wartosc|beneficjen|second.order/.test(s);
  const nonTickers = new Set(["AI", "ETF", "ETFS", "USD", "PLN", "EUR", "CEO", "CIO", "CTO", "EPS", "FCF", "DCF", "ROIC", "TAM", "CAGR"]);
  const tickerCount = new Set((userRequest.match(/\b[A-Z]{2,5}\b/g) || []).filter(token => !nonTickers.has(token))).size;
  const thesis = /\b(?:thesis|theses)\b|\btez(?:a|y|e|ę|ą|ie)?\b/;
  const security = /spolk|stock|security|akcj|etf|wycen|valuation|underwrit|ticker/.test(s) || thesis.test(s) || /issuer|company case/.test(s) || (tickerCount === 1 && /review|ocen|analiz|kup|buy|sell|sprzed|investment|add|increase/.test(s));
  const singleSecurityIntent = security && (thesis.test(s) || /underwrit|valuation|wycen|review.{0,24}(stock|security|ticker)|analy[sz].{0,24}(stock|security|ticker)|assess.{0,24}(stock|security|ticker)|(ocen|analiz).{0,24}(spolke|akcje|instrument|papier)|stock review|security review|good investment|fit.*portfolio|portfolio fit|position|sizing|size|\badd(?:ed|ing)?\b|\bincrease(?:d|s|ing)?\b|\breduce(?:d|s|ing)?\b|\btrim(?:med|s|ming)?\b|\bbuy\b|\bsell\b|kup|dodaj|zwieksz|zmniejsz|sprzed|pozycj/.test(s));
  const aggregatePortfolioReview = portfolio && risk && !singleSecurityIntent;
  let candidates: string[] = [], reason = "No unambiguous decision object matched.";
  if (explicit.length) { candidates = [...explicit]; reason = "Explicit workflow names in the request."; }
  else if (systemicRisk && !explicitReplayIntent && (!portfolio || /issuer exposure|cross.asset/.test(s))) { candidates = [routes[0]]; reason = "The decision object is systemic or cross-asset risk observation; historical vintage and missing portfolio evidence remain explicit."; }
  else if (replay) { candidates = [routes[7]]; reason = "The request reconstructs or evaluates a historical decision with as-of or out-of-sample constraints."; }
  else if (technicalStructure) { candidates = [routes[8]]; reason = "The request evaluates price pivots, trend structure or invalidation levels."; }
  else if (policy && /defini|ustal|zaprojekt|design|define|create|regul|zasad|limits|limity/.test(s)) { candidates = [routes[6]]; reason = "The decision object is investment rules or risk limits."; }
  else if (event) { candidates = [routes[5]]; reason = "New information is being assessed against holdings or theses."; }
  else if (portfolio && observation && !singleSecurityIntent) { candidates = [routes[0]]; reason = "Observation of changes or monitoring of existing holdings."; }
  else if (aggregatePortfolioReview) { candidates = [routes[1]]; reason = "Portfolio holdings or structure with a risk, concentration or allocation review."; }
  else if (theme && !explicitCandidateDiscovery) { candidates = [routes[4]]; reason = "Thematic or value-chain research is the primary decision object; beneficiary opportunities are part of that research."; }
  else if (opportunity) { candidates = [routes[3]]; reason = "Discovery of new research candidates; incidental or excluded portfolio mentions do not change the decision object."; }
  else if (singleSecurityIntent) { candidates = [routes[2]]; reason = "A named security is the decision object, including its thesis, valuation, portfolio fit or sizing."; }
  else if (portfolio) { candidates = [routes[1]]; reason = "A portfolio-level review is the decision object."; }
  else if (theme) { candidates = [routes[4]]; reason = "Thematic or value-chain research."; }
  else if (policy) { candidates = [routes[6]]; reason = "Investment policy or limits are the decision object."; }
  const investmentContext = explicit.length > 0 || replay || technicalStructure || systemicRisk || singleSecurityIntent || /investment|investing|portfolio|stock|security|securities|etf|fund|holdings|watchlist|inwestyc|portfel|spol|akcj|share|thesis|gross margin|marza brutto|research candidates/.test(s) || opportunity || theme || policy;
  const unrelatedGovernance = /security\.md|codeowners|report os.*production.ready/.test(s);
  const applicable = !editingOnly && !unrelatedGovernance && investmentContext;
  if (!applicable) { candidates = []; reason = editingOnly ? "request is limited to a non-investment editing task" : "no investment decision object was identified"; }
  const specific = candidates.length === 1;
  const route = !applicable ? "not_applicable" : specific ? candidates[0].replace("investment-", "") : "unknown";
  const child = specific ? candidates[0] : "investment-os-review";
  const needsClarification = applicable && !specific;
  return { route, child_workflow: child, ...(needsClarification ? { next_action: "load_front_door_then_clarify" } : {}), routing_receipt: `ROUTE=${route}; CHILD=${child}; NEXT_ACTION=${needsClarification ? "load_front_door_then_clarify" : `load_skill(${child})`}`, status: !applicable ? "not_applicable" : specific ? "routed" : "clarification_required", candidates, reason, method: "deterministic bilingual rules; no semantic model", clarification: !applicable || specific ? null : "Czy chodzi o obserwację portfela, jego ryzyko, konkretny instrument, nowe okazje, temat, news czy zasady inwestowania?", recommendation: null, workflow_executed: false, execution_state: "routed_only", workflow_execution_state: "not_executed", execution_state_reason: "router selected a workflow but did not execute it", outcome: null, is_investment_request: applicable, must_invoke_child_workflow: applicable, response_policy: needsClarification ? "load_front_door_then_clarify_before_analysis" : applicable ? "load_child_workflow_then_follow" : "not_applicable", source: SOURCE };
}
const escape = (s: string) => s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" }[c]!));
const short = (s: string, max = 22) => escape(s.length > max ? s.slice(0, max - 1) + "…" : s);
const format = (n: number) => new Intl.NumberFormat("en", { maximumSignificantDigits: 5, notation: Math.abs(n) >= 1e6 || (n !== 0 && Math.abs(n) < .001) ? "scientific" : "standard" }).format(n);
const colors = ["#2374e8", "#c45516", "#087f70", "#8b4ccd", "#bf335d", "#506579", "#847512", "#147ca1"];
function frame(title: string, unit: string, w: number, h: number, description: string, body: string) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-labelledby="chart-title chart-desc"><title id="chart-title">${escape(title)}</title><desc id="chart-desc">${escape(description)} Unit: ${escape(unit || "none")}.</desc><rect width="100%" height="100%" fill="#ffffff"/><g font-family="Arial, sans-serif" font-size="16" fill="#14273e"><text x="28" y="34" font-size="20" font-weight="700">${short(title, 70)}</text><text x="28" y="60" fill="#506579">${escape(unit)}</text>${body}</g></svg>`;
}
function domain(values: number[]) {
  const min = Math.min(0, ...values), max = Math.max(0, ...values);
  return min === max ? [0, 1] : [min, max];
}
function chartResult(kind: string, title: string, svg: string, data: unknown) {
  return { kind, title, svg, data, mime_type: "image/svg+xml", render_status: "PAYLOAD_RENDERED", client_display: "NOT_OBSERVABLE", provenance: "explicit caller data; no retrieval or inference" };
}
type BarChartData = { labels: string[]; values: number[]; title: string; unit: string; horizontal: boolean };
type LineChartData = { x_labels: string[]; series_names: string[]; series_values: number[][]; title: string; unit: string };
export function barChart(a: BarChartData) {
  const [min, max] = domain(a.values), width = a.horizontal ? 960 : Math.max(960, a.labels.length * 80 + 140), height = a.horizontal ? Math.max(300, a.labels.length * 38 + 120) : 540;
  let body = "";
  if (a.horizontal) {
    const x = (v: number) => 225 + (v - min) / (max - min) * 555, zero = x(0);
    for (let tick = 0; tick <= 4; tick++) { const v = min + (max - min) * tick / 4, at = x(v); body += `<path d="M${at} 80V${height - 45}" stroke="#e1e8f0"/><text x="${at}" y="${height - 18}" text-anchor="middle">${format(v)}</text>`; }
    body += `<path d="M${zero} 80V${height - 45}" stroke="#506579"/>`;
    a.values.forEach((v, i) => { const y = 86 + i * 38; body += `<text x="210" y="${y + 20}" text-anchor="end"><title>${escape(a.labels[i])}</title>${short(a.labels[i])}</text><rect x="${Math.min(zero, x(v))}" y="${y}" width="${Math.abs(x(v) - zero)}" height="27" rx="3" fill="${colors[0]}"><title>${escape(a.labels[i])}: ${v} ${escape(a.unit)}</title></rect><text x="920" y="${y + 20}" text-anchor="end" font-size="14">${format(v)}</text>`; });
  } else {
    const y = (v: number) => 420 - (v - min) / (max - min) * 320, zero = y(0), step = (width - 140) / a.labels.length;
    for (let tick = 0; tick <= 4; tick++) { const v = min + (max - min) * tick / 4, at = y(v); body += `<path d="M90 ${at}H${width - 25}" stroke="#e1e8f0"/><text x="82" y="${at + 5}" text-anchor="end" font-size="14">${format(v)}</text>`; }
    body += `<path d="M90 ${zero}H${width - 25}" stroke="#506579"/>`;
    a.values.forEach((v, i) => { const x = 95 + i * step; body += `<rect x="${x}" y="${Math.min(zero, y(v))}" width="${step * .65}" height="${Math.abs(y(v) - zero)}" rx="3" fill="${colors[0]}"><title>${escape(a.labels[i])}: ${v} ${escape(a.unit)}</title></rect><text x="${x + step * .325}" y="${v < 0 ? y(v) + 20 : y(v) - 10}" text-anchor="middle" font-size="14">${format(v)}</text><text transform="translate(${x + step * .325},447) rotate(25)" font-size="14"><title>${escape(a.labels[i])}</title>${short(a.labels[i], 12)}</text>`; });
  }
  const description = `Bar chart. Explicit caller-supplied category values: ${a.labels.map((item, i) => `${item}: ${format(a.values[i])}`).join("; ")}.`;
  return chartResult("bar", a.title, frame(a.title, a.unit, width, height, description, body), a);
}
export function lineChart(a: LineChartData) {
  const width = Math.max(960, a.x_labels.length * 24), height = 550 + Math.ceil(a.series_names.length / 2) * 28;
  const [min, max] = domain(a.series_values.flat()), x = (i: number) => 95 + i / (a.x_labels.length - 1) * (width - 145), y = (v: number) => 430 - (v - min) / (max - min) * 320;
  let body = "";
  for (let tick = 0; tick <= 4; tick++) { const v = min + (max - min) * tick / 4, at = y(v); body += `<path d="M95 ${at}H${width - 40}" stroke="#e1e8f0"/><text x="84" y="${at + 5}" text-anchor="end" font-size="14">${format(v)}</text>`; }
  a.x_labels.forEach((l, i) => { if (i % Math.ceil(a.x_labels.length / 10) === 0 || i === a.x_labels.length - 1) body += `<text x="${x(i)}" y="458" text-anchor="middle" font-size="14"><title>${escape(l)}</title>${short(l, 12)}</text>`; });
  a.series_values.forEach((values, si) => {
    body += `<polyline fill="none" stroke="${colors[si]}" stroke-width="3" points="${values.map((v, i) => `${x(i)},${y(v)}`).join(" ")}"/>`;
    values.forEach((v, i) => { body += `<circle cx="${x(i)}" cy="${y(v)}" r="3.5" fill="${colors[si]}"><title>${escape(a.series_names[si])} / ${escape(a.x_labels[i])}: ${v} ${escape(a.unit)}</title></circle>`; });
    const lx = 95 + (si % 2) * (width - 145) / 2, ly = 505 + Math.floor(si / 2) * 28;
    body += `<path d="M${lx} ${ly - 5}h24" stroke="${colors[si]}" stroke-width="3"/><text x="${lx + 34}" y="${ly}">${short(a.series_names[si], 36)}</text>`;
  });
  const description = `Line chart with ${a.series_names.length} series across ${a.x_labels.length} equally spaced categories; categories are not interpreted as dates. Exact values are available in each point's SVG tooltip.`;
  return chartResult("line", a.title, frame(a.title, a.unit, width, height, description, body), a);
}
export type ToolOutput = ReturnType<typeof listSkills> | ReturnType<typeof loadSkill> | ReturnType<typeof routeInvestment> | ReturnType<typeof barChart> | ReturnType<typeof lineChart> | Awaited<ReturnType<typeof runtimeInfo>>;
export function callTool(name: "runtime_info", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof runtimeInfo>;
export function callTool(name: "list_skills", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof listSkills>;
export function callTool(name: "load_skill", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof loadSkill>;
export function callTool(name: "route_investment_request", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof routeInvestment>;
export function callTool(name: "render_bar_chart", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof barChart>;
export function callTool(name: "render_line_chart", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof lineChart>;
export function callTool(name: string, args: unknown, metadata?: SiteVersionMetadata): ToolOutput | Promise<ToolOutput>;
export function callTool(name: string, args: unknown, metadata?: SiteVersionMetadata): ToolOutput | Promise<ToolOutput> {
  switch (name) {
    case "runtime_info": schemas.runtime_info.parse(args); return runtimeInfo(metadata);
    case "list_skills": schemas.list_skills.parse(args); return listSkills();
    case "load_skill": return loadSkill(schemas.load_skill.parse(args).skill_name);
    case "route_investment_request": return routeInvestment(schemas.route_investment_request.parse(args).user_request);
    case "render_bar_chart": {
      const parsed = schemas.render_bar_chart.parse(args);
      return barChart({ labels: parsed.labels, values: parsed.values, title: parsed.title, unit: parsed.unit, horizontal: parsed.horizontal });
    }
    case "render_line_chart": {
      const parsed = schemas.render_line_chart.parse(args);
      return lineChart({ x_labels: parsed.x_labels, series_names: parsed.series_names, series_values: parsed.series_values, title: parsed.title, unit: parsed.unit });
    }
    default: throw new Error("Unknown tool");
  }
}
