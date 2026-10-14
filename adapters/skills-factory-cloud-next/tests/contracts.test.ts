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
test("Cloud Next facade matches the canonical cross-adapter MCP tool contract", () => {
  const contractPath = path.resolve(process.cwd(), "../../runtime/contracts/mcp-tools-v1.json");
  const contract = JSON.parse(readFileSync(contractPath, "utf8")) as { tools: Record<string, string[]> };
  const actual = Object.fromEntries(TOOLS.map((tool) => [tool.name, [...((tool.inputSchema as { required?: string[] }).required ?? [])].sort()]));
  assert.deepEqual(actual, contract.tools);
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
    ["Co się teraz dzieje z moim portfelem? Sprawdź, co zmieniło się od poprzedniego poprawnego snapshotu i powiedz mi tylko, co naprawdę warto obserwować. Nie chcę jeszcze ustalać docelowej struktury portfela ani robić rebalancingu.", "investment-portfolio-observation"],
    ["ACN 25%, IUIT 22%: review portfolio concentration risk", "investment-portfolio-review"],
    ["Oceń ryzyko i nakładanie ETF w portfelu", "investment-portfolio-review"],
    ["XYZ Technologies is a good investment; should I add 5% of my portfolio?", "investment-security-review"],
    ["Review Micron's thesis, valuation and portfolio fit after its position drifted to 9.5%", "investment-security-review"],
    ["Review my portfolio allocation, concentration and overlap across holdings", "investment-portfolio-review"],
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
    ["Pomóż ustalić limity ryzyka i politykę inwestycyjną", "investment-policy-design"],
    ["What does GPT mean?", "investment-os-review"], ["hello", "investment-os-review"],
  ];
  for (const [request, expected] of cases) { const r = routeInvestment(request); assert.equal(r.child_workflow, expected, request); assert.match(r.routing_receipt, new RegExp(`CHILD=${expected};`)); assert.equal(r.recommendation, null); assert.equal(r.workflow_executed, false); }
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
  }
  for (const request of ["Review stock ACN", "Review Micron's thesis and valuation", "Should I buy NVDA shares?", "Oceń spółkę ASML.", "Przeanalizuj akcje NVDA.", "Oceń akcje Allegro."]) {
    assert.equal(routeInvestment(request).child_workflow, "investment-security-review", request);
  }
  for (const request of ["Sprawdź aktualną tezę dla akcji Microsoft.", "Oceń tezy inwestycyjne dla akcji Microsoft.", "Przeanalizuj tezę dla spółki Microsoft."]) {
    assert.equal(routeInvestment(request).child_workflow, "investment-security-review", request);
    assert.equal(routeInvestment(request).status, "routed", request);
  }
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
  const init = await (await handleMcp(rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } }))).json() as { result: { protocolVersion: string; serverInfo: { version: string }; instructions: string } }; assert.equal(init.result.protocolVersion, "2025-06-18"); assert.equal(init.result.serverInfo.version, "site-mcp-v2"); assert.match(init.result.instructions, /call route_investment_request before analysis/); assert.match(init.result.instructions, /load_skill for the exact returned child_workflow/);
  const list = await (await handleMcp(rpc("tools/list"))).json() as { result: { tools: unknown[] } }; assert.equal(list.result.tools.length, 6);
  for (const t of TOOLS) assert.deepEqual(t.annotations, { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false });
  assert.equal((await handleMcp(rpc("tools/call", { name: "render_bar_chart", arguments: { ...bar, expected_points: 3 } }))).status, 401);
  const good = await (await handleMcp(rpc("tools/call", { name: "render_bar_chart", arguments: { ...bar, expected_points: 3 } }, { "oai-authenticated-user-id": "test-only" }))).json() as { result: { isError: boolean; content: Array<{ resource?: { mimeType?: string } }> } }; assert.equal(good.result.isError, false); assert.equal(good.result.content[1].resource?.mimeType, "image/svg+xml");
  const bad = await (await handleMcp(rpc("tools/call", { name: "render_line_chart", arguments: { ...line, series_values: [[1]], expected_x_labels: 2, expected_series: 1, expected_points_per_series: 2 } }, { "oai-authenticated-user-id": "test-only" }))).json() as { result: { isError: boolean } }; assert.equal(bad.result.isError, true);
  const catalog = callTool("list_skills", {}); assert.equal(catalog.skills.length, 83); assert.ok(catalog.skills.every((item) => !("reference_files" in item)));
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
  assert.equal(attention.version, "0.2.3");
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
  assert.equal(catalog.skill_count, 83);
  assert.equal(catalog.lab_release.skill_count, 83);
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
  assert.equal(runtime.runtime_release.skill_count, 83);
  assert.equal(runtime.lab_release.skill_count, 83);
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
  for (const [request, expected] of [["Give attention to this thesis and suggest next research", "investment-attention-review"], ["Screen my watchlist, preview only", "investment-opportunity-hunter"]]) {
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
