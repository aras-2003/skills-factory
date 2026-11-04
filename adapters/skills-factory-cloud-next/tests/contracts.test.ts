Warning: truncated output (original token count: 16400)
Total output lines: 670

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
  assert.match(loaded.instructions, /surface the conflict and pause dependent work…9400 tokens truncated…26-10-09T10:00:00Z" };
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
