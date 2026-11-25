import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { INVESTMENT_DECISION_FIXTURES } from "../src/investment-decision-fixture-data";
import { callTool } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/cloud-tools";
import { handleMcp } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/mcp-handler";
import { LAB_RELEASE } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/skill-catalog";

const root = path.resolve(process.cwd(), "../..");
const inputPath = path.join(root, "adapters/skills-factory-cloud-next/src/investment-decision-fixtures.json");
const oraclePath = path.join(root, "adapters/skills-factory-cloud-next/tests/fixtures/investment-decision-oracle.json");
function canonical(value: any): any {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, canonical(item)]));
  return value;
}
const digest = (value: unknown) => createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");
const rpc = (args: unknown, authenticated = true) => new Request("https://example.test/mcp", { method: "POST", headers: { "content-type": "application/json", ...(authenticated ? { "oai-authenticated-user-id": "synthetic" } : {}) }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "evaluate_investment_decision_fixture", arguments: args } }) });

test("fixture inputs are source-bound, recomputed and match fresh Python decision oracle", async () => {
  const source = JSON.parse(readFileSync(inputPath, "utf8"));
  const storedOracle = JSON.parse(readFileSync(oraclePath, "utf8"));
  const python = `import json, pathlib\nfrom scripts.investing.investment_decisions import synthesize_decision\nr=pathlib.Path.cwd()\nd=json.load(open(${JSON.stringify(inputPath)}))\nprint(json.dumps({f['fixture_id']: synthesize_decision(f['input'],root=r) for f in d['fixtures']},sort_keys=True))`;
  const liveOracle = JSON.parse(execFileSync("python3", ["-c", python], { cwd: root, encoding: "utf8" }));
  assert.deepEqual(storedOracle, liveOracle, "stored oracle must reflect current Python implementation");
  assert.equal(INVESTMENT_DECISION_FIXTURES.length, 4);
  for (const f of INVESTMENT_DECISION_FIXTURES) {
    const src = source.fixtures.find((item: any) => item.fixture_id === f.fixture_id);
    assert.deepEqual(f.input, src.input);
    assert.equal(digest(f.input), f.input_sha256);
    assert.equal(f.input.context.execution_mode, "TEST");
    assert.deepEqual(f.input.context.write_scope, { mode: "NONE" });
    assert.match(f.input.context.analysis_id, /^analysis-synthetic-[0-9]+$/);
    assert.equal(f.input.context.instrument.canonical_id, "NASDAQ:TEST");
    const timestamp = f.input.context.as_of;
    assert.match(timestamp, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
    assert.equal(new Date(timestamp).toISOString(), timestamp.replace("Z", ".000Z"));
    for (const result of f.input.results) {
      assert.equal(result.instrument_id, f.input.context.instrument.canonical_id);
      assert.equal(result.as_of, timestamp);
      for (const ref of result.evidence_refs) {
        assert.equal(ref.source_url, "https://example.invalid/synthetic");
        assert.equal(ref.vendor, "synthetic-fixture");
        assert.match(ref.source_id, /^fixture-[a-z0-9-]+$/);
      }
    }
    const output: any = await callTool("evaluate_investment_decision_fixture", { fixture_id: f.fixture_id, expected_source_revision: LAB_RELEASE.source_revision });
    const expected = liveOracle[f.fixture_id];
    assert.equal(output.coverage, "PARITY_SUBSET_ONLY");
    assert.equal(output.fixture_input_sha256, f.input_sha256);
    for (const key of ["advisory_recommendation", "portfolio_action", "research_state", "owner_approval_required", "execution_authorized", "numeric_sizing_blocked"]) assert.deepEqual(output[key], expected[key], `${f.fixture_id}: ${key}`);
    assert.deepEqual(output.gate_results, expected.gate_results.map(({ gate_id, status, reason_codes }: any) => ({ gate_id, status, reason_codes })));
  }
});

test("MCP fixture pilot requires authentication, exact revision, known fixture and no extra arguments", async () => {
  const valid = { fixture_id: "new-unfavorable-wait", expected_source_revision: LAB_RELEASE.source_revision };
  assert.equal((await handleMcp(rpc(valid, false))).status, 401);
  const response: any = await (await handleMcp(rpc(valid), { tag: "a".repeat(40) })).json();
  assert.equal(response.result.isError, false);
  assert.equal(response.result.structuredContent.advisory_recommendation, "WAIT");
  assert.equal(response.result.structuredContent.tool_receipt.tool_name, "evaluate_investment_decision_fixture");
  assert.equal(response.result.structuredContent.tool_receipt.status, "SUCCESS");
  assert.match(response.result.structuredContent.tool_receipt.input_sha256, /^[a-f0-9]{64}$/);
  assert.match(response.result.structuredContent.tool_receipt.output_sha256, /^[a-f0-9]{64}$/);
  for (const bad of [{ ...valid, expected_source_revision: "f".repeat(40) }, { ...valid, expected_source_revision: null }, { ...valid, fixture_id: "unknown" }, { ...valid, context: { real_data: true } }, { fixture_id: valid.fixture_id }]) {
    const rejected: any = await (await handleMcp(rpc(bad))).json();
    assert.equal(rejected.result.isError, true);
    assert.equal(rejected.result.structuredContent.tool_receipt.status, "FAILURE");
  }
});
