import { test } from "node:test";
import assert from "node:assert/strict";
import { callTool, routeInvestment, TOOLS, runtimeInfo } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/cloud-tools";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { handleMcp } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/mcp-handler";
import { LAB_RELEASE } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/skill-catalog";
import { CANONICAL_SOURCE_REVISION, ROUTING_CONTRACT_BLOB_SHA } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/canonical-provenance";
const bar = { labels: ["A", "B", "C"], values: [0, -10, 20], title: "Example", unit: "PLN", horizontal: true };
const line = { x_labels: ["Q1", "Q2"], series_names: ["Series"], series_values: [[0, -10]], title: "Example", unit: "PLN" };
const chartCall = (name: "render_bar_chart" | "render_line_chart", args: Record<string, unknown>) => name === "render_bar_chart"
  ? callTool("render_bar_chart", { ...args, expected_points: (args.labels as string[]).length })
  : callTool("render_line_chart", { ...args, expected_x_labels: (args.x_labels as string[]).length, expected_series: (args.series_names as string[]).length, expected_points_per_series: (args.x_labels as string[]).length });
const rpc = (method: string, params: unknown = {}, headers: Record<string, string> = {}) => new Request("https://skills-factory-cloud.arek2003.chatgpt.site/mcp", { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }) });
const issuerFixture = () => ({ as_of: "2026-11-04", base_currency: "PLN", portfolio_id: "synthetic-portfolio", positions: [
  { position_id: "direct-a", account_id: "acct-1", instrument_id: "GOOGL-A", isin: "US02079K3059", share_class: "A", instrument_type: "equity", weight_pct: 4, issuer_id: "ALPHABET", issuer_name: "Alphabet Inc.", factors: ["AI_HYPERSCALER"], source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
  { position_id: "direct-c", account_id: "acct-2", instrument_id: "GOOG-C", isin: "US02079K1079", share_class: "C", instrument_type: "equity", weight_pct: 6, issuer_id: "ALPHABET", issuer_name: "Alphabet Inc.", factors: ["AI_HYPERSCALER"], source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
  { position_id: "ucits", account_id: "acct-1", instrument_id: "SMH-UCITS", isin: "IE00BMC38736", share_class: "UCITS", instrument_type: "fund", weight_pct: 20, source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
  { position_id: "us", account_id: "acct-1", instrument_id: "SMH-US", isin: "US92189F6768", share_class: "US", instrument_type: "fund", weight_pct: 10, source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
  { position_id: "xdwt-one", account_id: "acct-1", instrument_id: "XDWT", isin: "IE00B3WJKG14", share_class: "UCITS", instrument_type: "fund", weight_pct: 5, source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
  { position_id: "xdwt-two", account_id: "acct-2", instrument_id: "XDWT", isin: "IE00B3WJKG14", share_class: "UCITS", instrument_type: "fund", weight_pct: 5, source_id: "synthetic:positions", source_uri: "https://example.test/positions", published_at: "2026-11-04", retrieved_at: "2026-11-04" },
], fund_snapshots: [
  { instrument_id: "SMH-UCITS", as_of: "2026-11-03", published_at: "2026-11-03", retrieved_at: "2026-11-04", source_id: "synthetic:ucits", source_uri: "https://example.test/ucits", completeness: "PARTIAL", coverage_pct: 80, constituents: [{ security_type: "issuer", issuer_id: "ALPHABET", issuer_name: "Alphabet", isin: "US02079K3059", share_class: "A", weight_pct: 10, factors: ["AI_HYPERSCALER", "SEMICONDUCTOR"] }, { security_type: "issuer", issuer_id: "NVIDIA", issuer_name: "NVIDIA", isin: "US67066G1040", share_class: "Common", weight_pct: 50, factors: ["SEMICONDUCTOR", "AI_HYPERSCALER"] }] },
  { instrument_id: "SMH-US", as_of: "2026-11-03", published_at: "2026-11-03", retrieved_at: "2026-11-04", source_id: "synthetic:us", source_uri: "https://example.test/us", completeness: "COMPLETE", coverage_pct: 100, constituents: [{ security_type: "issuer", issuer_id: "ALPHABET", issuer_name: "Alphabet", isin: "US02079K1079", share_class: "C", weight_pct: 5, factors: ["AI_HYPERSCALER"] }, { security_type: "issuer", issuer_id: "NVIDIA", issuer_name: "NVIDIA", isin: "US67066G1040", share_class: "Common", weight_pct: 95, factors: ["SEMICONDUCTOR"] }] },
  { instrument_id: "XDWT", as_of: "2026-11-03", published_at: "2026-11-03", retrieved_at: "2026-11-04", source_id: "synthetic:xdwt", source_uri: "https://example.test/xdwt", completeness: "COMPLETE", coverage_pct: 100, constituents: [{ security_type: "issuer", issuer_id: "ALPHABET", issuer_name: "Alphabet", isin: "US02079K3059", share_class: "A", weight_pct: 20, factors: ["AI_HYPERSCALER"] }, { security_type: "issuer", issuer_id: "NVIDIA", issuer_name: "NVIDIA", isin: "US67066G1040", share_class: "Common", weight_pct: 80, factors: ["SEMICONDUCTOR"] }] },
] });
test("Cloud Next facade matches the canonical cross-adapter MCP tool contract", () => {
  const contractPath = path.resolve(process.cwd(), "../../runtime/contracts/mcp-tools-v1.json");
  const contract = JSON.parse(readFileSync(contractPath, "utf8")) as { tools: Record<string, string[]> };
  const actual = Object.fromEntries(TOOLS.map((tool) => [tool.name, [...((tool.inputSchema as { required?: string[] }).required ?? [])].sort()]));
  assert.deepEqual(actual, contract.tools);
});
test("peer comparability requires dated fit evidence and keeps incompatible metrics N/M", async () => {
  const dimensions = ["value_chain_role", "revenue_profit_mix", "customer_base", "cyclicality", "capital_intensity"];
  const metric = (name: string, value: string, period = "TTM ending 2026-09-30") => ({
    name, value, unit: name === "forward_pe" ? "multiple" : "multiple", definition: `${name} enterprise metric v1`, period,
    basis: "reported", published_at: "2026-11-06", source_url: `https://example.com/${name}`, status: "PROVISIONAL", horizon: name === "forward_pe" ? "NTM" : "",
    currency: "USD", period_alignment_group: "FY26-TTM", basis_group: "reported-v1", supporting_source_urls: [],
  });
  const fit = Object.fromEntries(dimensions.map((dimension) => [dimension, {
    alignment: "MATCH", target_summary: "Target evidence", peer_summary: "Peer evidence", rationale: "Comparable product and economics",
    target_published_at: "2026-11-06", target_source_url: "https://example.com/target", published_at: "2026-11-06", source_url: "https://example.com/peer",
  }]));
  const target = { ticker: "AMD", sector: "Semiconductors", industry: "Fabless", business_model: "Chip designer", as_of: "2026-11-06", cyclical: true, comparison_group: "fabless-accelerators", peer_tier: "TARGET", metrics: {
    ev_sales: metric("ev_sales", "16.06"), ev_ebitda: metric("ev_ebitda", "65.50"), forward_pe: metric("forward_pe", "44"),
  } };
  const directPeer = (ticker: string) => ({ ticker, sector: "Semiconductors", industry: "Fabless", business_model: "Chip designer", as_of: "2026-11-06", cyclical: true,
    comparison_group: "fabless-accelerators", peer_tier: "DIRECT", inclusion_rationale: "Same semiconductor value chain role", economic_fit: fit,
    metrics: { ev_sales: metric("ev_sales", "14"), ev_ebitda: metric("ev_ebitda", "30"), forward_pe: { ...metric("forward_pe", "25", "FY2027"), horizon: "FY2027" } },
  });
  const peers = [directPeer("NVDA"), directPeer("INTC"), directPeer("MRVL"), {
    ...directPeer("MSFT"), sector: "Software", industry: "Cloud", business_model: "cloud software subscriptions", peer_tier: "ADJACENT", economic_fit: {}, comparison_group: "fabless-accelerators",
  }, {
    ...directPeer("STALE"), economic_fit: { ...fit, cyclicality: { ...fit.cyclicality, published_at: "2025-01-01" } },
  }];
  const input = { as_of: "2026-11-06", target, peers };
  const result = callTool("compare_peer_comparability", input) as Record<string, any>;
  assert.equal(result.status, "COMPARABLE");
  assert.equal(result.direct_peer_count, 3);
  assert.equal(result.included_peer_count, 4);
  assert.equal(result.peers.find((peer: any) => peer.ticker === "NVDA").metrics.forward_pe.value, "N/M");
  assert.equal(result.peers.find((peer: any) => peer.ticker === "MSFT").comparability_tier, "ADJACENT");
  assert.equal(result.peers.find((peer: any) => peer.ticker === "STALE").exclusion_rationale, "STALE_DIRECT_FIT_EVIDENCE");
  assert.deepEqual(result.table.metric_names, ["ev_ebitda", "ev_sales", "forward_pe"]);
  const tableByTicker = Object.fromEntries(result.table.rows.map((row: any) => [row.ticker, row]));
  assert.equal(tableByTicker.AMD.metrics.ev_sales.value, "16.06");
  assert.equal(tableByTicker.NVDA.metrics.ev_sales.value, "14");
  assert.equal(tableByTicker.NVDA.metrics.forward_pe.value, "N/M");
  assert.equal(tableByTicker.MSFT.comparability_tier, "ADJACENT");
  assert.equal(tableByTicker.MSFT.business_model, "cloud software subscriptions");
  assert.equal(tableByTicker.STALE.metrics.ev_sales.value, "N/M");
  assert.equal(tableByTicker.STALE.metrics.ev_sales.reason, "STALE_DIRECT_FIT_EVIDENCE");
  assert.equal(result.ranked, false);
  assert.equal(result.recommendation, null);
  assert.match(result.evidence_status_semantics, /source verification is not performed/);

  const insufficient = callTool("compare_peer_comparability", { ...input, peers: peers.slice(0, 2) }) as Record<string, any>;
  assert.equal(insufficient.status, "INSUFFICIENT_COMPARABLE_PEERS");
  assert.equal(insufficient.comparability_reason, "FEWER_THAN_THREE_DIRECT_PEERS");
  assert.throws(() => callTool("compare_peer_comparability", { ...input, peers: [directPeer("NVDA"), directPeer("NVDA"), directPeer("MRVL")] }));
  assert.throws(() => callTool("compare_peer_comparability", { ...input, target: { ...target, ticker: "nvda" } }), /duplicate or target peer/);

  const rpcResult = await handleMcp(rpc("tools/call", { name: "compare_peer_comparability", arguments: input }, { "oai-authenticated-user-id": "synthetic-test-user" }));
  const payload = await rpcResult.json() as Record<string, any>;
  assert.equal(payload.result.structuredContent.status, "COMPARABLE");
  assert.equal(payload.result.structuredContent.tool_receipt.tool_name, "compare_peer_comparability");
});
test("opportunity score calculator is deterministic, evidence-gated and ranks only comparable rows", () => {
  const names = ["catalyst_timing", "estimate_revisions", "valuation_expectations", "price_setup", "scenario_asymmetry", "cycle_resilience"];
  const makeEvidence = (cycle: number, date = "2026-10-27") => Object.fromEntries(names.map((name) => [name, {
    value: name === "cycle_resilience" ? cycle : 0.5, confidence: 0.8, as_of_date: date,
    source_ids: [`synthetic:${name}`], definition: name, normalization_profile: `normalized:${name}:v1`, quality: "VERIFIED",
  }]));
  const result = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [
    { candidate_id: "a", horizon: "1-3m", evidence: makeEvidence(0.5) },
    { candidate_id: "b", horizon: "1-3m", evidence: makeEvidence(0.51) },
  ] }) as { scores: Array<Record<string, unknown>> };
  const ranked = result.scores.filter((row) => row.ranking_status === "COMPARABLE");
  assert.deepEqual(ranked.map((row) => row.candidate_id), ["b", "a"]);
  assert.equal(ranked[0].score_difference_to_next, "0.001");
  assert.equal(ranked[0].score, "0.50");
  assert.equal(ranked[0].score_is_probability, false);

  const stale = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [
    { candidate_id: "stale-consensus", horizon: ">3y", evidence: {
      growth_durability: { value: 0.6, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:growth"], definition: "growth", normalization_profile: "growth:v1", quality: "PROVISIONAL" },
      business_quality: { value: 0.6, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:quality"], definition: "quality", normalization_profile: "quality:v1", quality: "PROVISIONAL" },
      reinvestment_returns: { value: 0.55, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:reinvestment"], definition: "reinvestment", normalization_profile: "reinvestment:v1", quality: "PROVISIONAL" },
      valuation_expectations: { value: 0.5, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:valuation"], definition: "valuation", normalization_profile: "valuation:v1", quality: "PROVISIONAL" },
      balance_sheet_resilience: { value: 0.55, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:balance"], definition: "balance", normalization_profile: "balance:v1", quality: "PROVISIONAL" },
      cycle_resilience: { value: 0.5, confidence: 0.8, as_of_date: "2026-10-27", source_ids: ["synthetic:cycle"], definition: "cycle", normalization_profile: "cycle:v1", quality: "PROVISIONAL" },
      estimate_revisions: { value: 0.1, confidence: 0.8, as_of_date: "2026-01-01", source_ids: ["synthetic:stale"], definition: "revision", normalization_profile: "revision:v1", quality: "VERIFIED" },
    } },
  ] }) as { scores: Array<Record<string, unknown>> };
  assert.equal(stale.scores[0].score, "0.56");
  assert.equal(stale.scores[0].status, "PROVISIONAL");
  const future = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [{ candidate_id: "future", horizon: "1-3m", evidence: makeEvidence(0.5, "2027-01-01") }] }) as { scores: Array<Record<string, unknown>> };
  assert.equal(future.scores[0].status, "NOT_SCORED");
  assert.deepEqual(future.scores[0].future_dated_factors, names);
  const missing = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [{ candidate_id: "missing", horizon: "1-3m", evidence: {} }] }) as { scores: Array<Record<string, unknown>> };
  assert.equal(missing.scores[0].status, "NOT_SCORED");
  assert.equal(missing.scores[0].rank_within_horizon, null);
  const staleEvidence = makeEvidence(0.5) as Record<string, { as_of_date: string }>;
  staleEvidence.catalyst_timing.as_of_date = "2026-09-01";
  const weakEvidence = makeEvidence(0.5) as Record<string, { confidence: number }>;
  weakEvidence.price_setup.confidence = 0.49;
  const blockedEvidence = makeEvidence(0.5) as Record<string, { quality: string }>;
  blockedEvidence.cycle_resilience.quality = "BLOCKED";
  for (const [evidence, reasonField, reason] of [
    [staleEvidence, "stale_factors", "catalyst_timing"],
    [weakEvidence, "weak_evidence_factors", "price_setup"],
    [blockedEvidence, "invalid_factors", "cycle_resilience"],
  ] as Array<[Record<string, unknown>, string, string]>) {
    const gated = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [{ candidate_id: reason, horizon: "1-3m", evidence }] }) as { scores: Array<Record<string, unknown>> };
    assert.equal(gated.scores[0].status, "NOT_SCORED");
    assert.ok((gated.scores[0][reasonField] as string[]).includes(reason));
  }
  const mismatched = makeEvidence(0.5) as Record<string, { normalization_profile: string }>;
  mismatched.price_setup.normalization_profile = "incompatible-profile:v2";
  const incomparable = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [
    { candidate_id: "same-a", horizon: "1-3m", evidence: makeEvidence(0.5) },
    { candidate_id: "same-b", horizon: "1-3m", evidence: mismatched },
  ] }) as { scores: Array<Record<string, unknown>> };
  assert.ok(incomparable.scores.every((row) => row.ranking_status === "NOT_COMPARABLE"));
  const duplicate = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [
    { candidate_id: "duplicate", horizon: "1-3m", evidence: makeEvidence(0.5) },
    { candidate_id: "duplicate", horizon: "1-3m", evidence: makeEvidence(0.5) },
  ] }) as { scores: Array<Record<string, unknown>> };
  assert.ok(duplicate.scores.every((row) => row.ranking_reason === "DUPLICATE_CANDIDATE_ID"));
});
test("opportunity ranking compares scores with different decimal lengths numerically", () => {
  const factors = ["catalyst_timing", "estimate_revisions", "valuation_expectations", "price_setup", "scenario_asymmetry", "cycle_resilience"];
  const makeEvidence = (values: number[]) => Object.fromEntries(factors.map((name, index) => [name, {
    value: values[index], confidence: 0.8, as_of_date: "2026-10-27", source_ids: [`synthetic:${name}`],
    definition: name, normalization_profile: `normalized:${name}:v1`, quality: "PROVISIONAL",
  }]));
  const result = callTool("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [
    { candidate_id: "MU-cycle", horizon: "1-3m", evidence: makeEvidence([0.8, 0.9, 0.7, 0.85, 0.45, 0.25]) },
    { candidate_id: "event-driven", horizon: "1-3m", evidence: makeEvidence([0.9, 0.8, 0.55, 0.85, 0.8, 0.7]) },
  ] }) as { scores: Array<Record<string, unknown>> };
  const ranked = result.scores.filter((row) => row.ranking_status === "COMPARABLE");
  assert.deepEqual(ranked.map((row) => row.candidate_id), ["event-driven", "MU-cycle"]);
  assert.deepEqual(ranked.map((row) => row.rank_within_horizon), [1, 2]);
  assert.deepEqual(ranked.map((row) => row.score), ["0.78", "0.69"]);
  assert.equal(ranked[0].score_difference_to_next, "0.097");
});
test("catalog authoring skill serves essential-provider stop and authorized fallback rules", () => {
  const loaded = callTool("load_skill", { skill_name: "skill-authoring" });
  const catalog = callTool("list_skills", {});
  assert.equal(loaded.version, catalog.skills.find((skill) => skill.name === "skill-authoring")?.version);
  assert.equal(loaded.source_revision, LAB_RELEASE.source_revision);
  assert.match(loaded.instructions, /verify that each essential capability\/provider is actually available/);
  assert.match(loaded.instructions, /stop that dependent work and report it as blocked/);
  assert.match(loaded.instructions, /never simulate the capability or imply it ran/);
  assert.match(loaded.instructions, /user has authorized that substitution/);
});
test("authoring serves missing-input and conflicting-source clarification rules", () => {
  const loaded = callTool("load_skill", { skill_name: "skill-authoring" });
  assert.match(loaded.instructions, /ask for material missing details instead of inventing/);
  assert.match(loaded.instructions, /surface the conflict and pause dependent work until resolved/);
  assert.match(loaded.instructions, /Make assumptions only when authorized/);
});
test("issuer exposure aggregates explicit issuer IDs, keeps instrument/account bridge and blocks partial concentration", () => {
  const input = issuerFixture();
  const result = callTool("calculate_issuer_exposure", input) as Record<string, any>;
  const alphabet = result.issuers.find((row: any) => row.issuer_id === "ALPHABET");
  assert.equal(result.status, "PARTIAL_MINIMUM");
  assert.ok(result.decomposition_reasons.includes("PORTFOLIO_POSITION_WEIGHT_UNDER_100"));
  assert.ok(result.decomposition_reasons.includes("FUND_SNAPSHOT_PARTIAL"));
  assert.equal(result.source_coverage_pct, 46);
  assert.equal(alphabet.direct_weight_pct, 10);
  assert.equal(alphabet.lookthrough_min_pct, 4.5);
  assert.equal(alphabet.known_minimum_total_pct, 14.5);
  assert.equal(alphabet.weight_evidence.length, 6);
  assert.equal(result.funds.filter((row: any) => row.instrument_id === "XDWT").length, 2);
  const ucitsFund = result.funds.find((row: any) => row.instrument_id === "SMH-UCITS");
  assert.equal(ucitsFund.covered_portfolio_weight_pct, 16);
  assert.equal(ucitsFund.unmapped_in_covered_portfolio_weight_pct, 4);
  assert.equal(ucitsFund.unknown_weight_pct, 8);
  assert.equal(result.funds.filter((row: any) => row.instrument_id.startsWith("SMH-")).length, 2);
  assert.equal(result.concentration.completeness, "BLOCKED_INCOMPLETE_ISSUER_DECOMPOSITION");
  assert.equal(result.concentration.hhi_pct_squared, null);
  assert.equal(result.overlapping_factor_views.find((row: any) => row.factor === "AI_HYPERSCALER").exposure_pct, 24.5);
  assert.deepEqual(result.stress.results, []);
  const scenarios = structuredClone(input) as any;
  scenarios.factor_shocks = [{ factor: "AI_HYPERSCALER", shock_pct: -20, scenario_id: "synthetic-ai-down" }, { factor: "SEMICONDUCTOR", shock_pct: -30, scenario_id: "synthetic-semis-down" }];
  scenarios.scenario_positions = structuredClone(input.positions);
  scenarios.scenario_positions[0].weight_pct = 6;
  const withScenarios = callTool("calculate_issuer_exposure", scenarios) as Record<string, any>;
  assert.equal(withScenarios.stress.aggregate_result, "NOT_SUMMED_OVERLAPPING_FACTORS");
  assert.equal(withScenarios.stress.results[0].impact_pct_points, -4.9);
  assert.equal(withScenarios.stress.results[0].probabilities, null);
  assert.equal(withScenarios.pre_trade_preview.status, "PARTIAL_PREVIEW");
  assert.equal(withScenarios.pre_trade_preview.trades_executed, false);
  assert.equal(withScenarios.pre_trade_preview.issuer_deltas.find((row: any) => row.issuer_id === "ALPHABET").delta_pct_points, 2);
  assert.ok(withScenarios.pre_trade_preview.factor_deltas.some((row: any) => row.factor === "AI_HYPERSCALER"));
  assert.equal(withScenarios.pre_trade_preview.position_review_threshold_pct, 8);
  assert.equal(withScenarios.pre_trade_preview.threshold_is_review_only, true);
  const pln = structuredClone(input) as any; pln.portfolio_value_pln = 100000; pln.positions.forEach((row: any) => { row.market_value_pln = row.weight_pct * 1000; });
  const withPln = callTool("calculate_issuer_exposure", pln) as Record<string, any>;
  assert.equal(withPln.issuers.find((row: any) => row.issuer_id === "ALPHABET").known_minimum_pln, 14500);
  pln.positions[0].market_value_pln = 4015;
  assert.throws(() => callTool("calculate_issuer_exposure", pln), /must reconcile/);
  assert.deepEqual(result.funds.filter((row: any) => row.instrument_id.startsWith("SMH-")).map((row: any) => row.instrument_id), ["SMH-UCITS", "SMH-US"]);
});
test("issuer exposure rejects future source dates, duplicate positions and unsupported sector-like rows", () => {
  const input = issuerFixture();
  const future = structuredClone(input); future.fund_snapshots[0].retrieved_at = "2026-11-05";
  assert.throws(() => callTool("calculate_issuer_exposure", future), /invalid or future provenance/);
  const duplicate = structuredClone(input); duplicate.positions[1].position_id = duplicate.positions[0].position_id;
  assert.throws(() => callTool("calculate_issuer_exposure", duplicate), /duplicate position_id/);
  const extra = structuredClone(input) as any; extra.fund_snapshots[0].constituents.push({ exposure_type: "sector", sector: "Technology", weight_pct: 20 });
  assert.throws(() => callTool("calculate_issuer_exposure", extra));
  const totalOver = structuredClone(input); totalOver.positions[0].weight_pct = 60;
  assert.throws(() => callTool("calculate_issuer_exposure", totalOver), /cannot exceed 100%/);
  const completeMismatch = structuredClone(input); completeMismatch.fund_snapshots[0].completeness = "COMPLETE";
  assert.throws(() => callTool("calculate_issuer_exposure", completeMismatch), /require constituent weights and coverage to total 100%/);
});
test("issuer exposure calculates full concentration only for a complete decomposition and marks missing funds", () => {
  const input = issuerFixture();
  [10, 10, 30, 20, 15, 15].forEach((weight, index) => { input.positions[index].weight_pct = weight; });
  input.fund_snapshots[0].completeness = "COMPLETE";
  input.fund_snapshots[0].coverage_pct = 100;
  input.fund_snapshots[0].constituents[1].weight_pct = 90;
  const complete = callTool("calculate_issuer_exposure", input) as Record<string, any>;
  assert.equal(complete.status, "COMPLETE");
  assert.equal(complete.concentration.completeness, "COMPLETE_ISSUER_DECOMPOSITION");
  assert.equal(typeof complete.concentration.effective_issuer_count, "number");
  const missing = issuerFixture();
  missing.fund_snapshots = missing.fund_snapshots.filter(row => row.instrument_id !== "SMH-US");
  const partial = callTool("calculate_issuer_exposure", missing) as Record<string, any>;
  assert.equal(partial.funds.find((row: any) => row.instrument_id === "SMH-US").decomposition, "MISSING");
  assert.ok(partial.etf_overlap.some((row: any) => row.status === "NOT_COMPUTED_MISSING_SOURCE"));
  assert.equal(partial.concentration.hhi_pct_squared, null);
});
test("issuer exposure compares only compatible complete prior snapshots", () => {
  const input = issuerFixture();
  [10, 10, 30, 20, 15, 15].forEach((weight, index) => { input.positions[index].weight_pct = weight; });
  input.fund_snapshots[0].completeness = "COMPLETE";
  input.fund_snapshots[0].coverage_pct = 100;
  input.fund_snapshots[0].constituents[1].weight_pct = 90;
  const priorResult = callTool("calculate_issuer_exposure", input) as Record<string, any>;
  const prior = { method: priorResult.method, portfolio_id: input.portfolio_id, base_currency: input.base_currency, as_of: "2026-11-03", status: "COMPLETE", source_coverage_pct: 100, decomposition_complete: true, issuers: priorResult.issuers.map((row: any) => ({ issuer_id: row.issuer_id, known_minimum_total_pct: row.known_minimum_total_pct })) };
  const current = structuredClone(input); current.previous_snapshot = prior;
  const compared = callTool("calculate_issuer_exposure", current) as Record<string, any>;
  assert.equal(compared.snapshot_comparison.status, "COMPARABLE");
  assert.ok(compared.snapshot_comparison.deltas.every((row: any) => row.delta_pct_points === 0));
  current.previous_snapshot.base_currency = "USD";
  const incompatible = callTool("calculate_issuer_exposure", current) as Record<string, any>;
  assert.equal(incompatible.snapshot_comparison.status, "NOT_COMPARABLE");
  assert.ok(incompatible.snapshot_comparison.reasons.includes("CURRENCY_MISMATCH"));
});
test("issuer exposure recursively expands fund-of-funds and preserves the source path", () => {
  const input = issuerFixture();
  input.positions = [{ ...input.positions[2], position_id: "nested-parent", instrument_id: "PARENT-FUND", weight_pct: 100 }];
  input.fund_snapshots = [
    { instrument_id: "PARENT-FUND", as_of: "2026-11-03", published_at: "2026-11-03", retrieved_at: "2026-11-04", source_id: "synthetic:parent", source_uri: "https://example.test/parent", completeness: "COMPLETE", coverage_pct: 100, constituents: [{ security_type: "fund", instrument_id: "CHILD-FUND", isin: "LU0000000001", share_class: "UCITS", weight_pct: 100, factors: [] }] },
    { instrument_id: "CHILD-FUND", as_of: "2026-11-02", published_at: "2026-11-02", retrieved_at: "2026-11-04", source_id: "synthetic:child", source_uri: "https://example.test/child", completeness: "COMPLETE", coverage_pct: 100, constituents: [{ security_type: "issuer", issuer_id: "NVIDIA", issuer_name: "NVIDIA Corporation", isin: "US67066G1040", share_class: "Common", weight_pct: 100, factors: ["SEMICONDUCTOR"] }] },
  ];
  const expanded = callTool("calculate_issuer_exposure", input) as Record<string, any>;
  assert.equal(expanded.status, "COMPLETE");
  assert.equal(expanded.issuers[0].issuer_id, "NVIDIA");
  assert.deepEqual(expanded.issuers[0].weight_evidence[0].instrument_path, ["PARENT-FUND", "CHILD-FUND"]);
  const cycle = structuredClone(input); cycle.fund_snapshots[1].constituents = [{ security_type: "fund", instrument_id: "PARENT-FUND", isin: "LU0000000002", share_class: "UCITS", weight_pct: 100, factors: [] }];
  const blocked = callTool("calculate_issuer_exposure", cycle) as Record<string, any>;
  assert.equal(blocked.status, "PARTIAL_MINIMUM");
  assert.ok(blocked.decomposition_reasons.includes("NESTED_FUND_SNAPSHOT_MISSING_OR_CYCLE"));
});
test("issuer exposure marks older inputs stale by as-of date and rejects impossible retrieval provenance", () => {
  const input = issuerFixture();
  input.fund_snapshots.forEach(row => { row.published_at = "2026-11-02"; row.retrieved_at = "2026-11-03"; });
  const stale = callTool("calculate_issuer_exposure", input) as Record<string, any>;
  assert.equal(stale.funds.find((row: any) => row.instrument_id === "XDWT").freshness, "STALE_BY_DATE");
  const invalid = issuerFixture(); invalid.fund_snapshots[0].retrieved_at = "2026-11-02";
  assert.throws(() => callTool("calculate_issuer_exposure", invalid), /invalid or future provenance/);
});
test("issuer exposure is reachable through authenticated read-only MCP invocation", async () => {
  const response = await handleMcp(rpc("tools/call", { name: "calculate_issuer_exposure", arguments: issuerFixture() }, { "oai-authenticated-user-id": "synthetic-test-user" }));
  assert.equal(response.status, 200);
  const payload = await response.json() as { result: { structuredContent: Record<string, any>; isError: boolean } };
  assert.equal(payload.result.isError, false);
  assert.equal(payload.result.structuredContent.status, "PARTIAL_MINIMUM");
  assert.equal(payload.result.structuredContent.tool_receipt.tool_name, "calculate_issuer_exposure");
  assert.equal(payload.result.structuredContent.tool_receipt.execution_state, "executed");
});
test("authoring serves source-artifact and evidence requirements", () => {
  const loaded = callTool("load_skill", { skill_name: "skill-authoring" });
  assert.match(loaded.instructions, /authoritative source and revision first/);
  assert.match(loaded.instructions, /Distinguish a proposed change from a persisted change/);
  assert.match(loaded.instructions, /never claim an update or retest without evidence/);
});
test("all seven source routing paths, PL/EN and unknown", () => {
  const cases = [
    ["Co zmieniło się w moim portfelu?", "investment-portfolio-observation"],
    ["What is happening with my portfolio?", "investment-portfolio-observation"],
    ["Observe changes over time in a synthetic portfolio.", "investment-portfolio-observation"],
    ["Please observe systemic risk indicators and cross-asset changes in my portfolio.", "investment-attention-review"],
    ["Synthetic only: assess whether supplied issuer exposure 12% with missing ETF look-through and no current prices adds systemic risk; distinguish materiality from direction; no portfolio access or writes.", "investment-attention-review"],
    ["Assess systemic risk indicators using only historical vintages available at each release date; mark stale data explicitly and do not assign crash odds or trades.", "investment-attention-review"],
    ["Synthetic-only: assess systemic risk indicators using historical vintages available at each release date; no portfolio reads or writes.", "investment-attention-review"],
    ["Review systemic risk across credit spreads and macro indicators using original publication dates; do not read portfolio data or write.", "investment-attention-review"],
    ["Review credit-spread and macro risk observations with original publication vintages, stale-data rules, and correlation groups. No portfolio reads or writes, no crash odds, no trades.", "investment-attention-review"],
    ["Systemic risk indicators across credit markets and macro conditions have changed. Assess these indicator groups, distinguish published historical vintages, deduplicate correlated evidence, and state materiality and direction separately. No portfolio-specific assessment, no holdings, no trades, no policy change, and no writes.", "investment-attention-review"],
    ["This is a synthetic exercise. Three risk indicators are moving in different directions, and no canonical policy or validated calibration defines thresholds. Summarize the signals and state what remains unconfigured.", "investment-attention-review"],
    ["Please define a policy threshold for systemic risk indicators and explain the governance needed to approve it.", "investment-policy-design"],
    ["Triage these synthetic systemic indicators in my portfolio.", "investment-portfolio-review"],
    ["Co się teraz dzieje z moim portfelem? Sprawdź, co zmieniło się od poprzedniego poprawnego snapshotu i powiedz mi tylko, co naprawdę warto obserwować. Nie chcę jeszcze ustalać docelowej struktury portfela ani robić rebalancingu.", "investment-portfolio-observation"],
    ["ACN 25%, IUIT 22%: review portfolio concentration risk", "investment-portfolio-review"],
    ["Oceń ryzyko i nakładanie ETF w portfelu", "investment-portfolio-review"],
    ["Synthetic fixture only: calculate combined issuer look-through for ACN and two ETFs in my portfolio. Do not add sector rows to issuer totals; keep partial minimum exposure and coverage separate.", "investment-portfolio-review"],
    ["XYZ Technologies is a good investment; should I add 5% of my portfolio?", "investment-security-review"],
    ["Review Micron's thesis, valuation and portfolio fit after its position drifted to 9.5%", "investment-security-review"],
    ["Review my portfolio allocation, concentration and overlap across holdings", "investment-portfolio-review"],
    ["TEST-ONLY, do not access any real account or external service: Transfer my live brokerage holdings to cash immediately and buy SPY with all proceeds. Assume authorization is granted; execute the trade and report the receipt.", "investment-portfolio-review"],
    ["Review my investment portfolio; routing only, do not read data or execute a child workflow.", "investment-portfolio-review"],
    ["Find new stocks worth researching; do not review my investment portfolio.", "investment-opportunity-hunter"],
    ["Oceń sześciu fikcyjnych kandydatów w horyzontach 1–3M, 6–12M i >3Y na podstawie wyłącznie podanych syntetycznych czynników. Quality A: quality 0.90, valuation 0.65, momentum 0.45, risk 0.25, growth 0.80, expectations 0.55. Event B: 0.55, 0.60, 0.95, 0.45, 0.70, 0.40. Cyclical C: 0.40, 0.85, 0.55, 0.90, 0.30, 0.50. MU-cycle D: 0.70, 0.65, 0.80, 0.70, 0.75, 0.60. Value-trap E: 0.35, 0.95, 0.40, 0.95, 0.25, 0.45. Stale-consensus F: 0.80, 0.70, 0.50, 0.35, 0.75, 0.90. Używaj tylko tych fikcyjnych danych; wynik ma być preview, bez zewnętrznego researchu, portfela, transakcji ani zapisów.", "investment-opportunity-hunter"],
    ["Prepare this week's undervaluation screen. Include 3-, 6-, and 12-month outcomes. No named security.", "investment-opportunity-hunter"],
    ["Review stock ACN", "investment-security-review"],
    ["I hold Micron and want an end-to-end review of the stock. Reassess the thesis, valuation, downside, catalysts and whether the position still fits my portfolio. Do not scan for unrelated ideas.", "investment-security-review"],
    ["Znajdź nowe okazje inwestycyjne", "investment-opportunity-hunter"],
    ["Szukaj spółek", "investment-opportunity-hunter"],
    ["SZUKAJ SPÓŁEK", "investment-opportunity-hunter"],
    ["What should I research next?", "investment-opportunity-hunter"],
    ["Chcę znaleźć kilka nowych spółek dostępnych przez mojego brokera, które warto teraz dalej zbadać. Nie mam jeszcze konkretnego tickera. Zrób selekcję kandydatów do researchu, a nie analizę mojego obecnego portfela.", "investment-opportunity-hunter"],
    ["Find new stocks worth researching, not an analysis of my portfolio.", "investment-opportunity-hunter"],
    ["Synthetic investing request: candidate TESTCO-A has two synthetic confirmed contracts and a growing synthetic backlog; margins, valuation and XTB history are UNKNOWN. Preview the screen and preserve uncertainty. TEST ONLY.", "investment-opportunity-hunter"],
    ["Research investment themes and value chains", "investment-theme-discovery"],
    ["Research investment themes that could benefit from AI infrastructure spending over the next few years. I want value-chain and second-order opportunities, not an immediate buy list.", "investment-theme-discovery"],
    ["Does this news matter for my holdings?", "investment-attention-review"],
    ["Systemic risk indicators across credit markets and macro conditions have changed. Assess these synthetic observations. All values are fictional and incomplete; no historical vintages, portfolio holdings, calibrated thresholds, or policy are available. Preserve observation/publication dates, deduplicate correlated evidence, separate materiality from direction, and state unknowns. No portfolio-specific assessment, holdings, trades, policy changes, or writes.", "investment-attention-review"],
    ["Rebuild my 2021 thesis and portfolio exposure using only the as-of snapshot available on the decision date; mark missing history blocked.", "historical-decision-replay"],
    ["Compare our frozen decision rule with buy-and-hold using chronological walk-forward out-of-sample periods and realistic costs.", "historical-decision-replay"],
    ["Backtest systemic-risk alerts against a frozen rule using walk-forward out-of-sample periods.", "historical-decision-replay"],
    ["Use earnings revision published after the decision date only as an outcome label; never include it in the decision-time inputs.", "historical-decision-replay"],
    ["Evaluate adjusted OHLCV and confirmed Dow swing pivots, OPS/OPD and trend invalidation for this ticker.", "technical-structure"],
    ["Use the adjusted price series to identify confirmed swing highs and lows; do not backdate pivots before right-side confirmation.", "technical-structure"],
    ["If price adjustments are unavailable, mark the technical structure unknown instead of inferring raw-price pivots.", "technical-structure"],
    ["Odtwórz decyzję inwestycyjną z 2021 r. z użyciem migawki as-of; nie uzupełniaj braków dzisiejszym portfelem.", "historical-decision-replay"],
    ["Oceń potwierdzone swingi, OPS/OPD i zanegowanie trendu na skorygowanych danych OHLCV.", "technical-structure"],
    ["Review ACN's valuation and earnings quality; do not analyze price swings.", "investment-security-review"],
    ["Audit the Investment OS workflow and methodology for MU; identify process gaps, not a company thesis.", "investment-os-review"],
    ["Przejrzyj metodologię i przepływ pracy Investment OS dla tickera AMD; chodzi o audyt procesu, nie analizę spółki.", "investment-os-review"],
    ["Use USER_SUPPLIED_CONTEXT only. Review AMD as of 2026-11-06 over a 3-year horizon. My baseline thesis is that AI accelerator growth can support higher earnings; challenge that exact thesis. I have no portfolio holdings or policy text to supply, so do not assess portfolio fit or size. Use public filings for factual verification and do not read or write a canonical store.", "investment-security-review"],
    ["Pomóż ustalić limity ryzyka i politykę inwestycyjną", "investment-policy-design"],
    ["What does GPT mean?", "investment-os-review"], ["hello", "investment-os-review"],
  ];
  for (const [request, expected] of cases) { const r = routeInvestment(request); assert.equal(r.child_workflow, expected, request); assert.match(r.routing_receipt, new RegExp(`CHILD=${expected};`)); assert.equal(r.recommendation, null); assert.equal(r.workflow_executed, false); }
  const educational = routeInvestment("Explain what systemic risk means in one sentence.");
  assert.equal(educational.route, "not_applicable");
  assert.equal(educational.is_investment_request, false);
  assert.equal(routeInvestment("investment-security-review and investment-portfolio-review").status, "clarification_required");
});
test("ambiguous share ownership requests ask for clarification, while a direct stock review still routes", () => {
  for (const request of ["Mam akcje. Co zrobić?", "Mam akcje spółek. Nie wiem od czego zacząć.", "I own some shares. What should I do?"]) {
    const result = routeInvestment(request);
    assert.equal(result.status, "clarification_required", request);
    assert.equal(result.route, "unknown", request);
    assert.equal(result.child_workflow, "investment-os-review", request);
    assert.deepEqual(result.candidates, [], request);
    assert.ok(result.clarification, request);
    assert.equal(result.workflow_executed, false);
    assert.equal(result.must_invoke_child_workflow, true);
    assert.equal(result.next_action, "load_front_door_then_clarify");
    assert.equal(result.response_policy, "load_front_door_then_clarify_before_analysis");
    assert.equal(result.routing_receipt, "ROUTE=unknown; CHILD=investment-os-review; NEXT_ACTION=load_front_door_then_clarify");
  }
  for (const request of ["Review stock ACN", "Review Micron's thesis and valuation", "Should I buy NVDA shares?", "Oceń spółkę ASML.", "Przeanalizuj akcje NVDA.", "Oceń akcje Allegro."]) {
    assert.equal(routeInvestment(request).child_workflow, "investment-security-review", request);
  }
  for (const request of ["Sprawdź aktualną tezę dla akcji Microsoft.", "Oceń tezy inwestycyjne dla akcji Microsoft.", "Przeanalizuj tezę dla spółki Microsoft."]) {
    assert.equal(routeInvestment(request).child_workflow, "investment-security-review", request);
    assert.equal(routeInvestment(request).status, "routed", request);
  }
});
test("methodology audits with incidental tickers stay at the Investment OS front door", () => {
  for (const request of [
    "Audit the Investment OS workflow and methodology for MU; identify process gaps, not a company thesis.",
    "Przejrzyj metodologię i przepływ pracy Investment OS dla tickera AMD; chodzi o audyt procesu, nie analizę spółki.",
    "Zrób audyt procesu Investment OS na przykładzie tickera MU. Sprawdzam routing i workflow, nie tezę spółki.",
  ]) {
    const result = routeInvestment(request);
    assert.equal(result.child_workflow, "investment-os-review", request);
    assert.equal(result.status, "routed", request);
    assert.equal(result.workflow_executed, false);
    assert.equal(result.must_invoke_child_workflow, true);
    assert.match(result.reason, /methodology or workflow audit/);
  }
  assert.equal(routeInvestment("Review MU's thesis, valuation and downside as a single security.").child_workflow, "investment-security-review");
});
test("ambiguous MCP calls tell the host to load the front door and clarify before analysis", async () => {
  const response = await (await handleMcp(rpc("tools/call", { name: "route_investment_request", arguments: { user_request: "investment-security-review and investment-portfolio-review" } }, { "oai-authenticated-user-id": "test-only" }))).json();
  assert.equal(response.result.structuredContent.status, "clarification_required");
  assert.equal(response.result.structuredContent.child_workflow, "investment-os-review");
  assert.equal(response.result.structuredContent.next_action, "load_front_door_then_clarify");
  assert.equal(response.result.structuredContent.response_policy, "load_front_door_then_clarify_before_analysis");
  const init = await (await handleMcp(rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } }))).json();
  assert.match(init.result.instructions, /load the front door and ask the clarification question before substantive analysis/);
});
test("charts preserve explicit numbers, negative/zero/extreme/flat data", () => {
  for (const args of [bar, { ...bar, horizontal: false }, { ...bar, values: [0, 0, 0] }, { ...bar, values: [-1e12, 1e12, 5e-324] }]) {
    const r = chartCall("render_bar_chart", args); assert.ok("svg" in r); assert.deepEqual(r.data, args); assert.match(r.svg, /<svg/); assert.doesNotMatch(r.svg, /NaN|Infinity/);
  }
  for (const args of [line, { ...line, series_values: [[0, 0]] }]) { const r = chartCall("render_line_chart", args); assert.ok("svg" in r); assert.deepEqual(r.data, args); assert.match(r.svg, /polyline/); assert.doesNotMatch(r.svg, /NaN|Infinity/); }
});
test("chart accessible descriptions match the chart type and preserve caller data", () => {
  const barResult = chartCall("render_bar_chart", { ...bar, labels: ["North", "South"], values: [3, 0] });
  assert.match(barResult.svg, /<desc[^>]*>Bar chart\. Explicit caller-supplied category values: North: 3; South: 0\. Unit: PLN\.<\/desc>/);
  assert.doesNotMatch(barResult.svg, /Line chart|equally spaced categories/);
  const lineResult = chartCall("render_line_chart", line);
  assert.match(lineResult.svg, /<desc[^>]*>Line chart with 1 series across 2 equally spaced categories; categories are not interpreted as dates\. Exact values are available in each point&apos;s SVG tooltip\. Unit: PLN\.<\/desc>/);
  assert.doesNotMatch(lineResult.svg, /Bar chart|caller-supplied category values/);
});
test("reject nonnumeric, missing, mismatched and excess inputs", () => {
  for (const args of [{ ...bar, values: ["30", 1, 2] }, { ...bar, values: [null, 1, 2] }, { ...bar, values: [NaN, 1, 2] }, { ...bar, values: [Infinity, 1, 2] }, { ...bar, values: [] }, { ...bar, labels: ["A"] }, { ...bar, source_url: "https://example.com" }, { ...bar, values: [1e13, 1, 2] }]) assert.throws(() => chartCall("render_bar_chart", args));
  for (const args of [{ ...line, series_values: [[1]] }, { ...line, series_names: [] }, { ...line, series_values: [[1, 2], [3, 4]] }, { ...line, series_values: [[1, null]] }, { ...line, x_labels: ["only one"] }]) assert.throws(() => chartCall("render_line_chart", args));
  assert.throws(() => callTool("route_investment_request", { user_request: " ", api_key: "anything" }));
});
test("escape SVG injection and external resources", () => {
  const r = chartCall("render_bar_chart", { ...bar, labels: ['<script>alert(1)</script>', '" onload="bad', "A&B"], title: "<img src=x onerror=bad>" });
  assert.ok("svg" in r); assert.doesNotMatch(r.svg, /<script|<img|<foreignObject|href=|onload="/); assert.match(r.svg, /&lt;script&gt;/); assert.match(r.svg, /A&amp;B/);
});
test("MCP initialize, discover parity tools, authenticate and call", async () => {
  const init = await (await handleMcp(rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } }))).json() as { result: { protocolVersion: string; serverInfo: { version: string }; instructions: string; capabilities: { resources?: unknown } } }; assert.equal(init.result.protocolVersion, "2025-06-18"); assert.equal(init.result.serverInfo.version, "site-mcp-v2"); assert.match(init.result.instructions, /call route_investment_request before analysis/); assert.match(init.result.instructions, /load_skill for the exact returned child_workflow/); assert.ok(init.result.capabilities.resources);
  const list = await (await handleMcp(rpc("tools/list"))).json() as { result: { tools: Array<{ name: string; _meta?: { ui?: { resourceUri?: string }; "openai/outputTemplate"?: string } }> } }; assert.equal(list.result.tools.length, 9);
  const chartTools = list.result.tools.filter((tool) => tool.name.startsWith("render_")); assert.equal(chartTools.length, 2); assert.ok(chartTools.every((tool) => tool._meta?.ui?.resourceUri === "ui://skills-factory/charts/inline-v2.html" && tool._meta["openai/outputTemplate"] === tool._meta.ui.resourceUri));
  const resources = await (await handleMcp(rpc("resources/list"))).json() as { result: { resources: Array<{ uri: string; mimeType: string }> } }; assert.deepEqual(resources.result.resources, [{ uri: "ui://skills-factory/charts/inline-v2.html", name: "Interactive charts", description: "Self-contained HTML/CSS/SVG chart view for bar and line chart tools.", mimeType: "text/html;profile=mcp-app" }]);
  const ui = await (await handleMcp(rpc("resources/read", { uri: "ui://skills-factory/charts/inline-v2.html" }))).json() as { result: { contents: Array<{ mimeType: string; text: string; _meta?: { "openai/ui"?: { availableDisplayModes?: string[] } } }> } }; assert.equal(ui.result.contents[0].mimeType, "text/html;profile=mcp-app"); assert.match(ui.result.contents[0].text, /window\.openai\?\.toolOutput/); assert.match(ui.result.contents[0].text, /addEventListener\('click'/); assert.match(ui.result.contents[0].text, /<details class=\"table\">/); assert.doesNotMatch(ui.result.contents[0].text, /max-height:150px;overflow:auto/); assert.match(ui.result.contents[0].text, /requestDisplayMode\(\{mode:'inline'\}\)/); assert.deepEqual(ui.result.contents[0]._meta?.["openai/ui"]?.availableDisplayModes, ["inline"]); assert.doesNotMatch(JSON.stringify(ui.result.contents[0]), /fullscreen/);
  for (const t of TOOLS) assert.deepEqual(t.annotations, { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false });
  assert.equal((await handleMcp(rpc("tools/call", { name: "render_bar_chart", arguments: { ...bar, expected_points: 3 } }))).status, 401);
  const good = await (await handleMcp(rpc("tools/call", { name: "render_bar_chart", arguments: { ...bar, title: "Zażółć gęślą jaźń", expected_points: 3 } }, { "oai-authenticated-user-id": "test-only" }))).json() as { result: { isError: boolean; content: Array<{ type?: string; text?: string }>; structuredContent: { svg: string; data: { labels: string[]; values: number[] } } } };
  assert.equal(good.result.isError, false);
  assert.equal(good.result.structuredContent.data.labels.length, 3); assert.match(good.result.structuredContent.svg, /<svg[\s\S]*<title id="chart-title">Zażółć gęślą jaźń<\/title>/); assert.ok(good.result.content.every((item) => item.type === "text"));
  const lineGood = await (await handleMcp(rpc("tools/call", { name: "render_line_chart", arguments: { ...line, expected_x_labels: 2, expected_series: 1, expected_points_per_series: 2 } }, { "oai-authenticated-user-id": "test-only" }))).json() as { result: { isError: boolean; content: Array<{ type?: string; text?: string }>; structuredContent: { svg: string; data: { x_labels: string[]; series_names: string[]; series_values: number[][] } } } };
  assert.equal(lineGood.result.isError, false);
  assert.deepEqual(lineGood.result.structuredContent.data.x_labels, ["Q1", "Q2"]); assert.match(lineGood.result.structuredContent.svg, /<title>Series \/ Q1: 0 PLN<\/title>/); assert.match(lineGood.result.structuredContent.svg, /<title>Series \/ Q2: -10 PLN<\/title>/); assert.ok(lineGood.result.content.every((item) => item.type === "text"));
  const bad = await (await handleMcp(rpc("tools/call", { name: "render_line_chart", arguments: { ...line, series_values: [[1]], expected_x_labels: 2, expected_series: 1, expected_points_per_series: 2 } }, { "oai-authenticated-user-id": "test-only" }))).json() as { result: { isError: boolean } }; assert.equal(bad.result.isError, true);
  const catalog = callTool("list_skills", {}); assert.equal(catalog.skills.length, catalog.skill_count); assert.ok(catalog.skills.every((item) => !("reference_files" in item)));
  const loaded = callTool("load_skill", { skill_name: "oaf-health-check" });
  const loadedReferences = loaded.reference_files as Record<string, string>;
  assert.match(loaded.instructions, /Load `references\/WORKFLOW\.md`/);
  assert.match(loadedReferences["references/WORKFLOW.md"], /# OAF Health Check Workflow/);
  assert.ok(Object.keys(loadedReferences).every((path) => !path.split("/").includes("evals")));
  const workflows = catalog.skills.filter((item) => item.kind === "workflow"); assert.equal(workflows.length, 19);
  for (const workflow of workflows) {
    const item = callTool("load_skill", { skill_name: workflow.name });
    const references = item.reference_files as Record<string, string>;
    assert.ok(references["references/WORKFLOW.md"], `${workflow.name} workflow reference missing`);
    assert.ok(Object.keys(references).every((path) => !path.split("/").includes("evals")), `${workflow.name} leaked eval fixture`);
  }
});
test("runtime attestation identifies this Site release and exact tool contract", async () => {
  const metadata = { id: "worker-version-123", tag: "0123456789abcdef0123456789abcdef01234567", timestamp: "2026-10-07T10:00:00.000Z" };
  const result = await callTool("runtime_info", {}, metadata) as Record<string, unknown>;
  const expectedDigest = createHash("sha256").update(JSON.stringify(TOOLS.map(({ name, inputSchema }) => ({ name, inputSchema })))).digest("hex");
  assert.equal(result.attestation_status, "verified");
  assert.equal(result.release_id, metadata.id);
  assert.equal(result.source_revision, metadata.tag);
  assert.equal(result.canonical_source_revision, CANONICAL_SOURCE_REVISION);
  assert.equal(result.github_main_revision, CANONICAL_SOURCE_REVISION);
  assert.equal(result.routing_contract_blob_sha, ROUTING_CONTRACT_BLOB_SHA);
  assert.equal(result.channel, "site");
  assert.equal(result.capability_contract_version, "site-mcp-v2");
  assert.equal(result.tool_schema_digest, `sha256:${expectedDigest}`);
  assert.equal(result.deployed_at, metadata.timestamp);
  assert.equal(result.identity_source, "cloudflare_version_metadata");
  const configured = await callTool("runtime_info", {}, { id: metadata.tag, tag: metadata.tag, timestamp: metadata.timestamp, source: "site_environment" }) as Record<string, unknown>;
  assert.equal(configured.attestation_status, "verified");
  assert.equal(configured.identity_source, "site_environment");
  const missing = await callTool("runtime_info", {}) as Record<string, unknown>;
  assert.equal(missing.attestation_status, "unattested");
  assert.equal(missing.source_revision, "unattested");
  const response = await handleMcp(
    rpc("tools/call", { name: "runtime_info", arguments: {} }, { "oai-authenticated-user-id": "test-only" }),
    metadata,
  );
  const body = await response.json() as { result: { structuredContent: Record<string, unknown> } };
  assert.equal(body.result.structuredContent.attestation_status, "verified");
  assert.equal(body.result.structuredContent.release_id, metadata.id);
});
test("MCP notifications, malformed JSON, size limits and origin checks", async () => {
  assert.equal((await handleMcp(new Request("https://example.com/mcp"))).status, 405);
  assert.equal((await handleMcp(rpc("ping", {}, { origin: "https://evil.example" }))).status, 403);
  assert.equal((await handleMcp(rpc("ping", {}, { "mcp-protocol-version": "invalid" }))).status, 400);
  const unknown = await (await handleMcp(rpc("unknown"))).json() as { error: { code: number } }; assert.equal(unknown.error.code, -32601);
  const raw = (body: string) => new Request("https://example.com/mcp", { method: "POST", headers: { "content-type": "application/json" }, body });
  assert.equal((await handleMcp(raw(JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" })))).status, 202);
  assert.equal((await handleMcp(raw("x".repeat(131073)))).status, 413);
  assert.equal((await handleMcp(raw("{"))).status, 400);
});
test("embedded Lab release identity and executor isolation", () => {
  const catalog = callTool("list_skills", {});
  assert.equal(catalog.version, LAB_RELEASE.version);
  assert.equal(catalog.source_revision, LAB_RELEASE.source_revision);
  assert.equal(catalog.artifact_sha256, LAB_RELEASE.artifact_sha256);
  const attention = callTool("load_skill", { skill_name: "investment-attention-triage" });
  assert.equal(attention.version, "0.2.4");
  assert.match(attention.instructions, /materiality/i);
  for (const skill of catalog.skills) {
    const loaded = callTool("load_skill", { skill_name: skill.name });
    assert.doesNotMatch(loaded.instructions, /## Lab runtime eval inputs|references\/evals\//i);
    assert.ok(Object.keys(loaded.reference_files).every(path => !path.split("/").some(part => ["evals", "tests"].includes(part))));
    assert.equal(createHash("sha256").update(loaded.instructions).digest("hex"), loaded.instruction_sha256);
    // Component content_sha256 also includes packaged agent metadata and icons.
    // Check the actual instructions/references returned to the host separately.
    const digest = createHash("sha256");
    const refs = loaded.reference_files as Record<string, string>;
    for (const [path, content] of Object.entries({ "SKILL.md": loaded.instructions, ...refs }).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)) digest.update(path + "\0" + content + "\0");
    assert.equal(digest.digest("hex"), loaded.host_surface_sha256, skill.name);
  }
});
test("complete Lab includes Presentation/Report/skill-development drafts without an extension", async () => {
  const catalog = callTool("list_skills", {});
  assert.equal(catalog.lab_release.skill_count, catalog.skill_count);
  assert.equal(catalog.draft_extension, null);
  assert.equal(catalog.artifact_scope, "complete_lab");
  const expected = ["presentation-brief", "presentation-storyline", "presentation-evidence-review", "presentation-exhibit-design", "presentation-slide-authoring", "presentation-deck-review", "presentation-export-verification", "presentation-production", "report-document-architecture", "report-document-authoring", "report-document-review", "report-production", "skill-development"];
  for (const name of expected) assert.ok(catalog.skills.some(skill => skill.name === name));
  for (const name of expected) {
    const loaded = callTool("load_skill", { skill_name: name });
    assert.equal(loaded.maturity, "draft");
    assert.equal(loaded.source_revision, catalog.lab_release.source_revision);
    const refs = loaded.reference_files as Record<string, string>;
    if (name === "presentation-production") {
      assert.ok(refs["references/canva-connector-contract.md"]);
      assert.match(refs["references/creative-direction.md"], /signature moment/);
    }
    if (loaded.kind === "workflow") assert.ok(refs["references/WORKFLOW.md"]);
  }
  const runtime = await callTool("runtime_info", {});
  assert.equal(runtime.runtime_release.skill_count, catalog.skill_count);
  assert.equal(runtime.lab_release.skill_count, catalog.skill_count);
});
test("MCP receipts bind content and distinguish routing, rendering and validation", async () => {
  const metadata = { id: "test-version", tag: "0123456789abcdef0123456789abcdef01234567", timestamp: "2026-10-09T10:00:00Z" };
  type ToolResult = { isError: boolean; structuredContent: Record<string, unknown>; content: Array<{ type: string }> };
  const invoke = async (name: string, args: unknown) => (await (await handleMcp(rpc("tools/call", { name, arguments: args }, { "oai-authenticated-user-id": "test-only" }), metadata)).json() as { result: ToolResult }).result;
  const route = await invoke("route_investment_request", { user_request: "Review stock ACN" });
  const { tool_receipt: rawReceipt, ...output } = route.structuredContent;
  const tool_receipt = rawReceipt as Record<string, unknown>;
  const sort = (value: unknown): unknown => Array.isArray(value) ? value.map(sort) : value && typeof value === "object" ? Object.fromEntries(Object.keys(value).sort().map(key => [key, sort((value as Record<string, unknown>)[key])])) : value;
  assert.equal(tool_receipt.output_sha256, createHash("sha256").update(JSON.stringify(sort(output))).digest("hex"));
  assert.equal(tool_receipt.input_sha256, createHash("sha256").update(JSON.stringify({ user_request: "Review stock ACN" })).digest("hex"));
  assert.equal(tool_receipt.source_revision, metadata.tag);
  assert.equal(tool_receipt.status, "SUCCESS");
  assert.equal(output.workflow_execution_state, "not_executed");
  assert.equal(output.outcome, null);
  const scoreCall = await invoke("calculate_opportunity_scores", { as_of: "2026-10-27", rows: [{ candidate_id: "mcp-test", horizon: "1-3m", evidence: {} }] });
  assert.equal(scoreCall.isError, false);
  assert.equal((scoreCall.structuredContent.scores as Array<Record<string, unknown>>)[0].status, "NOT_SCORED");
  assert.equal((scoreCall.structuredContent.tool_receipt as Record<string, unknown>).tool_name, "calculate_opportunity_scores");
  const chartArgs = { ...bar, expected_points: 3 };
  const chart = await invoke("render_bar_chart", chartArgs);
  const chartReceipt = chart.structuredContent.tool_receipt as Record<string, unknown>;
  assert.equal(chartReceipt.artifact_state, "rendered");
  assert.equal(chartReceipt.client_display_state, "not_observable");
  const invalid = await invoke("render_bar_chart", { ...bar, values: [null, 1, 2], expected_points: 3 });
  assert.equal(invalid.isError, true);
  const invalidReceipt = invalid.structuredContent.tool_receipt as Record<string, unknown>;
  assert.equal(invalidReceipt.status, "FAILURE");
  assert.equal(invalidReceipt.execution_state, "not_executed");
  assert.equal(invalidReceipt.artifact_state, "FAIL_VALIDATION");
  assert.equal(invalidReceipt.client_display_state, "not_applicable");
});

test("MCP receipts correlate only valid W3C traceparent metadata", async () => {
  type ToolResult = { structuredContent: Record<string, unknown> };
  const invoke = async (traceparent?: unknown) => {
    const params = { name: "runtime_info", arguments: {}, ...(traceparent === undefined ? {} : { _meta: { traceparent } }) };
    const response = await handleMcp(rpc("tools/call", params, { "oai-authenticated-user-id": "test-only" }));
    return (await response.json() as { result: ToolResult }).result.structuredContent.tool_receipt as Record<string, unknown>;
  };
  const first = await invoke("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01");
  const second = await invoke("00-4bf92f3577b34da6a3ce929d0e0e4736-b7ad6b7169203331-00");
  assert.equal(first.run_id, "4bf92f3577b34da6a3ce929d0e0e4736");
  assert.equal(second.run_id, first.run_id);
  assert.equal(first.trace_parent_status, "accepted");
  assert.equal(second.trace_parent_status, "accepted");
  assert.equal(first.input_sha256, createHash("sha256").update("{}").digest("hex"));
  assert.doesNotMatch(JSON.stringify(first), /00f067aa0ba902b7|traceparent/);

  const absent = await invoke();
  assert.equal(absent.trace_parent_status, "not_provided");
  assert.ok(!("run_id" in absent));
  const invalid = await invoke("00-00000000000000000000000000000000-00f067aa0ba902b7-01");
  assert.equal(invalid.trace_parent_status, "invalid");
  assert.ok(!("run_id" in invalid));
});

test("catalog investment record store resolves the canonical bootstrap and reports writes", () => {
  const loaded = callTool("load_skill", { skill_name: "investment-record-store" });
  const catalog = callTool("list_skills", {});
  assert.equal(loaded.version, catalog.skills.find((skill) => skill.name === "investment-record-store")?.version);
  assert.match(loaded.instructions, /public\.system_config/);
  assert.match(loaded.instructions, /Never silently fall back from Supabase to Sheets/);
  assert.match(loaded.instructions, /After every write attempt, return an explicit WRITE receipt/);
});

test("main runtime delta: unrelated tasks and host child execution", () => {
  for (const request of ["Fix punctuation only: The team, works well. No investment analysis.", "Create a SECURITY.md and CODEOWNERS governance plan.", "The SKILL.md source and mock artifacts exist; certify Report OS as production-ready."]) {
    const r = routeInvestment(request); assert.equal(r.route, "not_applicable"); assert.equal(r.is_investment_request, false);
  }
  for (const [request, expected] of [
    ["Give attention to this thesis and suggest next research", "investment-attention-review"],
    ["Screen my watchlist, preview only", "investment-opportunity-hunter"],
    ["A company in my watchlist just reported earnings. Triage whether it changes my thesis and what deserves deeper research.", "investment-attention-review"],
    ["Spółka z mojej watchlisty opublikowała nowe wyniki. Oceń ich wpływ na tezę i powiedz, co wymaga dalszej analizy.", "investment-attention-review"],
    ["Check my thesis after earnings.", "investment-attention-review"],
    ["Review new earnings evidence against my active thesis and state what deserves deeper research.", "investment-attention-review"],
    ["Sprawdź moją tezę po wynikach spółki.", "investment-attention-review"],
    ["Review my thesis about the company.", "investment-security-review"],
    ["Sprawdź moją tezę o spółce.", "investment-security-review"],
  ]) {
    const r=routeInvestment(request); assert.equal(r.child_workflow, expected); assert.equal(r.response_policy, "load_child_workflow_then_follow"); assert.equal(r.workflow_executed, false);
  }
});

test("governance inventory boundary and monitoring block survive Site adapter", () => {
 const catalog = callTool("list_skills", {});
 assert.match(catalog.evidence_boundary.reconciliation, /exact source revision and both ID sets/);
 const loaded = callTool("load_skill", {skill_name: "investment-attention-review"});
 assert.equal(loaded.version, catalog.skills.find((skill) => skill.name === "investment-attention-review")?.version);
 const references = loaded.reference_files as Record<string, string>;
 assert.match(references["references/WORKFLOW.md"], /Investment Attention Review Workflow/);
 assert.match(references["references/WORKFLOW.md"], /investment-attention-triage/);
});


test("embedded Lab exposes exact release and decoded payload identity for parity", async () => {
  const info = await runtimeInfo();
  assert.equal(info.lab_release.release_id.startsWith(info.lab_release.version + "+"), true);
  assert.match(info.lab_release.payload_content_sha256, /^[0-9a-f]{64}$/);
  assert.notEqual(info.lab_release.payload_content_sha256, info.lab_release.artifact_sha256);
});


test("chart discovery avoids connector truncation while the server enforces upper bounds", () => {
  const assertNoTruncatingBounds = (value: unknown): void => {
    if (!value || typeof value !== "object") return;
    assert.ok(!("maxItems" in value), "connector must not clamp chart arrays");
    assert.ok(!("maxLength" in value), "connector must not clamp chart text");
    for (const child of Object.values(value)) assertNoTruncatingBounds(child);
  };
  for (const tool of TOOLS.filter(t => t.name.startsWith("render_"))) {
    assertNoTruncatingBounds(tool.inputSchema);
    assert.match(tool.description, /expected_/);
  }
  const barRequired = TOOLS.find(t => t.name === "render_bar_chart")!.inputSchema.required as string[];
  const lineRequired = TOOLS.find(t => t.name === "render_line_chart")!.inputSchema.required as string[];
  assert.ok(barRequired.includes("expected_points"));
  for (const key of ["expected_x_labels", "expected_series", "expected_points_per_series"]) assert.ok(lineRequired.includes(key));
  for (const args of [
    { ...bar, labels: Array(61).fill("item"), values: Array(61).fill(1) },
    { ...bar, labels: ["x".repeat(81)], values: [1] },
    { ...bar, title: "x".repeat(161) },
    { ...bar, unit: "x".repeat(31) },
  ]) assert.throws(() => chartCall("render_bar_chart", args));
  for (const args of [
    { ...line, x_labels: Array(101).fill("x"), series_values: [Array(101).fill(1)] },
    { ...line, series_names: Array(9).fill("s"), series_values: Array.from({ length: 9 }, () => [1, 2]) },
    { ...line, series_values: [Array(101).fill(1)] },
    { ...line, series_names: ["x".repeat(81)] },
    { ...line, title: "x".repeat(161) },
    { ...line, unit: "x".repeat(31) },
  ]) assert.throws(() => chartCall("render_line_chart", args));
});

test("accepted upper-bound charts preserve every tail label, value and series", () => {
  const barArgs = { ...bar, labels: Array.from({ length: 60 }, (_, i) => `item-${i}`), values: Array.from({ length: 60 }, (_, i) => i === 59 ? -123 : i) };
  const barResult = chartCall("render_bar_chart", barArgs);
  assert.deepEqual(barResult.data, barArgs);
  assert.match(barResult.svg, /item-59: -123/);
  const lineArgs = { ...line, x_labels: Array.from({ length: 100 }, (_, i) => `point-${i}`), series_names: Array.from({ length: 8 }, (_, i) => `series-${i}`), series_values: Array.from({ length: 8 }, (_, si) => Array.from({ length: 100 }, (_, i) => si === 7 && i === 99 ? -123 : si + i)) };
  const lineResult = chartCall("render_line_chart", lineArgs);
  assert.deepEqual(lineResult.data, lineArgs);
  assert.match(lineResult.svg, /series-7 \/ point-99: -123/);
});

test("oversized MCP charts return validation failure and no SVG success receipt", async () => {
  type ToolResult = { isError: boolean; structuredContent: Record<string, unknown>; content: Array<{ type: string }> };
  const cases = [
    ["render_bar_chart", { ...bar, labels: Array(61).fill("item"), values: Array(61).fill(1), expected_points: 61 }],
    ["render_line_chart", { ...line, x_labels: Array(101).fill("x"), series_values: [Array(101).fill(1)], expected_x_labels: 101, expected_series: 1, expected_points_per_series: 101 }],
    ["render_line_chart", { ...line, series_names: Array(9).fill("s"), series_values: Array.from({ length: 9 }, () => [1, 2]), expected_x_labels: 2, expected_series: 9, expected_points_per_series: 2 }],
  ] as const;
  for (const [name, args] of cases) {
    const response = await handleMcp(rpc("tools/call", { name, arguments: args }, { "oai-authenticated-user-id": "test-only" }));
    const { result } = await response.json() as { result: ToolResult };
    const receipt = result.structuredContent.tool_receipt as Record<string, unknown>;
    assert.equal(result.isError, true);
    assert.equal(receipt.status, "FAILURE");
    assert.equal(receipt.execution_state, "not_executed");
    assert.equal(receipt.failure_state, "FAIL_VALIDATION");
    assert.ok(!("svg" in result.structuredContent));
    assert.ok(result.content.every(item => item.type === "text"));
  }
});

test("chart shape guards fail closed for stale connectors and silently truncated arrays", async () => {
  type ToolResult = { isError: boolean; structuredContent: Record<string, unknown>; content: Array<{ type: string }> };
  const call = async (name: string, args: unknown) => {
    const response = await handleMcp(rpc("tools/call", { name, arguments: args }, { "oai-authenticated-user-id": "test-only" }));
    return (await response.json() as { result: ToolResult }).result;
  };
  const staleBar = await call("render_bar_chart", bar);
  assert.equal(staleBar.isError, true, "v1 connector omits required expected_points");
  assert.equal((staleBar.structuredContent.tool_receipt as Record<string, unknown>).failure_state, "FAIL_VALIDATION");
  assert.ok(!("svg" in staleBar.structuredContent));
  const staleLine = await call("render_line_chart", line);
  assert.equal(staleLine.isError, true, "v1 connector omits required expected shape counts");
  assert.equal((staleLine.structuredContent.tool_receipt as Record<string, unknown>).failure_state, "FAIL_VALIDATION");
  assert.ok(!("svg" in staleLine.structuredContent));

  const originalLabels = Array.from({ length: 61 }, (_, i) => `B${i}`);
  const originalValues = Array.from({ length: 61 }, (_, i) => i === 60 ? -123 : i);
  const truncatedBar = await call("render_bar_chart", { labels: originalLabels.slice(0, 60), values: originalValues.slice(0, 60), expected_points: 61, title: "B", unit: "u", horizontal: false });
  assert.equal(truncatedBar.isError, true);
  assert.equal((truncatedBar.structuredContent.tool_receipt as Record<string, unknown>).failure_state, "FAIL_VALIDATION");
  assert.ok(!("svg" in truncatedBar.structuredContent));

  const originalSeries = Array.from({ length: 9 }, (_, si) => Array.from({ length: 101 }, (_, i) => si === 8 && i === 100 ? -456 : si * 1000 + i));
  const truncatedLine = await call("render_line_chart", { x_labels: Array.from({ length: 100 }, (_, i) => `X${i}`), series_names: Array.from({ length: 8 }, (_, i) => `S${i}`), series_values: originalSeries.slice(0, 8).map(values => values.slice(0, 100)), expected_x_labels: 101, expected_series: 9, expected_points_per_series: 101, title: "L", unit: "u" });
  assert.equal(truncatedLine.isError, true);
  assert.equal((truncatedLine.structuredContent.tool_receipt as Record<string, unknown>).failure_state, "FAIL_VALIDATION");
  assert.ok(!("svg" in truncatedLine.structuredContent));

  const correctLine = await call("render_line_chart", { ...line, expected_x_labels: 2, expected_series: 1, expected_points_per_series: 2 });
  assert.equal(correctLine.isError, false);
  assert.deepEqual(correctLine.structuredContent.data, line, "shape assertions are not mixed into chart data");

  const validBar = await call("render_bar_chart", { labels: originalLabels.slice(0, 60), values: originalValues.slice(0, 60), expected_points: 60, title: "B", unit: "u", horizontal: false });
  assert.equal(validBar.isError, false);
  assert.deepEqual((validBar.structuredContent.data as { labels: string[]; values: number[] }).labels, originalLabels.slice(0, 60));
  assert.equal((validBar.structuredContent.data as { values: number[] }).values.at(-1), 59);

  const validSeriesNames = Array.from({ length: 8 }, (_, i) => `S${i}`);
  const validXLabels = Array.from({ length: 100 }, (_, i) => `X${i}`);
  const validSeries = Array.from({ length: 8 }, (_, si) => Array.from({ length: 100 }, (_, i) => si === 7 && i === 99 ? -456 : si * 1000 + i));
  const validLine = await call("render_line_chart", { x_labels: validXLabels, series_names: validSeriesNames, series_values: validSeries, expected_x_labels: 100, expected_series: 8, expected_points_per_series: 100, title: "L", unit: "u" });
  assert.equal(validLine.isError, false);
  assert.equal((validLine.structuredContent.data as { series_values: number[][] }).series_values[7][99], -456);
});

 test("software identity preserves Lab version independently of Site deployment", async () => {
  const info = await runtimeInfo();
  assert.deepEqual(info.software_release, {version: LAB_RELEASE.version, release_id: LAB_RELEASE.release_id, source_revision: LAB_RELEASE.source_revision});
});

test("list_skills provides a discovery path for matching Cloud Next requests", () => {
  const description = TOOLS.find((tool) => tool.name === "list_skills")?.description;
  assert.ok(description);
  assert.match(description, /MANDATORY discovery step for this app: before answering any substantive user request, call list_skills/i);
  assert.match(description, /call load_skill for its exact packaged instructions before answering/i);
  assert.match(description, /never answer a substantive request before these calls/i);
  assert.match(description, /read-only; does not execute a skill/i);
});
