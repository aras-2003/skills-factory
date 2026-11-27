const EVENT_TYPES = Object.freeze(["issue_opened", "issue_completed", "pr_merged"]);
const SOURCE_STATES = Object.freeze(["VERIFIED", "PARTIAL", "STALE", "UNAVAILABLE"]);
const REPOSITORY_PATH = "/aras-2003/skills-factory/";
const UNASSIGNED_BUSINESS_DOMAIN = "unassigned";

/** @template {{occurredAt:string,type:string,number:number,id:string}} T
 * @param {T[]} events
 * @returns {T[]}
 * Return a stable newest-first view without mutating the caller's event list.
 */
export function activityNewestFirst(events) {
  if (!Array.isArray(events)) return [];
  return [...events].sort((a, b) => {
    const timeOrder = String(b?.occurredAt ?? "").localeCompare(String(a?.occurredAt ?? ""));
    return timeOrder
      || String(a?.type ?? "").localeCompare(String(b?.type ?? ""))
      || (Number(a?.number) || 0) - (Number(b?.number) || 0)
      || String(a?.id ?? "").localeCompare(String(b?.id ?? ""));
  });
}

/** @template {{date:string,type:string,businessDomain?:string}} T
 * @param {T[]} events
 * @param {{from:string,to:string,type:string|null,businessDomain:string}} selection
 * @returns {T[]}
 * Return only source events represented by one domain/type/date-range heatmap selection.
 */
export function activityForHeatmapCell(events, selection) {
  if (!Array.isArray(events)) return [];
  return events.filter((event) => event.date >= selection.from
    && event.date <= selection.to
    && (!selection.type || event.type === selection.type)
    && (event.businessDomain ?? UNASSIGNED_BUSINESS_DOMAIN) === selection.businessDomain);
}

function utcDate(value) {
  if (typeof value !== "string" || !value) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const parsedDay = new Date(`${value}T00:00:00.000Z`);
    return Number.isFinite(parsedDay.getTime()) && parsedDay.toISOString().slice(0, 10) === value ? value : null;
  }
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString().slice(0, 10) : null;
}

/** @param {unknown} value @param {"issues"|"pull"} kind @param {number} number */
export function repositoryUrl(value, kind, number) {
  if (typeof value !== "string" || !Number.isSafeInteger(number) || number <= 0) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.hostname !== "github.com" || url.pathname !== `${REPOSITORY_PATH}${kind}/${number}` || url.search || url.hash) return null;
    return url.href;
  } catch {
    return null;
  }
}

export function workAreaFromLabels(labels) {
  if (!Array.isArray(labels)) return "unassigned";
  const candidates = labels
    .map((label) => typeof label === "string" ? label : label?.name)
    .filter((name) => typeof name === "string" && /^area:[a-z0-9][a-z0-9-]{0,63}$/i.test(name));
  if (candidates.length !== 1) return "unassigned";
  return candidates[0].slice("area:".length).toLowerCase();
}

export function priorityLabelFromLabels(labels) {
  if (!Array.isArray(labels)) return "unassigned";
  const candidates = labels
    .map((label) => typeof label === "string" ? label : label?.name)
    .filter((name) => typeof name === "string" && /^priority:[a-z0-9][a-z0-9-]{0,63}$/i.test(name));
  if (candidates.length !== 1) return "unassigned";
  return candidates[0].slice("priority:".length).toUpperCase();
}

function validRecord(row, kind) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return null;
  const number = Number(row.number);
  const url = repositoryUrl(row.html_url, kind, number);
  if (!url || typeof row.title !== "string" || typeof row.created_at !== "string") return null;
  return { id: Number.isSafeInteger(row.id) && row.id > 0 ? row.id : number, number, url, title: row.title.slice(0, 500), workArea: workAreaFromLabels(row.labels), row };
}

/** Build discrete, source-dated activity; never infer Project V2 state or workflow execution. */
export function buildGithubActivity(issues, pulls) {
  const events = [];
  const seen = new Set();
  const add = (type, record, sourceDate) => {
    const date = utcDate(sourceDate);
    if (!date) return;
    const key = `${type}:${record.id}`;
    if (seen.has(key)) return;
    seen.add(key);
    events.push({
      id: key,
      sourceId: record.id,
      type,
      date,
      occurredAt: new Date(sourceDate).toISOString(),
      // The current read source has no verified business-domain mapping.
      // Work-area labels and free text are not substitutes for that mapping.
      businessDomain: UNASSIGNED_BUSINESS_DOMAIN,
      workArea: record.workArea,
      number: record.number,
      title: record.title,
      url: record.url,
    });
  };

  for (const raw of Array.isArray(issues) ? issues : []) {
    if (raw?.pull_request) continue;
    const record = validRecord(raw, "issues");
    if (!record) continue;
    add("issue_opened", record, record.row.created_at);
    if (record.row.state === "closed" && record.row.state_reason === "completed") {
      add("issue_completed", record, record.row.closed_at);
    }
  }

  for (const raw of Array.isArray(pulls) ? pulls : []) {
    const record = validRecord(raw, "pull");
    if (!record) continue;
    add("pr_merged", record, record.row.merged_at);
  }

  return events.sort((a, b) => a.occurredAt.localeCompare(b.occurredAt)
    || a.type.localeCompare(b.type)
    || a.number - b.number
    || a.id.localeCompare(b.id));
}

/**
 * @param {Array<{type:string,date:string,businessDomain?:string}>} events
 * @param {{from:string,to:string,sourceState?:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",sourceStates?:Record<string,"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE">,sourceAsOf?:Record<string,string|null>,period?:"day"|"week"|"month"}} options
 * @returns {{bins:Array<{key:string,label:string,from:string,to:string}>,domains:string[],types:Array<"issue_opened"|"issue_completed"|"pr_merged">,cells:Array<{businessDomain:string,type:"issue_opened"|"issue_completed"|"pr_merged",date:string,count:number}>,complete:boolean,completeByType:Record<string,boolean>,completeByTypeAndBin:Record<string,Record<string,boolean>>,state:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",period:string}}
 */
export function buildHeatmap(events, { from, to, sourceState = "UNAVAILABLE", sourceStates = {}, sourceAsOf = {}, period = "day" }) {
  const start = utcDate(from);
  const end = utcDate(to);
  const state = ["VERIFIED", "PARTIAL", "STALE", "UNAVAILABLE"].includes(sourceState) ? sourceState : "UNAVAILABLE";
  const rangeDays = start && end ? (Date.parse(`${end}T00:00:00.000Z`) - Date.parse(`${start}T00:00:00.000Z`)) / 86_400_000 + 1 : Infinity;
  if (!start || !end || start > end || rangeDays > 90 || state === "UNAVAILABLE" || !["day", "week", "month"].includes(period)) {
    return { bins: [], domains: [], types: [...EVENT_TYPES], cells: [], complete: false, completeByType: {}, completeByTypeAndBin: {}, state, period };
  }
  const bins = [];
  const startDate = new Date(`${start}T00:00:00.000Z`);
  const endDate = new Date(`${end}T00:00:00.000Z`);
  if (period === "day") {
    for (let date = new Date(startDate); date <= endDate; date.setUTCDate(date.getUTCDate() + 1)) {
      const key = date.toISOString().slice(0, 10);
      bins.push({ key, label: key.slice(8), from: key, to: key });
    }
  } else if (period === "week") {
    const monday = new Date(startDate);
    monday.setUTCDate(monday.getUTCDate() - ((monday.getUTCDay() + 6) % 7));
    for (let fromDate = new Date(monday); fromDate <= endDate; fromDate.setUTCDate(fromDate.getUTCDate() + 7)) {
      const toDate = new Date(fromDate);
      toDate.setUTCDate(toDate.getUTCDate() + 6);
      const key = fromDate.toISOString().slice(0, 10);
      const clippedFrom = fromDate < startDate ? start : key;
      const clippedTo = toDate > endDate ? end : toDate.toISOString().slice(0, 10);
      bins.push({ key, label: `${clippedFrom.slice(5)}–${clippedTo.slice(5)}`, from: clippedFrom, to: clippedTo });
    }
  } else {
    const month = new Date(Date.UTC(startDate.getUTCFullYear(), startDate.getUTCMonth(), 1));
    for (let fromDate = new Date(month); fromDate <= endDate; fromDate.setUTCMonth(fromDate.getUTCMonth() + 1)) {
      const toDate = new Date(Date.UTC(fromDate.getUTCFullYear(), fromDate.getUTCMonth() + 1, 0));
      const key = fromDate.toISOString().slice(0, 7);
      const clippedFrom = fromDate < startDate ? start : `${key}-01`;
      const clippedTo = toDate > endDate ? end : toDate.toISOString().slice(0, 10);
      bins.push({ key, label: key, from: clippedFrom, to: clippedTo });
    }
  }
  const completeByTypeAndBin = Object.fromEntries(EVENT_TYPES.map((type) => {
    const asOf = typeof sourceAsOf[type] === "string" ? Date.parse(sourceAsOf[type]) : NaN;
    const coveredSource = (sourceStates[type] ?? state) === "VERIFIED" && Number.isFinite(asOf);
    return [type, Object.fromEntries(bins.map((bin) => [
      bin.key,
      coveredSource && asOf >= Date.parse(`${bin.to}T23:59:59.999Z`),
    ]))];
  }));
  const completeByType = Object.fromEntries(EVENT_TYPES.map((type) => [
    type,
    bins.length > 0 && bins.every((bin) => completeByTypeAndBin[type][bin.key]),
  ]));
  const binForDate = new Map();
  for (const bin of bins) {
    for (let date = new Date(`${bin.from}T00:00:00.000Z`); date.toISOString().slice(0, 10) <= bin.to; date.setUTCDate(date.getUTCDate() + 1)) {
      binForDate.set(date.toISOString().slice(0, 10), bin.key);
    }
  }
  const counts = new Map();
  for (const event of Array.isArray(events) ? events : []) {
    if (!EVENT_TYPES.includes(event?.type)) continue;
    const binKey = binForDate.get(event.date);
    if (!binKey) continue;
    // Until a source-backed domain mapping exists, every event is explicitly
    // unassigned. Ignore arbitrary domain-shaped values from cached payloads.
    const businessDomain = UNASSIGNED_BUSINESS_DOMAIN;
    const key = JSON.stringify([businessDomain, event.type, binKey]);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const cells = [...counts.entries()].map(([key, count]) => {
    const [businessDomain, type, date] = JSON.parse(key);
    return { businessDomain, type, date, count };
  }).sort((a, b) => a.date.localeCompare(b.date)
    || a.businessDomain.localeCompare(b.businessDomain)
    || a.type.localeCompare(b.type));
  return {
    bins,
    domains: [UNASSIGNED_BUSINESS_DOMAIN],
    types: [...EVENT_TYPES],
    cells,
    complete: state === "VERIFIED" && Object.values(completeByType).every(Boolean),
    completeByType,
    completeByTypeAndBin,
    state,
    period,
  };
}

/** Validate GitHub REST rows before aggregating them; excluded rows make coverage partial. */
/** @param {unknown[]} items @param {"issues"|"pulls"} resource @param {"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE"} [initialState] @param {string|null} [initialReason] @returns {{items:Array<Record<string,unknown>>|null,state:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",reason:string|null}} */
export function normalizeGithubCollection(items, resource, initialState = "VERIFIED", initialReason = null) {
  if (!Array.isArray(items)) return { items: null, state: "UNAVAILABLE", reason: initialReason ?? "Source did not return a record array." };
  const normalized = [];
  let invalid = 0;
  for (const item of items) {
    if (resource === "issues" && item?.pull_request) continue;
    const expectedKind = resource === "issues" ? "issues" : "pull";
    const number = Number(item?.number);
    const valid = item && typeof item === "object" && !Array.isArray(item)
      && Number.isSafeInteger(item.id) && item.id > 0
      && Number.isSafeInteger(number) && number > 0
      && typeof item.title === "string"
      && repositoryUrl(item.html_url, expectedKind, number) !== null
      && utcDate(item.created_at) !== null
      && (resource !== "issues" || ["open", "closed"].includes(item.state))
      && (resource !== "issues" || item.state !== "closed" || utcDate(item.closed_at) !== null)
      && (resource !== "pulls" || item.merged_at == null || utcDate(item.merged_at) !== null)
      && (item.milestone?.due_on == null || utcDate(item.milestone.due_on) !== null);
    if (!valid) { invalid += 1; continue; }
    normalized.push({
      id: item.id,
      number,
      title: item.title.slice(0, 500),
      html_url: item.html_url,
      created_at: item.created_at,
      ...(resource === "issues" ? {
        state: item.state,
        state_reason: ["completed", "not_planned", "duplicate"].includes(item.state_reason) ? item.state_reason : null,
        closed_at: item.closed_at ?? null,
      } : { merged_at: item.merged_at ?? null }),
      labels: Array.isArray(item.labels) ? item.labels.map((label) => typeof label === "string" ? label : label?.name).filter((name) => typeof name === "string").map((name) => name.slice(0, 100)) : [],
      ...(resource === "issues" && item.milestone ? {
        milestone: {
          title: typeof item.milestone.title === "string" ? item.milestone.title.slice(0, 200) : null,
          due_on: item.milestone.due_on ?? null,
        },
      } : {}),
    });
  }
  const partial = initialState !== "VERIFIED" || invalid > 0;
  const reason = [initialReason, invalid ? `${invalid} malformed ${resource} record(s) were excluded.` : null].filter(Boolean).join(" ") || null;
  return { items: normalized, state: partial ? "PARTIAL" : "VERIFIED", reason };
}

/**
 * @param {{state:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",items:Array<unknown>|null,asOf:string|null,reason?:string|null}} snapshot
 * @returns {{state:string,count:number|null,asOf:string|null,reason:string|null}}
 */
export function sourceSnapshot({ state, items, asOf, reason = null }) {
  const availableState = ["VERIFIED", "PARTIAL", "STALE"].includes(state);
  return {
    state,
    count: availableState && Array.isArray(items) ? items.length : null,
    asOf: typeof asOf === "string" ? asOf : null,
    reason: typeof reason === "string" && reason.length ? reason : null,
  };
}

/** Historical issue reopen events are not available in the current Issues projection. */
export function buildEventCoverage(issueState, pullState) {
  const issues = SOURCE_STATES.includes(issueState) ? issueState : "UNAVAILABLE";
  const pulls = SOURCE_STATES.includes(pullState) ? pullState : "UNAVAILABLE";
  return {
    issue_opened: issues,
    issue_completed: issues === "UNAVAILABLE" ? "UNAVAILABLE" : issues === "STALE" ? "STALE" : "PARTIAL",
    pr_merged: pulls,
  };
}

/** Keep a partial page cached while its provider retry window is still active. */
export function sourceCacheEntryIsFresh(entry, now, ttlMs) {
  if (!entry || !Number.isFinite(entry.savedAt)) return false;
  if (Number.isFinite(entry.nextRetryAt)) return now < entry.nextRetryAt;
  if (entry.state === "UNAVAILABLE") return false;
  return now - entry.savedAt < ttlMs;
}

/** Retain a partial/unavailable cache marker through its retry time. */
export function sourceCacheRetentionMs(entry, layer, currentTtlMs, verifiedTtlMs) {
  if (layer === "verified" && entry?.state === "VERIFIED") return verifiedTtlMs;
  const retryWindow = Number.isFinite(entry?.nextRetryAt) && Number.isFinite(entry?.savedAt)
    ? Math.max(0, entry.nextRetryAt - entry.savedAt)
    : 0;
  return Math.max(currentTtlMs, retryWindow);
}

/** Read a provider retry timestamp without inferring one from an ordinary failure. */
export function retryAtFromReason(reason) {
  const match = typeof reason === "string" ? reason.match(/retry after (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z)(?:[.;,\s]|$)/i) : null;
  const timestamp = match ? Date.parse(match[1]) : NaN;
  return Number.isFinite(timestamp) ? timestamp : null;
}

/** GitHub connector results may wrap JSON in a structured payload or text block. */
export function parseGithubPage(value) {
  const pending = [value];
  while (pending.length) {
    const current = pending.shift();
    if (Array.isArray(current)) return current;
    if (typeof current === "string") {
      try { pending.push(JSON.parse(current)); } catch { /* Ignore non-JSON content. */ }
    } else if (current && typeof current === "object") {
      if (Array.isArray(current.items)) return current.items;
      if (Array.isArray(current.data)) return current.data;
      if (current.structuredContent !== undefined) pending.push(current.structuredContent);
      if (Array.isArray(current.content)) {
        for (const block of current.content) if (block && typeof block.text === "string") pending.push(block.text);
      }
    }
  }
  return null;
}


/** Fetch bounded numbered pages; overlaps and incomplete reads never claim completeness. */
export async function collectPages(fetchPage, { pageSize = 100, maxPages = 10 } = {}) {
  const items = [];
  const seen = new Set();
  let overlap = false;
  for (let page = 1; page <= maxPages; page += 1) {
    let pageItems;
    try { pageItems = await fetchPage(page); } catch (error) {
      const reason = error instanceof Error && error.message ? error.message : "Source read failed.";
      return items.length
        ? { items, state: "PARTIAL", reason }
        : { items: null, state: "UNAVAILABLE", reason };
    }
    if (!Array.isArray(pageItems)) {
      const reason = "Source response did not contain a readable JSON page.";
      return items.length
        ? { items, state: "PARTIAL", reason }
        : { items: null, state: "UNAVAILABLE", reason };
    }
    for (const item of pageItems) {
      const row = item && typeof item === "object" ? item : null;
      const id = row && (Number.isSafeInteger(row.id) ? `id:${row.id}` : Number.isSafeInteger(row.number) ? `number:${row.number}` : null);
      if (id && seen.has(id)) { overlap = true; continue; }
      if (id) seen.add(id);
      items.push(item);
    }
    if (pageItems.length < pageSize) {
      return overlap
        ? { items, state: "PARTIAL", reason: "Paginated pages overlapped; completeness could not be verified." }
        : { items, state: "VERIFIED", reason: null };
    }
  }
  return { items, state: "PARTIAL", reason: overlap
    ? "Paginated pages overlapped and reached the page safety limit."
    : `Read reached the ${maxPages}-page safety limit.` };
}

/** Safe, single retry for idempotent REST reads; never wait through a long provider reset. */
export async function withBoundedGithubRetry(fetcher, url, { sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)), maxDelayMs = 2000 } = {}) {
  let retries = 0;
  while (true) {
    let response;
    try {
      response = await fetcher(url);
    } catch (error) {
      if (retries === 0 && error?.name === "TimeoutError") {
        retries += 1;
        await sleep(200);
        continue;
      }
      throw error;
    }
    const rateLimited = response?.status === 429 || (response?.status === 403 && response?.headers?.get("x-ratelimit-remaining") === "0");
    if (!rateLimited || retries > 0) return response;
    const retryAfter = response.headers.get("retry-after");
    const reset = response.headers.get("x-ratelimit-reset");
    const delay = retryAfter && /^\d+$/.test(retryAfter)
      ? Number(retryAfter) * 1000
      : reset && /^\d+$/.test(reset)
        ? Number(reset) * 1000 - Date.now()
        : Number.POSITIVE_INFINITY;
    if (!Number.isFinite(delay) || delay < 0 || delay > maxDelayMs) return response;
    retries += 1;
    await sleep(delay);
  }
}
