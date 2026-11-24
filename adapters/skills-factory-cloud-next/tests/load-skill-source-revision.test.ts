import { test } from "node:test";
import assert from "node:assert/strict";
import { handleMcp } from "../src/mcp-handler";
import { LAB_RELEASE, SKILL_CATALOG } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/skill-catalog";

const rpc = (method: string, params: unknown = {}) => new Request("https://example.test/mcp", {
  method: "POST", headers: { "content-type": "application/json", "oai-authenticated-user-id": "test" },
  body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
});

test("source-pinned load_skill contract through canonical Cloud Next handler", async () => {
  const list = await (await handleMcp(rpc("tools/list"))).json() as any;
  const schema = list.result.tools.find((tool: any) => tool.name === "load_skill").inputSchema;
  assert.deepEqual(schema.required, ["skill_name"]);
  assert.equal(schema.properties.expected_source_revision.type, undefined);
  assert.equal(schema.properties.expected_source_revision.minLength, undefined);
  assert.equal(schema.properties.expected_source_revision.maxLength, undefined);
  assert.equal(schema.properties.expected_source_revision.pattern, undefined);
  assert.equal(schema.properties.skill_name.minLength, undefined);
  assert.equal(schema.properties.skill_name.maxLength, undefined);
  assert.equal(schema.additionalProperties, false);
  const skill = SKILL_CATALOG[0];
  const siteRevision = LAB_RELEASE.source_revision === "f".repeat(40) ? "e".repeat(40) : "f".repeat(40);
  const invoke = async (args: Record<string, unknown>) => (await (await handleMcp(
    rpc("tools/call", { name: "load_skill", arguments: args }),
    { tag: siteRevision },
  )).json() as any).result;
  for (const args of [{ skill_name: skill.name }, { skill_name: skill.name, expected_source_revision: LAB_RELEASE.source_revision }]) {
    const result = await invoke(args);
    assert.equal(result.isError, false);
    assert.equal(result.structuredContent.source_revision, LAB_RELEASE.source_revision);
    assert.equal(result.structuredContent.instructions, skill.instructions);
  }
  const failures: Array<[Record<string, unknown>, string]> = [
    [{ skill_name: skill.name, expected_source_revision: siteRevision }, "SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision."],
    ...["", "a".repeat(39), "a".repeat(41), LAB_RELEASE.source_revision + "\n", "A".repeat(40), null, 42].map((value): [Record<string, unknown>, string] => [{ skill_name: skill.name, expected_source_revision: value }, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."]),
    [{ skill_name: skill.name, expected_source_revision: LAB_RELEASE.source_revision, unexpected: "do-not-echo" }, "INVALID_TOOL_ARGUMENTS: Invalid tool arguments."],
    [{ skill_name: skill.name, expected_source_revision: null, unexpected: "do-not-echo" }, "INVALID_TOOL_ARGUMENTS: Invalid tool arguments."],
    [{ skill_name: "", expected_source_revision: "A".repeat(40) }, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."],
    [{ skill_name: "", expected_source_revision: siteRevision }, "SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision."],
  ];
  for (const [args, message] of failures) {
    const result = await invoke(args);
    assert.equal(result.isError, true);
    assert.equal(result.structuredContent.error, message);
    assert.equal(JSON.parse(result.content[0].text).error, message);
    const error = result.structuredContent.error;
    assert.ok(!error.includes(skill.instructions));
    assert.ok(!error.includes(LAB_RELEASE.source_revision));
    assert.ok(!error.includes(siteRevision));
    assert.ok(!error.includes("do-not-echo"));
  }
  const release = LAB_RELEASE as unknown as { payload_content_sha256: unknown };
  const originalDigest = release.payload_content_sha256;
  try {
    release.payload_content_sha256 = null;
    for (const expected_source_revision of [LAB_RELEASE.source_revision, siteRevision]) {
      const result = await invoke({ skill_name: skill.name, expected_source_revision });
      assert.equal(result.isError, true);
      assert.equal(result.structuredContent.error, "SOURCE_REVISION_UNVERIFIABLE: Packaged source revision could not be verified.");
      assert.ok(!JSON.stringify(result).includes(skill.instructions));
    }
  } finally {
    release.payload_content_sha256 = originalDigest;
  }
});
