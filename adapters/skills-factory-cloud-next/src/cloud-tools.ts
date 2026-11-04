Warning: truncated output (original token count: 10939)
Total output lines: 328

import { z } from "zod";
import { LAB_RELEASE, DRAFT_RELEASE, RUNTIME_RELEASE, SKILL_CATALOG } from "./skill-catalog";
import { CANONICAL_SOURCE_REVISION, ROUTING_CONTRACT_BLOB_SHA } from "./canonical-provenance";
import { CHART_UI_URI } from "./chart-ui";
import { calculateOpportunityScores, opportunityScoreInputSchema } from "./opportunity-score";
import { calculateIssuerExposure, type IssuerExposureInput } from "./issuer-exposure";

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
const issuerPositionSchema = z.object({ position_id: z.string().min(1).max(120), account_id: z.string().min(1).max(120), instrument_id: z.string().min(1).max(120), isin: z.string().min(1).max(24), share_class: z.string().min(1).max(100), instrument_type: z.enum(["equity", "fund"]), weight_pct: z.number().finite().min(0).max(100), market_value_pln: z.number().finite().min(0).optional(), issuer_id: z.string().min(1).max(200).optional(), issuer_name: z.string().min(1).max(200).optional(), factors: z.array(z.string().min(1).max(100)).max(30).optional(), source_id: z.string().min(1).max(200), source_uri: z.string().url().startsWith("https://"), published_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), retrieved_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/) }).strict();
export const schemas = {
  runtime_info: z.object({}).strict(),
  list_skills: z.object({}).strict(),
  load_skill: z.object({ skill_name: z.string().trim().min(1).max(160) }).strict(),
  route_investment_request: z.object({ user_request: z.string().trim().min(1).max(8000) }).strict(),
  calculate_opportunity_scores: opportunityScoreInputSchema,
  calculate_issuer_exposure: z.object({
    as_of: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), base_currency: z.string().trim().min(1).max(8), portfolio_id: z.string().trim().min(1).max(120), portfolio_value_pln: z.number().finite().positive().optional(),
    positions: z.array(issuerPositionSchema).min(1).max(100),
    fund_snapshots: z.array(z.object({ instrument_id: z.string().min(1).max(120), as_of: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), published_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), retrieved_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), source_id: z.string().min(1).max(200), source_uri: z.string().url().startsWith("https://"), completeness: z.enum(["COMPLETE", "PARTIAL"]), coverage_pct: z.number().finite().min(0).max(100), constituents: z.array(z.object({ security_type: z.enum(["issuer", "fund"]), instrument_id: z.string().min(1).max(120).optional(), issuer_id: z.string().min(1).max(200).optional(), issuer_name: z.string().min(1).max(200).optional(), isin: z.string().min(1).max(24), share_class: z.string().min(1).max(100), weight_pct: z.number().finite().min(0).max(100), factors: z.array(z.string().min(1).max(100)).max(30) }).strict()).max(500) }).strict()).max(100),
    previous_snapshot: z.object({ method: z.string().min(1).max(120), portfolio_id: z.string().min(1).max(120), base_currency: z.string().min(1).max(8), as_of: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), status: z.string().min(1).max(40), source_coverage_pct: z.number().finite().min(0).max(100), decomposition_complete: z.boolean(), issuers: z.array(z.object({ issuer_id: z.string().min(1).max(200), known_minimum_total_pct: z.number().finite().min(0).max(100) }).strict()).max(500) }).strict().optional(),
    scenario_positions: z.array(issuerPositionSchema).min(1).max(100).optional(),
    factor_shocks: z.array(z.object({ factor: z.string().min(1).max(100), shock_pct: z.number().finite().min(-100).max(100), scenario_id: z.string().min(1).max(120) }).strict()).max(30).optional(),
  }).strict(),
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
const opportunityFactorSchema = {
  type: "object",
  properties: {
    value: { type: "number", minimum: 0, maximum: 1 }, confidence: { type: "number", minimum: 0, maximum: 1 },
    as_of_date: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" },
    source_ids: { type: "array", minItems: 1, maxItems: 20, items: { type: "string", minLength: 1, maxLength: 200 } },
    definition: { type: "string", minLength: 1, maxLength: 500 }, normalization_profile: { type: "string", minLength: 1, maxLength: 200 },
    quality: { type: "string", enum: ["VERIFIED", "PROVISIONAL", "BLOCKED"] },
  },
  required: ["value", "confidence", "as_of_date", "source_ids", "definition", "normalization_profile", "quality"],
  additionalProperties: false,
};
const opportunityScoreToolInputSchema = {
  type: "object",
  properties: {
    as_of: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" },
    rows: {
      type: "array", minItems: 1, maxItems: 30,
      items: {
        type: "object",
        properties: {
          candidate_id: { type: "string", minLength: 1, maxLength: 120 },
          horizon: { type: "string", enum: ["1-3m", "6-12m", ">3y"] },
          evidence: { type: "object", maxProperties: 30, description: "Factor-name keyed object. Each value is a normalized factor with dated source IDs and an explicit quality label.", additionalProperties: opportunityFactorSchema },
        },
        required: ["candidate_id", "horizon", "evidence"], additionalProperties: false,
      },
    },
  },
  required: ["as_of", "rows"], additionalProperties: false,
};
const dateSchema = { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" };
const issuerExposureToolInputSchema = {
  type: "object", additionalProperties: false,
  required: ["as_of", "base_currency", "portfolio_id", "positions", "fund_snapshots"],
  properties: {
    as_of: dateSchema,
    base_currency: { type: "string", minLength: 1, maxLength: 8 },
    portfolio_id: { type: "string", minLength: 1, maxLength: 120 },
    portfolio_value_pln: { type: "number", exclusiveMinimum: 0 },
    positions: { type: "array", minItems: 1, maxItems: 100, items: { type: "object", additionalProperties: false,
      required: ["position_id", "account_id", "instrument_id", "isin", "share_class", "instrument_type", "weight_pct", "source_id", "source_uri", "published_at", "retrieved_at"],
      properties: {
        position_id: { type: "string" }, account_id: { type: "string" }, instrument_id: { type: "string" }, isin: { type: "string" }, share_class: { type: "string" },
        instrument_type: { type: "string", enum: ["equity", "fund"] }, weight_pct: { type: "number", minimum: 0, maximum: 100 }, market_value_pln: { type: "number", minimum: 0 },
        issuer_id: { type: "string" }, issuer_name: { type: "string" }, factors: { type: "array", maxItems: 30, items: { type: "string" } }, source_id: { type: "string" }, source_uri: { type: "string", format: "uri" }, published_at: dateSchema, retrieved_at: dateSchema,
      },
    } },
    fund_snapshots: { type: "array", maxItems: 100, items: { type: "object", additionalProperties: false,
      required: ["instrument_id", "as_of", "published_at", "retrieved_at", "source_id", "source_uri", "completeness", "coverage_pct", "constituents"],
      properties: {
        instrument_id: { type: "string" }, as_of: dateSchema, published_at: dateSchema, retrieved_at: dateSchema, source_id: { type: "string" }, source_uri: { type: "string", format: "uri" },
        completeness: { type: "string", enum: ["COMPLETE", "PARTIAL"] }, coverage_pct: { type: "number", minimum: 0, maximum: 100 },
        constituents: { type: "array", maxItems: 500, items: { type: "object", additionalProperties: false, required: ["security_type", "isin", "share_class", "weight_pct", "factors"], properties: {
          security_type: { type: "string", enum: ["issuer", "fund"] }, instrument_id: { type: "string" }, issuer_id: { type: "string" }, issuer_name: { type: "string" }, isin: { type: "string" }, share_class: { type: "string" }, weight_pct: { type: "number", minimum: 0, maximum: 100 }, factors: { type: "array", maxItems: 30, items: { type: "string" } },
        } } },
      },
    } },
    previous_snapshot: { type: "object", additionalProperties: false, required: ["method", "portfolio_id", "base_currency", "as_of", "status", "source_coverage_pct", "decomposition_complete", "issuers"], properties: {
      method: { type: "string" }, portfolio_id: { type: "string" }, base_currency: { type: "string" }, as_of: dateSchema, status: { type: "string" }, source_coverage_pct: { type: "number", minimum: 0, maximum: 100 }, decomposition_complete: { type: "boolean" },
      issuers: { type: "array", maxItems: 500, items: { type: "object", additionalProperties: false, required: ["issuer_id", "known_minimum_total_pct"], properties: { issuer_id: { type: "string" }, known_minimum_total_pct: { type: "number", minimum: 0, maximum: 100 } } } },
    } },
    scenario_positions: { type: "array", minItems: 1, maxItems: 100, items: { $ref: "#/$defs/issuer_position" } },
    factor_shocks: { type: "array", maxItems: 30, items: { type: "object", additionalProperties: false, required: ["factor", "shock_pct", "scenario_id"], properties: { factor: { type: "string", minLength: 1 }, shock_pct: { type: "number", minimum: -100, maximum: 100 }, scenario_id: { type: "string", minLength: 1 } } } },
  },
  $defs: { issuer_position: { type: "object", additionalProperties: false, required: ["position_id", "account_id", "instrument_id", "isin", "share_class", "instrument_type", "weight_pct", "source_id", "source_uri", "published_at", "retrieved_at"], properties: { position_id: { type: "string" }, account_id: { type: "string" }, instrument_id: { type: "string" }, isin: { type: "string" }, share_class: { type: "string" }, instrument_type: { type: "string", enum: ["equity", "fund"] }, weight_pct: { type: "number", minimum: 0, maximum: 100 }, market_value_pln: { type: "number", minimum: 0 }, issuer_id: { type: "string" }, issuer_name: { type: "string" }, factors: { type: "array", maxItems: 30, items: { type: "string" } }, source_id: { type: "string" }, source_uri: { type: "string", format: "uri" }, published_at: dateSchema, retrieved_at: dateSchema } } },
};
export const TOOLS = [
  { name: "runtime_info", description: "Return this Site Worker's deployment attestation and the embedded Skills Factory Lab release. Missing platform identity is reported as unattested. Read-only; does not execute a skill.", inputSchema: { type: "object", properties: {}, additionalProperties: false }, annotations },
  { name: "list_skills", description: "List every skill and workflow in the source-bound Lab artifact irrespective of maturity, inclu…3939 tokens truncated…:med|s|ming)?\b|\bbuy\b|\bsell\b|kup|dodaj|zwieksz|zmniejsz|sprzed|pozycj/.test(s));
  const aggregateExposureIntent = /issuer exposure|issuer look[ -]?through|look[ -]?through|cross[ -]?(?:etf|fund)|sector exposure|exposure coverage|exposure drift|etf overlap|fund overlap|portfolio concentration/.test(s);
  const aggregatePortfolioReview = portfolio
    && (risk || tickerCount >= 2 || aggregateExposureIntent)
    && (!singleSecurityIntent || aggregateExposureIntent);
  let candidates: string[] = [], reason = "No unambiguous decision object matched.";
  if (explicit.length) { candidates = [...explicit]; reason = "Explicit workflow names in the request."; }
  else if (policyDesignIntent) { candidates = [routes[6]]; reason = "The user explicitly asks to define or change investment rules or risk limits."; }
  else if (systemicRiskTriage && !replay && (!portfolio || /issuer exposure|cross.asset|credit|macro/.test(s))) { candidates = [routes[5]]; reason = "The decision object is systemic or cross-asset risk observation; historical vintage and missing portfolio evidence remain explicit."; }
  else if (replay) { candidates = [routes[7]]; reason = "The request reconstructs or evaluates a historical decision with as-of or out-of-sample constraints."; }
  else if (technicalStructure) { candidates = [routes[8]]; reason = "The request evaluates price pivots, trend structure or invalidation levels."; }
  else if (portfolioAction) { candidates = [routes[1]]; reason = "The request reallocates or liquidates multiple holdings, so the portfolio owns the decision."; }
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
  const investmentContext = explicit.length > 0 || replay || technicalStructure || systemicRiskTriage || singleSecurityIntent || /investment|investing|portfolio|stock|security|securities|etf|fund|holdings|watchlist|inwestyc|portfel|spol|akcj|share|thesis|gross margin|marza brutto|research candidates/.test(s) || opportunity || theme || policy;
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
export type ToolOutput = ReturnType<typeof listSkills> | ReturnType<typeof loadSkill> | ReturnType<typeof routeInvestment> | ReturnType<typeof barChart> | ReturnType<typeof lineChart> | ReturnType<typeof calculateOpportunityScores> | ReturnType<typeof calculateIssuerExposure> | Awaited<ReturnType<typeof runtimeInfo>>;
export function callTool(name: "runtime_info", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof runtimeInfo>;
export function callTool(name: "list_skills", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof listSkills>;
export function callTool(name: "load_skill", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof loadSkill>;
export function callTool(name: "route_investment_request", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof routeInvestment>;
export function callTool(name: "calculate_opportunity_scores", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof calculateOpportunityScores>;
export function callTool(name: "calculate_issuer_exposure", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof calculateIssuerExposure>;
export function callTool(name: "render_bar_chart", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof barChart>;
export function callTool(name: "render_line_chart", args: unknown, metadata?: SiteVersionMetadata): ReturnType<typeof lineChart>;
export function callTool(name: string, args: unknown, metadata?: SiteVersionMetadata): ToolOutput | Promise<ToolOutput>;
export function callTool(name: string, args: unknown, metadata?: SiteVersionMetadata): ToolOutput | Promise<ToolOutput> {
  switch (name) {
    case "runtime_info": schemas.runtime_info.parse(args); return runtimeInfo(metadata);
    case "list_skills": schemas.list_skills.parse(args); return listSkills();
    case "load_skill": return loadSkill(schemas.load_skill.parse(args).skill_name);
    case "route_investment_request": return routeInvestment(schemas.route_investment_request.parse(args).user_request);
    case "calculate_opportunity_scores": return calculateOpportunityScores(schemas.calculate_opportunity_scores.parse(args));
    case "calculate_issuer_exposure": return calculateIssuerExposure(schemas.calculate_issuer_exposure.parse(args) as IssuerExposureInput);
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
