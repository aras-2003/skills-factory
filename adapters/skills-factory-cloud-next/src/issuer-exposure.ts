/** Deterministic look-through over explicit caller supplied portfolio fixtures. */
export type IssuerExposureInput = {
  as_of: string;
  base_currency: string;
  portfolio_id: string;
  portfolio_value_pln?: number;
  scenario_positions?: IssuerExposureInput["positions"];
  factor_shocks?: Array<{ factor: string; shock_pct: number; scenario_id: string }>;
  positions: Array<{
    position_id: string; account_id: string; instrument_id: string; isin: string; share_class: string;
    instrument_type: "equity" | "fund"; weight_pct: number; market_value_pln?: number; issuer_id?: string; issuer_name?: string;
    source_id: string; source_uri: string; published_at: string; retrieved_at: string; factors?: string[];
  }>;
  fund_snapshots: Array<{
    instrument_id: string; as_of: string; published_at: string; retrieved_at: string; source_id: string; source_uri: string;
    completeness: "COMPLETE" | "PARTIAL"; coverage_pct: number;
    constituents: Array<{ issuer_id: string; issuer_name: string; isin: string; share_class: string; weight_pct: number; factors: string[] }>;
  }>;
  previous_snapshot?: { method: string; portfolio_id: string; base_currency: string; as_of: string; status: string; source_coverage_pct: number; decomposition_complete: boolean; issuers: Array<{ issuer_id: string; known_minimum_total_pct: number }> };
};

const dateOk = (value: string) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
};
const pct = (n: number) => Math.round(n * 1e6) / 1e6;
type IssuerExposureResult = {
  method: string;
  status: string;
  source_coverage_pct: number;
  decomposition_complete: boolean;
  issuers: Array<{ issuer_id: string; direct_weight_pct: number; lookthrough_min_pct: number; known_minimum_total_pct: number }>;
  overlapping_factor_views: Array<{ factor: string; exposure_pct: number; overlap_allowed: boolean }>;
  concentration: { completeness: string };
};

export function calculateIssuerExposure(input: IssuerExposureInput): IssuerExposureResult {
  if (!dateOk(input.as_of)) throw new Error("as_of must be an ISO calendar date");
  if (!input.portfolio_id.trim() || !input.base_currency.trim()) throw new Error("portfolio_id and base_currency are required");
  if (input.portfolio_value_pln !== undefined && (!Number.isFinite(input.portfolio_value_pln) || input.portfolio_value_pln <= 0 || input.base_currency !== "PLN")) throw new Error("portfolio_value_pln requires a positive value and PLN base currency");
  if (input.factor_shocks?.some(s => !s.factor.trim() || !s.scenario_id.trim() || !Number.isFinite(s.shock_pct) || s.shock_pct < -100 || s.shock_pct > 100) || (input.factor_shocks && new Set(input.factor_shocks.map(s => s.factor)).size !== input.factor_shocks.length)) throw new Error("factor shocks require unique factors and finite shocks between -100% and 100%");
  const positionIds = new Set<string>();
  const snapshots = new Map<string, IssuerExposureInput["fund_snapshots"][number]>();
  for (const s of input.fund_snapshots) {
    if (snapshots.has(s.instrument_id)) throw new Error(`duplicate fund snapshot: ${s.instrument_id}`);
    if (!dateOk(s.as_of) || !dateOk(s.published_at) || !dateOk(s.retrieved_at) || s.as_of > input.as_of || s.published_at > input.as_of || s.retrieved_at > input.as_of || !/^https:\/\//.test(s.source_uri)) throw new Error("fund snapshot has invalid or future provenance date or source URI");
    if (s.coverage_pct < 0 || s.coverage_pct > 100 || s.constituents.some(c => c.weight_pct < 0 || c.weight_pct > 100)) throw new Error("weights and coverage_pct must be between 0 and 100");
    if (s.completeness === "COMPLETE" && (s.coverage_pct !== 100 || Math.abs(s.constituents.reduce((sum, c) => sum + c.weight_pct, 0) - 100) > 1e-4)) throw new Error("COMPLETE fund snapshots require constituent weights and coverage to total 100%");
    if (s.constituents.reduce((sum, c) => sum + c.weight_pct, 0) > s.coverage_pct + 1e-6) throw new Error("constituent weights cannot exceed declared coverage");
    snapshots.set(s.instrument_id, s);
  }
  let positionWeightTotal = 0;
  for (const p of input.positions) {
    if (positionIds.has(p.position_id)) throw new Error(`duplicate position_id: ${p.position_id}`);
    positionIds.add(p.position_id);
    if (!p.position_id || !p.account_id || !p.instrument_id || !p.isin || !p.share_class || !p.source_id || !/^https:\/\//.test(p.source_uri)) throw new Error("positions require account, instrument, ISIN, share class and source identity");
    if (!dateOk(p.published_at) || !dateOk(p.retrieved_at) || p.published_at > input.as_of || p.retrieved_at > input.as_of) throw new Error("position has invalid or future provenance date");
    if (p.weight_pct < 0 || p.weight_pct > 100) throw new Error("position weight_pct must be between 0 and 100");
    if (p.market_value_pln !== undefined && (!Number.isFinite(p.market_value_pln) || p.market_value_pln < 0)) throw new Error("market_value_pln must be finite and nonnegative");
    if (input.portfolio_value_pln !== undefined && (p.market_value_pln === undefined || Math.abs(p.market_value_pln - input.portfolio_value_pln * p.weight_pct / 100) > Math.max(1, input.portfolio_value_pln * 0.0001))) throw new Error("market_value_pln must reconcile with weight_pct and portfolio_value_pln");
    positionWeightTotal += p.weight_pct;
    if (p.instrument_type === "equity" && (!p.issuer_id || !p.issuer_name)) throw new Error("direct equity positions require explicit issuer_id and issuer_name");
  }
  if (positionWeightTotal > 100 + 1e-6) throw new Error("portfolio position weights cannot exceed 100%");

  const issuerRows = new Map<string, { issuer_id: string; issuer_name: string; direct_weight_pct: number; lookthrough_min_pct: number; factors: Set<string>; sources: Set<string>; instruments: Set<string>; weight_evidence: Array<Record<string, unknown>> }>();
  const factorWeights = new Map<string, number>();
  const fundRows: Array<Record<string, unknown>> = [];
  let portfolioCoverage = 0;
  let decompositionComplete = Math.abs(positionWeightTotal - 100) <= 1e-6;
  const decompositionReasons = new Set<string>();
  if (!decompositionComplete) decompositionReasons.add("PORTFOLIO_POSITION_WEIGHT_UNDER_100");
  const add = (issuerId: string, name: string, amount: number, kind: "direct" | "fund", factors: string[], source: string, uri: string, instrument: string, isin: string, shareClass: string, account: string, asOf: string, publishedAt: string, retrievedAt: string) => {
    const row = issuerRows.get(issuerId) ?? { issuer_id: issuerId, issuer_name: name, direct_weight_pct: 0, lookthrough_min_pct: 0, factors: new Set<string>(), sources: new Set<string>(), instruments: new Set<string>(), weight_evidence: [] };
    if (kind === "direct") row.direct_weight_pct += amount;
    else row.lookthrough_min_pct += amount;
    factors.forEach(factor => factorWeights.set(factor, (factorWeights.get(factor) ?? 0) + amount));
    row.weight_evidence.push({ contribution_pct: pct(amount), basis: kind, account_id: account, instrument_id: instrument, isin, share_class: shareClass, as_of: asOf, published_at: publishedAt, retrieved_at: retrievedAt, freshness: input.as_of > retrievedAt ? "STALE_BY_DATE" : "CURRENT_AS_OF_DATE", source_id: source, source_uri: uri });
    factors.forEach(f => row.factors.add(f)); row.sources.add(source); row.instruments.add(instrument); issuerRows.set(issuerId, row);
  };

  for (const p of input.positions) {
    if (p.instrument_type === "equity") {
      add(p.issuer_id!, p.issuer_name!, p.weight_pct, "direct", p.factors ?? [], p.source_id, p.source_uri, p.instrument_id, p.isin, p.share_class, p.account_id, input.as_of, p.published_at, p.retrieved_at);
      portfolioCoverage += p.weight_pct;
      continue;
    }
    const snapshot = snapshots.get(p.instrument_id);
    if (!snapshot) { decompositionComplete = false; decompositionReasons.add("FUND_SNAPSHOT_MISSING"); fundRows.push({ instrument_id: p.instrument_id, account_id: p.account_id, isin: p.isin, share_class: p.share_class, source_coverage_pct: 0, decomposition: "MISSING", unknown_weight_pct: p.weight_pct }); continue; }
    const partial = snapshot.completeness !== "COMPLETE";
    if (partial) decompositionReasons.add("FUND_SNAPSHOT_PARTIAL");
    const covered = p.weight_pct * snapshot.coverage_pct / 100;
    const mappedConstituentPct = snapshot.constituents.reduce((sum, c) => sum + c.weight_pct, 0);
    const unmappedInCoveredPct = Math.max(0, snapshot.coverage_pct - mappedConstituentPct);
    portfolioCoverage += covered;
    decompositionComplete &&= !partial;
    for (const c of snapshot.constituents) add(c.issuer_id, c.issuer_name, p.weight_pct * c.weight_pct / 100, "fund", c.factors, snapshot.source_id, snapshot.source_uri, p.instrument_id, c.isin, c.share_class, p.account_id, snapshot.as_of, snapshot.published_at, snapshot.retrieved_at);
    fundRows.push({ instrument_id: p.instrument_id, account_id: p.account_id, isin: p.isin, share_class: p.share_class, market_value_pln: p.market_value_pln ?? null, source_id: snapshot.source_id, source_uri: snapshot.source_uri, source_as_of: snapshot.as_of, published_at: snapshot.published_at, retrieved_at: snapshot.retrieved_at, freshness: input.as_of > snapshot.retrieved_at ? "STALE_BY_DATE" : "CURRENT_AS_OF_DATE", source_coverage_pct: snapshot.coverage_pct, decomposition: snapshot.completeness, covered_portfolio_weight_pct: pct(covered), unmapped_in_covered_portfolio_weight_pct: pct(p.weight_pct * unmappedInCoveredPct / 100), unknown_weight_pct: pct(p.weight_pct * (100 - mappedConstituentPct) / 100) });
  }

  const issuerList = [...issuerRows.values()].map(r => ({ issuer_id: r.issuer_id, issuer_name: r.issuer_name, direct_weight_pct: pct(r.direct_weight_pct), lookthrough_min_pct: pct(r.lookthrough_min_pct), known_minimum_total_pct: pct(r.direct_weight_pct + r.lookthrough_min_pct), factors: [...r.factors].sort(), source_ids: [...r.sources].sort(), instrument_ids: [...r.instruments].sort(), weight_evidence: r.weight_evidence })).sort((a, b) => b.known_minimum_total_pct - a.known_minimum_total_pct || a.issuer_id.localeCompare(b.issuer_id));
  const etfs = [...new Map(input.positions.filter(p => p.instrument_type === "fund").map(p => [p.instrument_id, p])).values()];
  const overlap = [] as Array<Record<string, unknown>>;
  for (let i = 0; i < etfs.length; i++) for (let j = i + 1; j < etfs.length; j++) {
    const a = snapshots.get(etfs[i].instrument_id), b = snapshots.get(etfs[j].instrument_id);
    if (!a || !b) { overlap.push({ instrument_a: etfs[i].instrument_id, instrument_b: etfs[j].instrument_id, status: "NOT_COMPUTED_MISSING_SOURCE" }); continue; }
    const am = new Map<string, number>(), bm = new Map<string, number>();
    for (const c of a.constituents) am.set(c.issuer_id, (am.get(c.issuer_id) ?? 0) + c.weight_pct);
    for (const c of b.constituents) bm.set(c.issuer_id, (bm.get(c.issuer_id) ?? 0) + c.weight_pct);
    const shared = [...am.keys()].filter(id => bm.has(id));
    const sharedMin = shared.reduce((n, id) => n + Math.min(am.get(id)!, bm.get(id)!), 0);
    overlap.push({ instrument_a: etfs[i].instrument_id, instrument_b: etfs[j].instrument_id, status: a.completeness === "COMPLETE" && b.completeness === "COMPLETE" ? "COMPLETE" : "PARTIAL_MINIMUM", shared_issuer_count: shared.length, shared_weight_pct_of_fund_a_min: pct(sharedMin), shared_weight_pct_of_fund_b_min: pct(sharedMin), shared_issuer_ids: shared.sort() });
  }
  const comparison = !input.previous_snapshot ? { status: "NOT_REQUESTED", deltas: [] } : (() => {
    const previous = input.previous_snapshot!;
    const reasons = [
      previous.method !== "issuer-lookthrough-v1" ? "METHOD_MISMATCH" : null,
      previous.portfolio_id !== input.portfolio_id ? "PORTFOLIO_MISMATCH" : null,
      previous.base_currency !== input.base_currency ? "CURRENCY_MISMATCH" : null,
      !dateOk(previous.as_of) || previous.as_of >= input.as_of ? "INVALID_OR_NONPRIOR_AS_OF" : null,
      previous.status !== "COMPLETE" || !previous.decomposition_complete || previous.source_coverage_pct !== 100 || !decompositionComplete || portfolioCoverage < 100 ? "INCOMPLETE_DECOMPOSITION" : null,
    ].filter(Boolean) as string[];
    if (reasons.length) return { status: "NOT_COMPARABLE", reasons, deltas: [] };
    const previousRows = new Map(previous.issuers.map(row => [row.issuer_id, row.known_minimum_total_pct]));
    const currentRows = new Map(issuerList.map(row => [row.issuer_id, row.known_minimum_total_pct]));
    const ids = [...new Set([...previousRows.keys(), ...currentRows.keys()])].sort();
    return { status: "COMPARABLE", previous_as_of: previous.as_of, method: "issuer-lookthrough-v1", deltas: ids.map(issuer_id => ({ issuer_id, previous_weight_pct: pct(previousRows.get(issuer_id) ?? 0), current_weight_pct: pct(currentRows.get(issuer_id) ?? 0), delta_pct_points: pct((currentRows.get(issuer_id) ?? 0) - (previousRows.get(issuer_id) ?? 0)) })) };
  })();
  const stress = {
    status: input.factor_shocks?.length ? "SCENARIO_ONLY" : "NOT_REQUESTED",
    results: (input.factor_shocks ?? []).map(shock => {
      const exposure = factorWeights.get(shock.factor);
      if (exposure === undefined) return { scenario_id: shock.scenario_id, factor: shock.factor, status: "NOT_COMPUTED_UNKNOWN_FACTOR", impact_pct_points: null, impact_pln: null };
      const impact = exposure * shock.shock_pct / 100;
      return { scenario_id: shock.scenario_id, factor: shock.factor, status: decompositionComplete ? "KNOWN_EXPOSURE_SCENARIO" : "PARTIAL_MINIMUM_SCENARIO", exposure_pct: pct(exposure), assumed_shock_pct: shock.shock_pct, impact_pct_points: pct(impact), impact_pln: input.portfolio_value_pln === undefined ? null : pct(impact * input.portfolio_value_pln / 100), probabilities: null };
    }),
    aggregate_result: "NOT_SUMMED_OVERLAPPING_FACTORS",
  };
  const preTradePreview = input.scenario_positions ? (() => {
    const scenario = calculateIssuerExposure({ ...input, positions: input.scenario_positions, scenario_positions: undefined, previous_snapshot: undefined, factor_shocks: undefined });
    const currentById = new Map(issuerList.map(row => [row.issuer_id, row.known_minimum_total_pct]));
    const scenarioById = new Map(scenario.issuers.map(row => [row.issuer_id, row.known_minimum_total_pct]));
    const issuerIds = [...new Set([...currentById.keys(), ...scenarioById.keys()])].sort();
    const currentFactors = new Map([...factorWeights].map(([factor, exposure]) => [factor, exposure]));
    const scenarioFactors = new Map(scenario.overlapping_factor_views.map(row => [row.factor, row.exposure_pct]));
    const factorIds = [...new Set([...currentFactors.keys(), ...scenarioFactors.keys()])].sort();
    return { status: "PREVIEW_ONLY_CALLER_SUPPLIED_POST_TRADE_POSITIONS", scenario_status: scenario.status, issuer_deltas: issuerIds.map(issuer_id => { const delta = (scenarioById.get(issuer_id) ?? 0) - (currentById.get(issuer_id) ?? 0); return { issuer_id, current_weight_pct: pct(currentById.get(issuer_id) ?? 0), scenario_weight_pct: pct(scenarioById.get(issuer_id) ?? 0), delta_pct_points: pct(delta), delta_pln: input.portfolio_value_pln === undefined ? null : pct(delta * input.portfolio_value_pln / 100) }; }), factor_deltas: factorIds.map(factor => ({ factor, current_exposure_pct: pct(currentFactors.get(factor) ?? 0), scenario_exposure_pct: pct(scenarioFactors.get(factor) ?? 0), delta_pct_points: pct((scenarioFactors.get(factor) ?? 0) - (currentFactors.get(factor) ?? 0)), overlapping_non_additive: true })), current_concentration: concentrationSummary(issuerList, decompositionComplete), scenario_concentration: scenario.concentration, position_review_threshold_pct: 8, scenario_issuers_over_review_threshold: scenario.issuers.filter(row => row.known_minimum_total_pct > 8).map(row => row.issuer_id), threshold_is_review_only: true, trades_executed: false };
  })() : { status: "NOT_REQUESTED" };
  const result = {
    method: "issuer-lookthrough-v1",
    status: decompositionComplete ? "COMPLETE" : "PARTIAL_MINIMUM",
    as_of: input.as_of, portfolio_id: input.portfolio_id, base_currency: input.base_currency, portfolio_value_pln: input.portfolio_value_pln ?? null,
    source_coverage_pct: pct(Math.min(100, portfolioCoverage)), decomposition_complete: decompositionComplete, decomposition_reasons: [...decompositionReasons].sort(),
    issuers: issuerList.map(row => ({ ...row, direct_pln: input.portfolio_value_pln === undefined ? null : pct(row.direct_weight_pct * input.portfolio_value_pln / 100), lookthrough_min_pln: input.portfolio_value_pln === undefined ? null : pct(row.lookthrough_min_pct * input.portfolio_value_pln / 100), known_minimum_pln: input.portfolio_value_pln === undefined ? null : pct(row.known_minimum_total_pct * input.portfolio_value_pln / 100) })), funds: fundRows.map(row => ({ ...row, source_covered_value_pln: input.portfolio_value_pln === undefined ? null : pct(Number(row.covered_portfolio_weight_pct ?? 0) / 100 * input.portfolio_value_pln) })), etf_overlap: overlap, snapshot_comparison: comparison, pre_trade_preview: preTradePreview,
    overlapping_factor_views: [...factorWeights].map(([factor, exposure_pct]) => ({ factor, exposure_pct: pct(exposure_pct), overlap_allowed: true })).sort((a, b) => b.exposure_pct - a.exposure_pct),
    stress,
    concentration: decompositionComplete ? { top_3_issuer_weight_pct: pct(issuerList.slice(0, 3).reduce((n, r) => n + r.known_minimum_total_pct, 0)), top_5_issuer_weight_pct: pct(issuerList.slice(0, 5).reduce((n, r) => n + r.known_minimum_total_pct, 0)), top_10_issuer_weight_pct: pct(issuerList.slice(0, 10).reduce((n, r) => n + r.known_minimum_total_pct, 0)), hhi_pct_squared: pct(issuerList.reduce((n, r) => n + r.known_minimum_total_pct ** 2, 0)), effective_issuer_count: pct(10000 / issuerList.reduce((n, r) => n + r.known_minimum_total_pct ** 2, 0)), completeness: "COMPLETE_ISSUER_DECOMPOSITION" } : { top_3_issuer_weight_pct: null, top_5_issuer_weight_pct: null, top_10_issuer_weight_pct: null, hhi_pct_squared: null, effective_issuer_count: null, completeness: "BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION" },
    limitations: ["Input-only preview; no portfolio retrieval or persistence.", "Issuer exposure is counted once per position and fund constituent; sector rows are not accepted.", "Factor views overlap and must not be added together.", "No forecast, probability, recommendation, transaction or policy decision is produced."],
  };
  return result;

function concentrationSummary(issuers: Array<{ known_minimum_total_pct: number }>, complete: boolean) {
  if (!complete) return { status: "BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION", top_3_pct: null, top_5_pct: null, top_10_pct: null, hhi_pct_squared: null, effective_issuer_count: null };
  const values = issuers.map(row => row.known_minimum_total_pct);
  const hhi = values.reduce((total, value) => total + value ** 2, 0);
  return { status: "COMPLETE", top_3_pct: pct(values.slice(0, 3).reduce((a, b) => a + b, 0)), top_5_pct: pct(values.slice(0, 5).reduce((a, b) => a + b, 0)), top_10_pct: pct(values.slice(0, 10).reduce((a, b) => a + b, 0)), hhi_pct_squared: pct(hhi), effective_issuer_count: pct(10000 / hhi) };
}
}
