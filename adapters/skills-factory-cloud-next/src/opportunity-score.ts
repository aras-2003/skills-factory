import { z } from "zod";

/**
 * Runtime mirror of skills/investing/fundamental-intelligence/engine.py.
 * Keep the Python and Worker implementations in parity with the shared known-answer
 * fixture exercised by the adapter contract suite and Python unit suite.
 */
const SCALE = 100_000_000n;
const MODEL_VERSION = "opportunity-score-v0.1-provisional";
const MIN_CONFIDENCE = 0.5;

const horizonWeights = {
  "1-3m": {
    catalyst_timing: [22, 45], estimate_revisions: [18, 90], valuation_expectations: [15, 90],
    price_setup: [15, 30], scenario_asymmetry: [20, 90], cycle_resilience: [10, 180],
  },
  "6-12m": {
    scenario_asymmetry: [23, 180], valuation_expectations: [22, 180], estimate_revisions: [18, 120],
    business_quality: [17, 365], risk_resilience: [10, 180], cycle_resilience: [10, 365],
  },
  ">3y": {
    growth_durability: [24, 365], business_quality: [22, 365], reinvestment_returns: [18, 365],
    valuation_expectations: [16, 180], balance_sheet_resilience: [10, 180], cycle_resilience: [10, 730],
  },
} as const;

type Horizon = keyof typeof horizonWeights;
type Factor = {
  value: number;
  confidence: number;
  as_of_date: string;
  source_ids: string[];
  definition: string;
  normalization_profile: string;
  quality: "VERIFIED" | "PROVISIONAL" | "BLOCKED";
};
type ScoreInput = { candidate_id: string; horizon: Horizon; evidence: Record<string, Factor> };

export const opportunityScoreInputSchema = z.object({
  as_of: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  rows: z.array(z.object({
    candidate_id: z.string().trim().min(1).max(120),
    horizon: z.enum(["1-3m", "6-12m", ">3y"]),
    evidence: z.record(z.string(), z.object({
      value: z.number().finite().min(0).max(1),
      confidence: z.number().finite().min(0).max(1),
      as_of_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      source_ids: z.array(z.string().trim().min(1).max(200)).min(1).max(20),
      definition: z.string().trim().min(1).max(500),
      normalization_profile: z.string().trim().min(1).max(200),
      quality: z.enum(["VERIFIED", "PROVISIONAL", "BLOCKED"]),
    }).strict()),
  }).strict()).min(1).max(30),
}).strict().superRefine((input, ctx) => {
  if (!validDate(input.as_of)) ctx.addIssue({ code: "custom", path: ["as_of"], message: "as_of must be a real ISO calendar date" });
  input.rows.forEach((row, rowIndex) => {
    if (Object.keys(row.evidence).length > 30) ctx.addIssue({ code: "custom", path: ["rows", rowIndex, "evidence"], message: "at most 30 evidence factors are allowed per row" });
    for (const [name, factor] of Object.entries(row.evidence)) {
      if (!validDate(factor.as_of_date)) ctx.addIssue({ code: "custom", path: ["rows", rowIndex, "evidence", name, "as_of_date"], message: "factor date must be a real ISO calendar date" });
      if (!hasMaxDecimalPlaces(factor.value) || !hasMaxDecimalPlaces(factor.confidence)) ctx.addIssue({ code: "custom", path: ["rows", rowIndex, "evidence", name], message: "value and confidence support at most 8 decimal places" });
    }
  });
});

function validDate(value: string) {
  const date = new Date(`${value}T00:00:00.000Z`);
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function hasMaxDecimalPlaces(value: number) {
  const scaled = value * Number(SCALE);
  return Number.isSafeInteger(Math.round(scaled)) && Math.abs(scaled - Math.round(scaled)) < 0.00001;
}

function scaled(value: number): bigint { return BigInt(Math.round(value * Number(SCALE))); }
function roundHalfUp(numerator: bigint, denominator: bigint): bigint { return (numerator * 2n + denominator) / (2n * denominator); }
function decimalString(numerator: bigint, denominator: bigint, places = 10) {
  const negative = numerator < 0n;
  const absolute = negative ? -numerator : numerator;
  const whole = absolute / denominator;
  const fraction = ((absolute % denominator) * 10n ** BigInt(places) / denominator).toString().padStart(places, "0").replace(/0+$/, "");
  return `${negative ? "-" : ""}${whole}${fraction ? `.${fraction}` : ""}`;
}
function fixedHundredths(value: bigint) { return `${value / 100n}.${(value % 100n).toString().padStart(2, "0")}`; }
function dayNumber(value: string) { return Math.floor(Date.parse(`${value}T00:00:00.000Z`) / 86_400_000); }

type Scored = Record<string, unknown> & {
  candidate_id: string;
  horizon: Horizon;
  model_version: string;
  as_of: string;
  status: string;
  score: string | null;
  unrounded_score?: string;
  normalization_profiles?: Record<string, string>;
  factor_evidence?: Record<string, { definition: string }>;
};

function scoreOne(row: ScoreInput, asOf: string): Scored {
  const profile = horizonWeights[row.horizon] as Record<string, readonly [number, number]>;
  const missing: string[] = [], stale: string[] = [], future: string[] = [], weak: string[] = [], invalid: string[] = [];
  const valid: Record<string, Factor> = {};
  let completenessWeight = 0n;
  let confidenceNumerator = 0n;
  for (const [name, [weight, maxAge]] of Object.entries(profile)) {
    const item = row.evidence[name];
    if (!item) { missing.push(name); continue; }
    if (!validDate(item.as_of_date) || !item.definition.trim() || !item.normalization_profile.trim() || !item.source_ids.length
        || !hasMaxDecimalPlaces(item.value) || !hasMaxDecimalPlaces(item.confidence) || item.quality === "BLOCKED") {
      invalid.push(name); continue;
    }
    const age = dayNumber(asOf) - dayNumber(item.as_of_date);
    if (age < 0) { future.push(name); continue; }
    if (age > maxAge) { stale.push(name); continue; }
    if (item.confidence < MIN_CONFIDENCE) { weak.push(name); continue; }
    valid[name] = item;
    completenessWeight += BigInt(weight);
    confidenceNumerator += BigInt(weight) * scaled(item.confidence) * (item.quality === "VERIFIED" ? 100n : 70n);
  }
  const completeness = fixedHundredths(completenessWeight);
  const confidence = completenessWeight ? fixedHundredths(roundHalfUp(confidenceNumerator * 100n, completenessWeight * 100n * SCALE)) : null;
  const reasons = { missing_factors: missing, stale_factors: stale, future_dated_factors: future, weak_evidence_factors: weak, invalid_factors: invalid };
  if (missing.length || stale.length || future.length || weak.length || invalid.length) {
    return { candidate_id: row.candidate_id, horizon: row.horizon, model_version: MODEL_VERSION, as_of: asOf, status: "NOT_SCORED", reason: "EVIDENCE_GATE", score: null, completeness, confidence, ...reasons };
  }
  let numerator = 0n;
  const factorContributions: Record<string, string> = {}, factorWeights: Record<string, string> = {};
  for (const [name, [weight]] of Object.entries(profile)) {
    const value = scaled(valid[name].value);
    numerator += BigInt(weight) * value;
    factorContributions[name] = decimalString(BigInt(weight) * value, 100n * SCALE);
    factorWeights[name] = fixedHundredths(BigInt(weight));
  }
  const denominator = 100n * SCALE;
  const scoreHundredths = roundHalfUp(numerator, SCALE);
  const rawHundredths = numerator * 100n;
  const band = rawHundredths >= 80n * denominator ? "VERY_ATTRACTIVE"
    : rawHundredths >= 65n * denominator ? "ATTRACTIVE"
    : rawHundredths >= 45n * denominator ? "NEUTRAL_WATCH"
    : rawHundredths >= 25n * denominator ? "WEAK" : "UNFAVORABLE";
  const action = rawHundredths >= 65n * denominator ? "PRIORITIZE"
    : rawHundredths >= 45n * denominator ? "WATCH"
    : rawHundredths >= 25n * denominator ? "DEPRIORITIZE" : "REJECT";
  const factorEvidence = Object.fromEntries(Object.entries(valid).map(([name, item]) => [name, {
    value: decimalString(scaled(item.value), SCALE), confidence: decimalString(scaled(item.confidence), SCALE),
    quality: item.quality, as_of_date: item.as_of_date, source_ids: item.source_ids, definition: item.definition,
  }]));
  return {
    candidate_id: row.candidate_id, horizon: row.horizon, model_version: MODEL_VERSION, status: Object.values(valid).some(item => item.quality === "PROVISIONAL") ? "PROVISIONAL" : "SCORED",
    score: fixedHundredths(scoreHundredths), unrounded_score: decimalString(numerator, denominator), score_is_probability: false,
    score_band: band, research_action: Object.values(valid).some(item => item.quality === "PROVISIONAL") ? "REVIEW_PROVISIONAL" : action,
    confidence, completeness: "1.00", factor_contributions: factorContributions, factor_weights: factorWeights,
    factor_evidence: factorEvidence, normalization_profiles: Object.fromEntries(Object.entries(valid).map(([name, item]) => [name, item.normalization_profile])),
    factor_source_ids: Object.fromEntries(Object.entries(valid).map(([name, item]) => [name, item.source_ids])), as_of: asOf,
  };
}

function rankRows(rows: Scored[]): Scored[] {
  const groups = new Map<string, Scored[]>();
  const ranked: Scored[] = rows.filter(row => !["SCORED", "PROVISIONAL"].includes(row.status)).map(row => ({ ...row, rank_within_horizon: null, score_difference_to_next: null, ranking_status: "NOT_RANKED", ranking_reason: row.reason ?? "NOT_SCOREABLE" }));
  for (const row of rows.filter(item => ["SCORED", "PROVISIONAL"].includes(item.status))) {
    const key = `${row.horizon}|${row.model_version}|${row.as_of}`;
    groups.set(key, [...(groups.get(key) ?? []), row]);
  }
  for (const key of [...groups.keys()].sort()) {
    const group = groups.get(key)!;
    const ids = group.map(row => row.candidate_id);
    if (new Set(ids).size !== ids.length) {
      ranked.push(...group.map(row => ({ ...row, rank_within_horizon: null, ranking_status: "NOT_COMPARABLE", ranking_reason: "DUPLICATE_CANDIDATE_ID" })));
      continue;
    }
    const fingerprints = new Set(group.map(row => JSON.stringify([
      Object.entries(row.normalization_profiles ?? {}).sort(([a], [b]) => a.localeCompare(b)),
      Object.entries(row.factor_evidence ?? {}).map(([name, evidence]) => [name, evidence.definition]).sort(([a], [b]) => String(a).localeCompare(String(b))),
    ])));
    if (fingerprints.size > 1) {
      ranked.push(...group.map(row => ({ ...row, rank_within_horizon: null, ranking_status: "NOT_COMPARABLE", ranking_reason: "INCOMPATIBLE_NORMALIZATION_OR_FACTOR_DEFINITION" })));
      continue;
    }
    group.sort((a, b) => {
      const left = BigInt(String(a.unrounded_score).replace(".", ""));
      const right = BigInt(String(b.unrounded_score).replace(".", ""));
      return left === right ? a.candidate_id.localeCompare(b.candidate_id) : left > right ? -1 : 1;
    });
    group.forEach((row, index) => {
      let difference: string | null = null;
      if (index + 1 < group.length) {
        const current = scoreToTenDecimalUnits(String(row.unrounded_score));
        const next = scoreToTenDecimalUnits(String(group[index + 1].unrounded_score));
        difference = fixedThousandths(roundHalfUp((current - next) * 1000n, 10n ** 10n));
      }
      ranked.push({ ...row, rank_within_horizon: index + 1, score_difference_to_next: difference, ranking_status: "COMPARABLE" });
    });
  }
  return ranked;
}

function scoreToTenDecimalUnits(value: string) {
  const [whole, fraction = ""] = value.split(".");
  return BigInt(whole) * 10n ** 10n + BigInt((fraction + "0000000000").slice(0, 10));
}

function fixedThousandths(value: bigint) { return `${value / 1000n}.${(value % 1000n).toString().padStart(3, "0")}`; }

export function calculateOpportunityScores(input: z.infer<typeof opportunityScoreInputSchema>) {
  const parsed = opportunityScoreInputSchema.parse(input);
  const scored = parsed.rows.map(row => scoreOne(row as ScoreInput, parsed.as_of));
  return { model_version: MODEL_VERSION, as_of: parsed.as_of, scores: rankRows(scored), source: "deterministic_runtime_calculation; supplied_factor_evidence_only", score_is_probability: false };
}
