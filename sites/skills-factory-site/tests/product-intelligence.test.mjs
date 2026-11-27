import test from "node:test";
import assert from "node:assert/strict";
import {
  activityNewestFirst,
  activityForHeatmapCell,
  buildGithubActivity,
  buildEventCoverage,
  buildHeatmap,
  collectPages,
  normalizeGithubCollection,
  priorityLabelFromLabels,
  repositoryUrl,
  retryAtFromReason,
  sourceSnapshot,
  sourceCacheEntryIsFresh,
  sourceCacheRetentionMs,
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
  assert.equal(completed[0].businessDomain, "unassigned");
});

test("domain heatmap keeps unverified business-domain mapping in one unassigned bucket", () => {
  const events = buildGithubActivity([
    issue({ id: 31, number: 51, labels: [{ name: "area:engineering" }], created_at: "2026-11-26T08:00:00Z" }),
    issue({ id: 32, number: 52, labels: [], created_at: "2026-11-26T09:00:00Z" }),
    issue({ id: 33, number: 53, created_at: "2026-11-27T09:00:00Z" }),
  ], [pull({ id: 41, number: 61, merged_at: "2026-11-26T10:00:00Z" })]);
  const heatmap = buildHeatmap(events, {
    from: "2026-11-26", to: "2026-11-26", sourceState: "VERIFIED",
    sourceAsOf: { issue_opened: "2026-11-27T00:00:00Z", issue_completed: "2026-11-27T00:00:00Z", pr_merged: "2026-11-27T00:00:00Z" },
  });

  assert.deepEqual(events.map((event) => event.businessDomain), ["unassigned", "unassigned", "unassigned", "unassigned"]);
  assert.deepEqual(heatmap.domains, ["unassigned"]);
  assert.equal(heatmap.cells.find((cell) => cell.businessDomain === "unassigned" && cell.type === "issue_opened")?.count, 2);
  assert.equal(heatmap.cells.find((cell) => cell.businessDomain === "unassigned" && cell.type === "pr_merged")?.count, 1);
  assert.deepEqual(activityForHeatmapCell(events, {
    from: "2026-11-26", to: "2026-11-26", type: "issue_opened", businessDomain: "unassigned",
  }).map((event) => event.number), [51, 52]);
});

test("recent activity orders full UTC instants newest first and breaks ties deterministically", () => {
  const issues = Array.from({ length: 11 }, (_, index) => {
    const latest = index === 0;
    const number = latest ? 1 : index + 1;
    const time = latest
      ? "2026-11-26T23:59:00Z"
      : index === 10
        ? "2026-11-27T00:59:00+01:00"
        : `2026-11-26T00:${String(index + 1).padStart(2, "0")}:00Z`;
    return issue({ id: 100 + index, number, created_at: time });
  });
  const events = buildGithubActivity(issues, [
    pull({ id: 250, number: 250, merged_at: "2026-11-26T23:59:00+00:00" }),
  ]);
  const latestTen = activityNewestFirst(events).slice(0, 10);

  assert.equal(latestTen[0].occurredAt, "2026-11-26T23:59:00.000Z");
  assert.equal(events.find((event) => event.number === 11)?.occurredAt, "2026-11-26T23:59:00.000Z");
  assert.equal(latestTen.some((event) => event.number === 1), true);
  assert.equal(latestTen.some((event) => event.number === 2), false);
  assert.equal(latestTen.length, 10);
  const tied = activityNewestFirst([
    { id: "z", type: "pr_merged", number: 9, occurredAt: "2026-11-27T01:00:00.000Z" },
    { id: "b", type: "issue_opened", number: 8, occurredAt: "2026-11-27T01:00:00.000Z" },
    { id: "a", type: "issue_opened", number: 3, occurredAt: "2026-11-27T01:00:00.000Z" },
  ]);
  assert.deepEqual(tied.map((event) => event.id), ["a", "b", "z"]);
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
  const heatmap = buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "VERIFIED", sourceAsOf: {
    issue_opened: "2026-11-30T23:59:59.999Z", issue_completed: "2026-11-30T23:59:59.999Z", pr_merged: "2026-11-30T23:59:59.999Z",
  } });
  assert.deepEqual(heatmap.types, ["issue_opened", "issue_completed", "pr_merged"]);
  assert.equal(heatmap.cells.find((cell) => cell.type === "issue_opened" && cell.date === "2026-11-27")?.count, 2);
  assert.equal(heatmap.cells.find((cell) => cell.type === "issue_completed" && cell.date === "2026-11-27")?.count, 1);
  assert.equal(heatmap.bins.some((bin) => bin.from === "2026-11-26"), true);
  assert.equal(heatmap.complete, true);
  assert.equal(buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "PARTIAL" }).complete, false);
  assert.equal(buildHeatmap(events, { from: "2026-11-26", to: "2026-11-27", sourceState: "STALE" }).complete, false);
  const weekly = buildHeatmap(events, { from: "2026-11-23", to: "2026-11-29", sourceState: "VERIFIED", sourceAsOf: {
    issue_opened: "2026-11-30T23:59:59.999Z", issue_completed: "2026-11-30T23:59:59.999Z", pr_merged: "2026-11-30T23:59:59.999Z",
  }, period: "week" });
  assert.equal(weekly.bins.length, 1);
  assert.equal(weekly.cells.find((cell) => cell.type === "issue_opened")?.count, 2);
  const monthly = buildHeatmap(events, { from: "2026-11-01", to: "2026-11-30", sourceState: "VERIFIED", sourceAsOf: {
    issue_opened: "2026-12-01T00:00:00.000Z", issue_completed: "2026-12-01T00:00:00.000Z", pr_merged: "2026-12-01T00:00:00.000Z",
  }, period: "month" });
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

test("malformed source rows downgrade collection completeness before aggregation", () => {
  const result = normalizeGithubCollection([
    issue({ body: "not projected into the normalized cache" }),
    issue({ id: 11, number: 44, html_url: "https://attacker.example/issues/44" }),
  ], "issues");
  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].body, undefined);
  assert.equal(result.state, "PARTIAL");
  assert.match(result.reason, /malformed/i);
  const pullResult = normalizeGithubCollection([
    pull(),
    pull({ id: 21, number: 45, merged_at: "not-a-date" }),
  ], "pulls");
  assert.equal(pullResult.items.length, 1);
  assert.equal(pullResult.state, "PARTIAL");
  const heatmap = buildHeatmap([], { from: "2026-11-01", to: "2026-11-02", sourceState: "PARTIAL" });
  assert.equal(heatmap.completeByType.issue_opened, false);
});

test("event coverage is type-specific and heatmap date ranges are bounded and strict", () => {
  const heatmap = buildHeatmap([], {
    from: "2026-11-01",
    to: "2026-11-03",
    sourceState: "VERIFIED",
    sourceStates: { issue_opened: "VERIFIED", issue_completed: "PARTIAL", pr_merged: "STALE" },
    sourceAsOf: { issue_opened: "2026-11-04T00:00:00.000Z", issue_completed: "2026-11-04T00:00:00.000Z", pr_merged: "2026-11-04T00:00:00.000Z" },
  });
  assert.deepEqual(heatmap.completeByType, { issue_opened: true, issue_completed: false, pr_merged: false });
  assert.equal(buildHeatmap([], { from: "2026-01-01", to: "2026-04-01", sourceState: "VERIFIED" }).bins.length, 0);
  assert.equal(buildHeatmap([], { from: "2026-02-31", to: "2026-03-02", sourceState: "VERIFIED" }).bins.length, 0);
  assert.deepEqual(buildEventCoverage("VERIFIED", "PARTIAL"), {
    issue_opened: "VERIFIED", issue_completed: "PARTIAL", pr_merged: "PARTIAL",
  });
  assert.equal(buildEventCoverage("STALE", "VERIFIED").issue_completed, "STALE");
});

test("per-source as-of times prevent empty daily, weekly and monthly bins beyond UTC coverage", () => {
  const daily = buildHeatmap([], {
    from: "2026-11-26", to: "2026-11-27", sourceState: "VERIFIED",
    sourceStates: { issue_opened: "VERIFIED", issue_completed: "PARTIAL", pr_merged: "VERIFIED" },
    sourceAsOf: { issue_opened: "2026-11-26T23:59:00.000Z", issue_completed: "2026-11-26T23:59:00.000Z", pr_merged: "2026-11-27T00:01:00.000Z" },
  });
  assert.equal(daily.completeByTypeAndBin.issue_opened["2026-11-26"], false);
  assert.equal(daily.completeByTypeAndBin.pr_merged["2026-11-26"], true);
  assert.equal(daily.completeByTypeAndBin.pr_merged["2026-11-27"], false);

  const weekly = buildHeatmap([], {
    from: "2026-11-23", to: "2026-11-29", sourceState: "VERIFIED", period: "week",
    sourceAsOf: { issue_opened: "2026-11-30T00:01:00.000Z", issue_completed: "2026-11-30T00:01:00.000Z", pr_merged: "2026-11-29T23:59:00.000Z" },
  });
  assert.equal(weekly.completeByTypeAndBin.issue_opened["2026-11-23"], true);
  assert.equal(weekly.completeByTypeAndBin.pr_merged["2026-11-23"], false);

  const monthly = buildHeatmap([], {
    from: "2026-11-01", to: "2026-11-30", sourceState: "VERIFIED", period: "month",
    sourceAsOf: { issue_opened: "2026-12-01T00:00:00.000Z", issue_completed: "2026-12-01T00:00:00.000Z", pr_merged: "2026-11-30T23:59:59.000Z" },
  });
  assert.equal(monthly.completeByTypeAndBin.issue_opened["2026-11"], true);
  assert.equal(monthly.completeByTypeAndBin.pr_merged["2026-11"], false);
});

test("partial rate-limited collection remains visible without retrying before provider reset", () => {
  const now = Date.parse("2026-11-27T12:00:00.000Z");
  const reset = Date.parse("2026-11-27T13:30:00.000Z");
  assert.equal(retryAtFromReason("Rate limited; retry after 2026-11-27T13:30:00.000Z."), reset);
  assert.equal(sourceCacheEntryIsFresh({ state: "PARTIAL", savedAt: now - 20 * 60_000, nextRetryAt: reset }, now, 10 * 60_000), true);
  assert.equal(sourceCacheEntryIsFresh({ state: "PARTIAL", savedAt: now - 20 * 60_000, nextRetryAt: reset }, reset, 10 * 60_000), false);
  assert.equal(sourceCacheEntryIsFresh({ state: "PARTIAL", savedAt: now - 5 * 60_000 }, now, 10 * 60_000), true);
  assert.equal(sourceCacheEntryIsFresh({ state: "UNAVAILABLE", savedAt: now }, now, 10 * 60_000), false);
  assert.equal(sourceCacheRetentionMs({ state: "PARTIAL", savedAt: now, nextRetryAt: reset }, "current", 10 * 60_000, 24 * 60 * 60_000), reset - now);
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
