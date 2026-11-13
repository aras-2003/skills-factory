import { test } from "node:test";
import assert from "node:assert/strict";
import { filterCatalog, PROVENANCE_CLASSIFICATIONS } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/catalog-view";
import { listSkills } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/cloud-tools";
import { LAB_RELEASE } from "../../../sites/skills-factory-site/lib/skills-factory-adapter/skill-catalog";

test("provenance filter distinguishes all five states and preserves missing metadata as UNKNOWN", () => {
  const rows = [...PROVENANCE_CLASSIFICATIONS.map((classification) => ({
    name: classification.toLowerCase(), kind: "skill", domain: "demo", description: "synthetic", provenance: { classification },
  })), { name: "missing", kind: "skill", domain: "demo", description: "synthetic" }];
  assert.deepEqual(rows.map((row) => filterCatalog([row], { classification: "UNKNOWN" }).length), [0, 0, 0, 0, 1, 1]);
  for (const classification of PROVENANCE_CLASSIFICATIONS) {
    const expected = classification === "UNKNOWN" ? ["unknown", "missing"] : [classification.toLowerCase()];
    assert.deepEqual(filterCatalog(rows, { classification }).map((row) => row.name), expected);
  }
});

test("search, provenance and domain filters compose without changing item identity", () => {
  const rows = [
    { name: "alpha", kind: "skill", domain: "investing", description: "peer comparison", provenance: { classification: "COMPOSED" } },
    { name: "beta", kind: "workflow", domain: "investing", description: "portfolio review", provenance: { classification: "UNKNOWN" } },
    { name: "gamma", kind: "skill", domain: "career", description: "peer comparison", provenance: { classification: "COMPOSED" } },
  ];
  assert.deepEqual(filterCatalog(rows, { query: "PEER", classification: "COMPOSED", domain: "investing" }).map((row) => row.name), ["alpha"]);
  assert.deepEqual(filterCatalog(rows, { query: "missing" }), []);
});

test("MCP list_skills carries exact canonical provenance for its packaged Lab catalog", () => {
  const result = listSkills();
  assert.equal(result.skills.length, result.skill_count);
  assert.match(result.canonical_catalog_registry_sha256, /^[a-f0-9]{64}$/);
  assert.ok(result.skills.every((item) => item.canonical_source_revision === LAB_RELEASE.source_revision));
  assert.ok(result.skills.every((item) => item.canonical_source === item.provenance.source));
  assert.ok(result.skills.every((item) => /^[a-f0-9]{64}$/.test(item.provenance.source_sha256)));
  assert.ok(result.skills.every((item) => PROVENANCE_CLASSIFICATIONS.includes(item.provenance.classification)));
  assert.ok(result.skills.every((item) => item.maturity && item.source_status && item.capability_assessment));
  assert.ok(result.skills.some((item) => item.provenance.classification === "UNKNOWN"));
});
