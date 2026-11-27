import test from "node:test";
import assert from "node:assert/strict";
import {
  buildGithubActivity,
  buildHeatmap,
  collectPages,
  priorityLabelFromLabels,
  repositoryUrl,
  sourceSnapshot,
  workAreaFromLabels,
  withBoundedGithubRetry,
} from "../lib/product-intelligence.mjs";

const issue = (overrides = {}) => ({
  id: 10,
  number: 42,
  title: "Track a capability",
  html_url: `https://github.com/aras-2003/skills-factory/issues/${overrides.number ?? 42}`,
  state: "open",
  state_reason: null,
  labels: [{ name: "area:engineering" }],
  created_at: "2026-11-26T12:00:00Z",
  closed_at: null,
  ...overrides,
});
const pull = (overrides = {}) => ({
  id: 20,
  number: 43,
  title: "Ship the capability",
  html_url: `https://github.com/aras-2003/skills-factory/pull/${overrides.number ?? 43}`,
  state: "closed",
  merged_at: "2026-11-27T09:00:00Z",
  created_at: "2026-11-26T10:00:00Z",
  ...overrides,
});

test("issue and PR activity uses distinct source dates and ignores PR-shaped issue rows", () => {
  const events = buildGithubActivity([issue(), { ...issue({ id: 20, number: 43, pull_request: { url: "..." } }) }], [pull()]);
  assert.equal(events[0].sourceId, 10);
  assert.equal(events[0].occurredAt, "2026-11-26T12:00:00.000Z");
  assert.deepEqual(events.map(({ type, date, url }) => ({ type, date, url })), [
    { type: "issue_opened", date: "2026-11-26", url: "https://github.com/aras-2003/skills-factory/issues/42" },
    { type: "pr_merged", date: "2026-11-27", url: "https://github.com/aras-2003/skills-factory/pull/43" },
  ]);
});

test("completed issues exclude not_planned and unmapped domains remain unassigned", () => {
  const events = buildGithubActivity([
    issue({ state: "closed", closed_at: "2026-11-25T23:30:00Z", state_reason: "completed", labels: [] }),
    issue({ id: 11, number: 44, state: "closed", closed_at: "2026-11-26T10:00:00Z", state_reason: "not_planned" }),
  ], []);
  const completed = events.filter((event) => event.type === "issue_completed");
  assert.equal(completed.length, 1);
  assert.equal(completed[0].workArea, "unassigned");
});

test("duplicate issues are counted once and invalid source records are ignored", () => {
  const events = buildGithubActivity([issue(), issue(), issue({ number: 99, html_url: "javascript:alert(1)" })], []);
  assert.equal(events.filter((event) => event.type === "issue_opened").length, 1);
});

test("heatmap keeps activity types separate and bins events by UTC calendar day", () => {
  const events = buildGithubActivity([
    issue({ created_at: "2026-11-26T23:59:59-02:00" }),
    issue({ id: 11, number: 44, state: "closed", created_at: "2026-11-27T00:30:00Z", closed_at: "2026-11-27T01:00:00Z", state_reason: "completed" }),
  ], [pull()]);
  const heatmap = buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "VERIFIED" });
  assert.deepEqual(heatmap.types, ["issue_opened", "issue_completed", "pr_merged"]);
  assert.equal(heatmap.cells.find((cell) => cell.type === "issue_opened" && cell.date === "2026-11-27")?.count, 2);
  assert.equal(heatmap.cells.find((cell) => cell.type === "issue_completed" && cell.date === "2026-11-27")?.count, 1);
  assert.equal(heatmap.bins.some((bin) => bin.from === "2026-11-26"), true);
  assert.equal(heatmap.complete, true);
  assert.equal(buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "PARTIAL" }).complete, false);
  assert.equal(buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "STALE" }).complete, false);
  const weekly = buildHeatmap(events, { from: "2026-11-23", to: "2026-11-29", sourceState: "VERIFIED", period: "week" });
  assert.equal(weekly.bins.length, 1);
  assert.equal(weekly.cells.find((cell) => cell.type === "issue_opened")?.count, 2);
  const monthly = buildHeatmap(events, { from: "2026-11-01", to: "2026-11-30", sourceState: "VERIFIED", period: "month" });
  assert.equal(monthly.bins[0].key, "2026-11");
  assert.equal(monthly.cells.find((cell) => cell.type === "pr_merged")?.count, 1);
  assert.equal(buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "UNAVAILABLE" }).cells.length, 0);
});

test("source snapshots distinguish verified zero, partial data, and unavailable data", () => {
  assert.deepEqual(sourceSnapshot({ state: "VERIFIED", items: [], asOf: "2026-11-27T12:00:00.000Z" }), {
    state: "VERIFIED", count: 0, asOf: "2026-11-27T12:00:00.000Z", reason: null,
  });
  assert.equal(sourceSnapshot({ state: "PARTIAL", items: [issue()], asOf: "2026-11-27T12:00:00.000Z" }).count, 1);
  assert.deepEqual(sourceSnapshot({ state: "UNAVAILABLE", items: null, asOf: null, reason: "GitHub source unavailable." }), {
    state: "UNAVAILABLE", count: null, asOf: null, reason: "GitHub source unavailable.",
  });
});


test("page collector preserves pagination, deduplicates overlap, and does not claim a complete snapshot", async () => {
  const requestedPages = [];
  const result = await collectPages(async (page) => {
    requestedPages.push(page);
    if (page === 1) return Array.from({ length: 100 }, (_, index) => ({ id: index + 1, number: index + 1 }));
    if (page === 2) return [{ id: 100, number: 100 }, ...Array.from({ length: 99 }, (_, index) => ({ id: index + 101, number: index + 101 }))];
    return [];
  }, { pageSize: 100, maxPages: 3 });
  assert.equal(result.items.length, 199);
  assert.deepEqual(requestedPages, [1, 2, 3]);
  assert.equal(result.state, "PARTIAL");
  assert.match(result.reason, /overlapped/i);
});

test("page collector retains observed rows and marks a rate-limited continuation partial", async () => {
  const result = await collectPages(async (page) => {
    if (page === 1) return Array.from({ length: 100 }, (_, index) => ({ id: index + 1, number: index + 1 }));
    throw new Error("GitHub rate limited the read. Retry after the limit resets.");
  }, { pageSize: 100, maxPages: 3 });
  assert.equal(result.items.length, 100);
  assert.equal(result.state, "PARTIAL");
  assert.match(result.reason, /rate limited/i);
});

test("page collector reports an unavailable source instead of a false zero", async () => {
  const result = await collectPages(async () => { throw new Error("GitHub reader unavailable."); });
  assert.deepEqual(result, { items: null, state: "UNAVAILABLE", reason: "GitHub reader unavailable." });
});


test("ambiguous issue labels stay unassigned and GitHub priority labels remain distinct from Project fields", () => {
  assert.equal(workAreaFromLabels([{ name: "area:engineering" }, { name: "area:investing" }]), "unassigned");
  assert.equal(workAreaFromLabels([{ name: "area:engineering" }]), "engineering");
  assert.equal(priorityLabelFromLabels([{ name: "priority:p0" }]), "P0");
  assert.equal(priorityLabelFromLabels([{ name: "priority:p0" }, { name: "priority:p1" }]), "unassigned");
});

test("roadmap source links accept only canonical GitHub issue URLs", () => {
  assert.equal(repositoryUrl("https://github.com/aras-2003/skills-factory/issues/42", "issues", 42), "https://github.com/aras-2003/skills-factory/issues/42");
  assert.equal(repositoryUrl("https://attacker.example/aras-2003/skills-factory/issues/42", "issues", 42), null);
  assert.equal(repositoryUrl("https://github.com/aras-2003/skills-factory/issues/42?redirect=1", "issues", 42), null);
  assert.equal(repositoryUrl("https://github.com/aras-2003/skills-factory/pull/42", "issues", 42), null);
});


test("GitHub retry is bounded to one short Retry-After and respects long rate-limit waits", async () => {
  let attempts = 0;
  const response = await withBoundedGithubRetry(async () => {
    attempts += 1;
    return attempts === 1
      ? new Response("limited", { status: 429, headers: { "Retry-After": "0" } })
      : new Response("[]", { status: 200 });
  }, "https://api.github.com/repos/aras-2003/skills-factory/issues", { sleep: async () => {} });
  assert.equal(response.status, 200);
  assert.equal(attempts, 2);

  attempts = 0;
  const limited = await withBoundedGithubRetry(async () => {
    attempts += 1;
    return new Response("limited", { status: 429, headers: { "Retry-After": "600" } });
  }, "https://api.github.com/repos/aras-2003/skills-factory/issues", { sleep: async () => { throw new Error("must not sleep through reset"); } });
  assert.equal(limited.status, 429);
  assert.equal(attempts, 1);
});
