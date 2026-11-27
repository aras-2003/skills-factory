const EVENT_TYPES = Object.freeze(["issue_opened", "issue_completed", "pr_merged"]);
const REPOSITORY_PATH = "/aras-2003/skills-factory/";

function utcDate(value) {
  if (typeof value !== "string" || !value) return null;
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
    if (record.row.state === "closed" && record.row.state_reason !== "not_planned") {
      add("issue_completed", record, record.row.closed_at);
    }
  }

  for (const raw of Array.isArray(pulls) ? pulls : []) {
    const record = validRecord(raw, "pull");
    if (!record) continue;
    add("pr_merged", record, record.row.merged_at);
  }

  return events.sort((a, b) => a.date.localeCompare(b.date) || a.type.localeCompare(b.type) || a.number - b.number);
}

/**
 * @param {Array<{type:string,date:string}>} events
 * @param {{from:string,to:string,sourceState?:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",period?:"day"|"week"|"month"}} options
 * @returns {{bins:Array<{key:string,label:string,from:string,to:string}>,types:Array<"issue_opened"|"issue_completed"|"pr_merged">,cells:Array<{type:"issue_opened"|"issue_completed"|"pr_merged",date:string,count:number}>,complete:boolean,state:"VERIFIED"|"PARTIAL"|"STALE"|"UNAVAILABLE",period:string}}
 */
export function buildHeatmap(events, { from, to, sourceState = "UNAVAILABLE", period = "day" }) {
  const start = utcDate(from);
  const end = utcDate(to);
  const state = ["VERIFIED", "PARTIAL", "STALE", "UNAVAILABLE"].includes(sourceState) ? sourceState : "UNAVAILABLE";
  if (!start || !end || start > end || state === "UNAVAILABLE" || !["day", "week", "month"].includes(period)) {
    return { bins: [], types: [...EVENT_TYPES], cells: [], complete: false, state, period };
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
    const key = `${event.type}:${binKey}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const cells = [...counts.entries()].map(([key, count]) => {
    const split = key.indexOf(":");
    return { type: key.slice(0, split), date: key.slice(split + 1), count };
  }).sort((a, b) => a.date.localeCompare(b.date) || a.type.localeCompare(b.type));
  return { bins, types: [...EVENT_TYPES], cells, complete: state === "VERIFIED", state, period };
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
