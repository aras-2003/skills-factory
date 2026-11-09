import { z } from "zod";

const nonempty = (max: number) => z.string().trim().min(1).max(max);
const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const httpsUrl = z.string().url().startsWith("https://");
const fitSchema = z.object({
  alignment: z.enum(["MATCH", "PARTIAL", "UNKNOWN", "MISMATCH"]),
  target_summary: nonempty(500), peer_summary: nonempty(500), rationale: nonempty(1000),
  target_published_at: date, target_source_url: httpsUrl, published_at: date, source_url: httpsUrl,
}).strict();
const metricSchema = z.object({
  name: nonempty(80), value: z.string().regex(/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/).nullable(),
  unit: nonempty(40), definition: nonempty(500), period: nonempty(160), basis: nonempty(200),
  published_at: date, source_url: httpsUrl, status: z.enum(["VERIFIED", "PROVISIONAL", "UNVERIFIED", "CONFLICTED", "NOT_APPLICABLE"]),
  horizon: z.string().max(80).default(""), currency: nonempty(12),
  period_alignment_group: z.string().max(200).default(""), basis_group: z.string().max(200).default(""),
  supporting_source_urls: z.array(httpsUrl).max(20).default([]),
}).strict();
const issuerSchema = z.object({
  ticker: nonempty(40), sector: nonempty(100), industry: nonempty(100), business_model: nonempty(200),
  as_of: date, metrics: z.record(nonempty(80), metricSchema).superRefine((metrics, ctx) => {
    if (Object.keys(metrics).length > 40) ctx.addIssue({ code: "custom", message: "at most 40 metrics are allowed" });
    for (const [key, metric] of Object.entries(metrics)) if (key !== metric.name) ctx.addIssue({ code: "custom", path: [key], message: "metric key must equal metric.name" });
  }),
  cyclical: z.boolean().default(false), comparison_group: nonempty(200), inclusion_rationale: z.string().max(1000).default(""),
  peer_tier: z.enum(["DIRECT", "ADJACENT", "TARGET"]).default("TARGET"),
  economic_fit: z.record(z.string(), fitSchema).default({}).superRefine((fit, ctx) => {
    for (const key of Object.keys(fit)) if (!FIT_DIMENSIONS.includes(key as typeof FIT_DIMENSIONS[number])) ctx.addIssue({ code: "custom", path: [key], message: "unknown economic-fit dimension" });
    if (Object.keys(fit).length > FIT_DIMENSIONS.length) ctx.addIssue({ code: "custom", message: "too many economic-fit dimensions" });
  }),
}).strict();

export const peerComparabilityInputSchema = z.object({
  as_of: date, target: issuerSchema,
  peers: z.array(issuerSchema).max(15),
}).strict().superRefine((input, ctx) => {
  if (input.target.as_of !== input.as_of) ctx.addIssue({ code: "custom", path: ["target", "as_of"], message: "target snapshot date must match as_of" });
  if (input.peers.some((peer) => peer.peer_tier === "TARGET")) ctx.addIssue({ code: "custom", path: ["peers"], message: "peer tier must be DIRECT or ADJACENT" });
});

export type PeerComparabilityInput = z.infer<typeof peerComparabilityInputSchema>;
type Issuer = PeerComparabilityInput["target"];
type Metric = Issuer["metrics"][string];
const FIT_DIMENSIONS = ["value_chain_role", "revenue_profit_mix", "customer_base", "cyclicality", "capital_intensity"] as const;
const MULTIPLES = new Set(["ev_sales", "ev_ebitda", "forward_pe", "price_sales", "price_to_sales", "ev_fcf"]);
const FRACTIONS = new Set(["revenue_growth", "fcf_growth", "eps_cagr", "fcf_yield", "operating_margin", "gross_margin", "fcf_margin", "roic", "eps_revision_90d"]);
const FORWARD = new Set(["forward_pe", "eps_cagr"]);
const CORE = ["ev_ebitda", "ev_sales", "forward_pe"] as const;
const nonblank = (value: unknown): value is string => typeof value === "string" && value.trim().length > 0;
const validDate = (value: string) => {
  const d = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(d.getTime()) && d.toISOString().slice(0, 10) === value;
};
const daysBetween = (later: string, earlier: string) => (Date.parse(`${later}T00:00:00Z`) - Date.parse(`${earlier}T00:00:00Z`)) / 86_400_000;
const validHttps = (value: string) => { try { const u = new URL(value); return u.protocol === "https:" && Boolean(u.hostname); } catch { return false; } };

function fitReason(peer: Issuer, asOf: string): string | null {
  const evidence = peer.economic_fit as Record<string, z.infer<typeof fitSchema>>;
  if (FIT_DIMENSIONS.some((dimension) => !evidence?.[dimension])) return "INCOMPLETE_DIRECT_FIT_EVIDENCE";
  for (const dimension of FIT_DIMENSIONS) {
    const item = evidence[dimension];
    if (!item || !["MATCH", "PARTIAL"].includes(item.alignment)) return "DIRECT_FIT_NOT_ESTABLISHED";
    if (!nonblank(item.target_summary) || !nonblank(item.peer_summary) || !nonblank(item.rationale)) return "INCOMPLETE_DIRECT_FIT_EVIDENCE";
    if (!validDate(item.target_published_at) || !validDate(item.published_at) || item.target_published_at > asOf || item.published_at > asOf) return "INVALID_OR_LOOKAHEAD_DIRECT_FIT_SOURCE_DATE";
    if (daysBetween(asOf, item.target_published_at) > 400 || daysBetween(asOf, item.published_at) > 400) return "STALE_DIRECT_FIT_EVIDENCE";
    if (!validHttps(item.target_source_url) || !validHttps(item.source_url)) return "INVALID_DIRECT_FIT_SOURCE_URL";
  }
  return null;
}

function metricReason(metric: Metric | undefined, name: string, asOf: string, comparison?: Metric): string | null {
  if (!metric) return "MISSING";
  if (!["VERIFIED", "PROVISIONAL"].includes(metric.status)) return metric.status;
  if (metric.value === null || !Number.isFinite(Number(metric.value))) return "MISSING_OR_NONFINITE";
  if (!validDate(metric.published_at) || metric.published_at > asOf) return "LOOKAHEAD";
  if (!validHttps(metric.source_url) || metric.supporting_source_urls.some((url) => !validHttps(url))) return "INVALID_SOURCE_URL";
  if (![metric.name, metric.unit, metric.definition, metric.period, metric.basis, metric.currency].every(nonblank)) return "INCOMPLETE_DEFINITION";
  const value = Number(metric.value);
  if ((MULTIPLES.has(name) || metric.unit === "multiple") && (metric.unit !== "multiple" || value <= 0)) return "NOT_MEANINGFUL";
  if (FRACTIONS.has(name) && metric.unit !== "fraction") return "INCOMPATIBLE_UNIT";
  if (FORWARD.has(name)) {
    if (!metric.horizon) return "MISSING_FORECAST_HORIZON";
    if ((name === "forward_pe" && !["12M", "NTM"].includes(metric.horizon)) || (name === "eps_cagr" && !["3Y", "5Y", "3–5Y"].includes(metric.horizon))) return name === "forward_pe" ? "INCOMPATIBLE_FORWARD_PE_HORIZON" : "INCOMPATIBLE_EPS_GROWTH_HORIZON";
    if (daysBetween(asOf, metric.published_at) > 90) return "STALE_FORWARD_OR_REVISION_DATA";
  }
  if (comparison && (
    metric.name !== comparison.name || metric.unit !== comparison.unit || metric.definition !== comparison.definition || metric.horizon !== comparison.horizon ||
    (metric.period !== comparison.period && !(nonblank(metric.period_alignment_group) && metric.period_alignment_group === comparison.period_alignment_group)) ||
    (metric.basis !== comparison.basis && !(nonblank(metric.basis_group) && metric.basis_group === comparison.basis_group)) ||
    (metric.currency.toUpperCase() !== comparison.currency.toUpperCase() && !["fraction", "multiple", "heuristic"].includes(metric.unit))
  )) return "INCOMPATIBLE_DEFINITION_PERIOD_BASIS_OR_HORIZON";
  return null;
}

export function comparePeerComparability(input: PeerComparabilityInput) {
  const { target, peers, as_of: asOf } = input;
  if (!validDate(asOf) || target.as_of !== asOf || peers.length > 15) throw new Error("invalid as_of or peer count");
  const tickers = peers.map((peer) => peer.ticker.trim().toUpperCase());
  if (new Set(tickers).size !== tickers.length || tickers.includes(target.ticker.trim().toUpperCase())) throw new Error("duplicate or target peer");
  const rows = [...peers].sort((a, b) => a.ticker.localeCompare(b.ticker)).map((peer) => {
    let reason: string | null = null;
    if (peer.as_of !== asOf) reason = "AS_OF_MISMATCH";
    else if (peer.peer_tier === "DIRECT" && (peer.sector !== target.sector || peer.industry !== target.industry)) reason = "SECTOR_OR_INDUSTRY_MISMATCH";
    else if (!peer.ticker || !peer.sector || !peer.industry || !peer.business_model) reason = "MISSING_PEER_IDENTITY";
    else if (!["DIRECT", "ADJACENT"].includes(peer.peer_tier)) reason = "INVALID_COMPARABILITY_TIER";
    else if (!peer.comparison_group || peer.comparison_group !== target.comparison_group) reason = "COMPARISON_GROUP_MISMATCH";
    else if (!nonblank(peer.inclusion_rationale)) reason = "MISSING_INCLUSION_RATIONALE";
    else if (peer.peer_tier === "DIRECT") reason = fitReason(peer, asOf);

    const row: Record<string, unknown> = {
      ticker: peer.ticker, eligibility: reason ? "EXCLUDED" : "INCLUDED", reason,
      business_model: peer.business_model, comparison_group: peer.comparison_group,
      comparability_tier: reason ? "EXCLUDED" : peer.peer_tier,
      inclusion_rationale: peer.inclusion_rationale || null,
      exclusion_rationale: reason,
      economic_fit: reason ? {} : peer.economic_fit,
      cycle_normalization_required: peer.cyclical, metrics: {} as Record<string, unknown>,
    };
    if (reason) return row;
    const metrics = row.metrics as Record<string, unknown>;
    for (const [name, targetMetric] of Object.entries(target.metrics).sort(([a], [b]) => a.localeCompare(b))) {
      const peerMetric = peer.metrics[name];
      const metricReasonResult = metricReason(targetMetric, name, asOf) ?? metricReason(peerMetric, name, asOf, targetMetric);
      if (metricReasonResult || !peerMetric) {
        metrics[name] = {
          value: "N/M", unit: targetMetric.unit, status: "NOT_MEANINGFUL", reason: metricReasonResult ?? "MISSING",
          definition: targetMetric.definition, period: targetMetric.period, horizon: targetMetric.horizon, basis: targetMetric.basis,
          target_currency: targetMetric.currency, target_source_url: targetMetric.source_url,
          target_supporting_source_urls: targetMetric.supporting_source_urls, target_published_at: targetMetric.published_at,
          peer_basis: peerMetric?.basis ?? null, peer_period: peerMetric?.period ?? null,
          target_period_alignment_group: targetMetric.period_alignment_group, peer_period_alignment_group: peerMetric?.period_alignment_group ?? null,
          target_basis_group: targetMetric.basis_group, peer_basis_group: peerMetric?.basis_group ?? null,
          peer_source_url: peerMetric?.source_url ?? null, peer_supporting_source_urls: peerMetric?.supporting_source_urls ?? [],
          peer_published_at: peerMetric?.published_at ?? null,
        };
      } else {
        metrics[name] = {
          value: peerMetric.value, unit: peerMetric.unit,
          status: targetMetric.status === "VERIFIED" && peerMetric.status === "VERIFIED" ? "VERIFIED" : "PROVISIONAL",
          reason: null, definition: peerMetric.definition, period: peerMetric.period, horizon: peerMetric.horizon, basis: peerMetric.basis,
          target_period: targetMetric.period, target_basis: targetMetric.basis,
          peer_period_alignment_group: peerMetric.period_alignment_group, target_period_alignment_group: targetMetric.period_alignment_group,
          peer_basis_group: peerMetric.basis_group, target_basis_group: targetMetric.basis_group,
          peer_currency: peerMetric.currency, target_currency: targetMetric.currency, target_value: targetMetric.value,
          target_source_url: targetMetric.source_url, target_supporting_source_urls: targetMetric.supporting_source_urls,
          target_published_at: targetMetric.published_at, source_url: peerMetric.source_url,
          supporting_source_urls: peerMetric.supporting_source_urls, published_at: peerMetric.published_at,
        };
      }
    }
    return row;
  });
  const includedRows = rows.filter((row) => row.eligibility === "INCLUDED");
  const included = includedRows.filter((row) => row.comparability_tier === "DIRECT");
  const counts = Object.fromEntries(CORE.map((name) => [name, included.filter((row) => {
    const metric = (row.metrics as Record<string, { status?: string }>)[name];
    return metric && ["VERIFIED", "PROVISIONAL"].includes(metric.status ?? "");
  }).length]));
  const reason = included.length < 3 ? "FEWER_THAN_THREE_DIRECT_PEERS" : !Object.values(counts).some((count) => count >= 3) ? "NO_CORE_METRIC_HAS_THREE_COMPATIBLE_DIRECT_PEERS" : null;
  const metricNames = Object.keys(target.metrics).sort();
  const tableRows = [
    {
      ticker: target.ticker, business_model: target.business_model, comparability_tier: "TARGET",
      eligibility: "TARGET", reason: null,
      metrics: Object.fromEntries(metricNames.map((name) => {
        const metric = target.metrics[name];
        const metricStatus = metricReason(metric, name, asOf);
        return [name, {
          value: metricStatus ? "N/M" : metric.value, unit: metric.unit,
          status: metricStatus ? "NOT_MEANINGFUL" : metric.status,
          reason: metricStatus, definition: metric.definition, period: metric.period,
          basis: metric.basis, currency: metric.currency, horizon: metric.horizon,
          published_at: metric.published_at, source_url: metric.source_url,
          supporting_source_urls: metric.supporting_source_urls,
        }];
      })),
    },
    ...rows.map((row) => ({
      ticker: row.ticker, business_model: row.business_model, comparability_tier: row.comparability_tier,
      eligibility: row.eligibility, reason: row.exclusion_rationale,
      metrics: Object.fromEntries(metricNames.map((name) => {
        const details = (row.metrics as Record<string, Record<string, unknown>>)[name];
        return [name, details ? {
          value: details.value, unit: details.unit, status: details.status, reason: details.reason,
          definition: details.definition, period: details.period, basis: details.basis,
          currency: details.peer_currency ?? details.target_currency,
          horizon: details.horizon, published_at: details.published_at ?? details.peer_published_at,
          source_url: details.source_url ?? details.peer_source_url,
          supporting_source_urls: details.supporting_source_urls ?? details.peer_supporting_source_urls,
        } : { value: "N/M", status: "NOT_MEANINGFUL", reason: row.exclusion_rationale }];
      })),
    })),
  ];
  return {
    status: reason ? "INSUFFICIENT_COMPARABLE_PEERS" : "COMPARABLE", comparability_reason: reason,
    as_of: asOf, target: target.ticker, sector: target.sector, industry: target.industry,
    business_model: target.business_model, comparison_group: target.comparison_group,
    evidence_status_semantics: "Caller-supplied status; source verification is not performed by this tool.",
    included_peer_count: includedRows.length, direct_peer_count: included.length,
    core_metric_peer_counts: counts, cycle_normalization_required: target.cyclical,
    required_peer_range: "3–5 for a compact table; expand to 5–15 only when economically valid",
    table: { as_of: asOf, metric_names: metricNames, rows: tableRows },
    peers: rows, recommendation: null, ranked: false, cross_sector_ranking: false,
    limitations: ["Caller-supplied snapshots only; no source retrieval or verification.", "N/M marks missing or incompatible metrics; no values are inferred.", "This tool provides comparability checks, not an investment recommendation, ranking, valuation, or portfolio action."],
  };
}

export const peerComparabilityToolInputSchema = {
  type: "object", additionalProperties: false, required: ["as_of", "target", "peers"], properties: {
    as_of: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" },
    target: { $ref: "#/$defs/issuer" },
    peers: { type: "array", maxItems: 15, items: { $ref: "#/$defs/issuer" } },
  },
  $defs: {
    fit: { type: "object", additionalProperties: false, required: ["alignment", "target_summary", "peer_summary", "rationale", "target_published_at", "target_source_url", "published_at", "source_url"], properties: {
      alignment: { type: "string", enum: ["MATCH", "PARTIAL", "UNKNOWN", "MISMATCH"] }, target_summary: { type: "string", minLength: 1, maxLength: 500 }, peer_summary: { type: "string", minLength: 1, maxLength: 500 }, rationale: { type: "string", minLength: 1, maxLength: 1000 }, target_published_at: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" }, target_source_url: { type: "string", format: "uri" }, published_at: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" }, source_url: { type: "string", format: "uri" },
    } },
    metric: { type: "object", additionalProperties: false, required: ["name", "value", "unit", "definition", "period", "basis", "published_at", "source_url", "status", "horizon", "currency", "period_alignment_group", "basis_group", "supporting_source_urls"], properties: {
      name: { type: "string", minLength: 1, maxLength: 80 }, value: { anyOf: [{ type: "string", pattern: "^-?(?:\\d+\\.?\\d*|\\.\\d+)(?:[eE][+-]?\\d+)?$" }, { type: "null" }] }, unit: { type: "string", minLength: 1, maxLength: 40 }, definition: { type: "string", minLength: 1, maxLength: 500 }, period: { type: "string", minLength: 1, maxLength: 160 }, basis: { type: "string", minLength: 1, maxLength: 200 }, published_at: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" }, source_url: { type: "string", format: "uri" }, status: { type: "string", enum: ["VERIFIED", "PROVISIONAL", "UNVERIFIED", "CONFLICTED", "NOT_APPLICABLE"] }, horizon: { type: "string", maxLength: 80 }, currency: { type: "string", minLength: 1, maxLength: 12 }, period_alignment_group: { type: "string", maxLength: 200 }, basis_group: { type: "string", maxLength: 200 }, supporting_source_urls: { type: "array", maxItems: 20, items: { type: "string", format: "uri" } },
    } },
    issuer: { type: "object", additionalProperties: false, required: ["ticker", "sector", "industry", "business_model", "as_of", "metrics", "cyclical", "comparison_group", "inclusion_rationale", "peer_tier", "economic_fit"], properties: {
      ticker: { type: "string", minLength: 1, maxLength: 40 }, sector: { type: "string", minLength: 1, maxLength: 100 }, industry: { type: "string", minLength: 1, maxLength: 100 }, business_model: { type: "string", minLength: 1, maxLength: 200 }, as_of: { type: "string", pattern: "^\\d{4}-\\d{2}-\\d{2}$" }, metrics: { type: "object", maxProperties: 40, additionalProperties: { $ref: "#/$defs/metric" } }, cyclical: { type: "boolean" }, comparison_group: { type: "string", minLength: 1, maxLength: 200 }, inclusion_rationale: { type: "string", maxLength: 1000 }, peer_tier: { type: "string", enum: ["DIRECT", "ADJACENT", "TARGET"] }, economic_fit: { type: "object", maxProperties: 5, propertyNames: { enum: [...FIT_DIMENSIONS] }, additionalProperties: { $ref: "#/$defs/fit" } },
    } },
  },
};
