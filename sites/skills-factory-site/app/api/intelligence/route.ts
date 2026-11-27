import { callTool } from "@/lib/skills-factory-adapter/cloud-tools";
import { getChatGPTUser } from "@/app/chatgpt-auth";
import { env } from "cloudflare:workers";
import type { SiteVersionMetadata } from "@/lib/skills-factory-adapter/cloud-tools";
import {
  buildGithubActivity,
  collectPages,
  parseGithubPage,
  priorityLabelFromLabels,
  repositoryUrl,
  sourceSnapshot,
  withBoundedGithubRetry,
  workAreaFromLabels,
} from "@/lib/product-intelligence.mjs";

export const dynamic = "force-dynamic";

const OWNER = "aras-2003";
const REPOSITORY = "skills-factory";
const PAGE_SIZE = 100;
const MAX_PAGES = 3;
const CACHE_TTL_MS = 10 * 60 * 1000;
const LAST_KNOWN_GOOD_TTL_MS = 24 * 60 * 60 * 1000;
const GITHUB_API_BASE = "https://api.github.com";
const SAFE_HEADERS = {
  "Cache-Control": "no-store, max-age=0",
  "X-Content-Type-Options": "nosniff",
};

type SourceState = "VERIFIED" | "PARTIAL" | "STALE" | "UNAVAILABLE";
type Collection = { items: unknown[] | null; state: Exclude<SourceState, "STALE">; reason: string | null };
type CachedSnapshot = { savedAt: number; nextRetryAt?: number; data: Record<string, unknown> };

let memorySnapshot: CachedSnapshot | null = null;
let inFlightSnapshot: ReturnType<typeof buildSnapshot> | null = null;

function json(data: unknown, status = 200) {
  return Response.json(data, { status, headers: SAFE_HEADERS });
}

function pageUrl(resource: "issues" | "pulls", page: number) {
  const url = new URL(`/repos/${OWNER}/${REPOSITORY}/${resource}`, GITHUB_API_BASE);
  url.searchParams.set("state", "all");
  url.searchParams.set("per_page", String(PAGE_SIZE));
  url.searchParams.set("page", String(page));
  url.searchParams.set("sort", "updated");
  url.searchParams.set("direction", "desc");
  return url.href;
}

function retryTime(response: Response): string | null {
  const retryAfter = response.headers.get("retry-after");
  if (retryAfter && /^\d+$/.test(retryAfter)) {
    return new Date(Date.now() + Number(retryAfter) * 1000).toISOString();
  }
  const reset = response.headers.get("x-ratelimit-reset");
  if (reset && /^\d+$/.test(reset)) {
    const timestamp = Number(reset) * 1000;
    if (Number.isFinite(timestamp)) return new Date(timestamp).toISOString();
  }
  return null;
}

async function fetchGithubPage(resource: "issues" | "pulls", page: number) {
  let response: Response;
  try {
    response = await withBoundedGithubRetry((url: string) => fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SkillsFactory-ProductIntelligence/1.0",
      },
      signal: AbortSignal.timeout(10_000),
      cache: "no-store",
    }), pageUrl(resource, page));
  } catch {
    throw new Error("GitHub REST could not be reached from this Site runtime.");
  }
  if (response.status === 403 || response.status === 429 || response.headers.get("x-ratelimit-remaining") === "0") {
    const retryAt = retryTime(response);
    throw new Error(`GitHub rate limited the read. The bounded retry limit was reached${retryAt ? `; retry after ${retryAt}` : ""}.`);
  }
  if (!response.ok) {
    if (response.status === 404) throw new Error("GitHub REST did not expose this repository to the Site runtime.");
    throw new Error(`GitHub REST returned HTTP ${response.status}; no retry was made.`);
  }
  try {
    return parseGithubPage(await response.json());
  } catch {
    throw new Error("GitHub REST did not return a readable JSON page.");
  }
}

async function loadCollection(resource: "issues" | "pulls"): Promise<Collection> {
  return collectPages((page: number) => fetchGithubPage(resource, page), {
    pageSize: PAGE_SIZE,
    maxPages: MAX_PAGES,
  }) as Promise<Collection>;
}

function combinedState(states: Collection["state"][]): Exclude<SourceState, "STALE"> {
  if (states.every((state) => state === "VERIFIED")) return "VERIFIED";
  if (states.some((state) => state !== "UNAVAILABLE")) return "PARTIAL";
  return "UNAVAILABLE";
}

function normalizeRuntimeIdentity(value: unknown) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const row = value as Record<string, unknown>;
  const lab = row.lab_release && typeof row.lab_release === "object" && !Array.isArray(row.lab_release)
    ? row.lab_release as Record<string, unknown>
    : {};
  const safeText = (input: unknown, max = 200) => typeof input === "string" && input.length <= max ? input : null;
  const safeSha = (input: unknown) => typeof input === "string" && /^[a-f0-9]{40}$/.test(input) ? input : null;
  return {
    attestationStatus: row.attestation_status === "verified" ? "VERIFIED" : "UNATTESTED",
    siteMirrorRevision: safeSha(row.source_revision),
    identitySource: safeText(row.identity_source, 80),
    releaseId: safeText(row.release_id, 120),
    canonicalSourceRevision: safeSha(row.github_main_revision),
    packagedLabRevision: safeSha(lab.source_revision),
    packagedLabVersion: safeText(lab.version, 80),
    deployedAt: safeText(row.deployed_at, 40),
    siteChannel: safeText(row.channel, 80),
    contractVersion: safeText(row.capability_contract_version, 80),
  };
}

function edgeCache(): Cache | undefined {
  return (globalThis.caches as unknown as { default?: Cache } | undefined)?.default;
}

function cacheKey(request: Request) {
  const url = new URL("/api/intelligence?__snapshot=github-v1", request.url);
  return new Request(url, { method: "GET" });
}

async function readCachedSnapshot(key: Request): Promise<CachedSnapshot | null> {
  try {
    if (edgeCache()) {
      const response = await edgeCache()!.match(key);
      if (response) {
        const entry = await response.json() as CachedSnapshot;
        if (entry && Number.isFinite(entry.savedAt) && entry.data && typeof entry.data === "object") {
          memorySnapshot = entry;
          return entry;
        }
      }
    }
  } catch { /* Cache eviction or unavailability falls back to the current isolate only. */ }
  return memorySnapshot;
}

async function writeCachedSnapshot(key: Request, data: Record<string, unknown>, savedAt: number, nextRetryAt?: number) {
  const entry = { savedAt, ...(nextRetryAt ? { nextRetryAt } : {}), data };
  memorySnapshot = entry;
  try {
    if (edgeCache()) {
      await edgeCache()!.put(key, Response.json(entry, {
        headers: { "Cache-Control": `public, max-age=${Math.floor(LAST_KNOWN_GOOD_TTL_MS / 1000)}` },
      }));
    }
  } catch { /* A regional cache is best-effort; the API remains read-only. */ }
}

function staleSnapshot(snapshot: CachedSnapshot, reason: string) {
  const previous = structuredClone(snapshot.data);
  const sources = previous.sources as Record<string, Record<string, unknown>>;
  const github = sources.github;
  github.state = "STALE";
  github.reason = reason;
  for (const key of ["issues", "pulls"]) {
    const source = github[key] as Record<string, unknown> | undefined;
    if (source) source.state = "STALE";
  }
  const runtime = sources.runtime;
  if (runtime) runtime.state = "STALE";
  previous.snapshotState = "STALE";
  previous.staleReason = reason;
  return previous;
}

function isReadFailure(collection: Collection) {
  return collection.state === "UNAVAILABLE" || Boolean(collection.reason && !/safety limit|pages overlapped/i.test(collection.reason));
}

async function buildSnapshot() {
  let observedAt = "";
  let runtimeAsOf: string | null = null;
  let runtimeInfo: Record<string, unknown> | null = null;
  let skills: Array<Record<string, unknown>> | null = null;
  let runtimeReason: string | null = null;
  let catalogReason: string | null = null;
  const [runtimeResult, catalogResult] = await Promise.allSettled([
    callTool("runtime_info", {}, env.CF_VERSION_METADATA as SiteVersionMetadata),
    callTool("list_skills", {}),
  ]);
  runtimeAsOf = new Date().toISOString();
  if (runtimeResult.status === "fulfilled") runtimeInfo = normalizeRuntimeIdentity(runtimeResult.value);
  else runtimeReason = "The packaged runtime identity could not be read.";
  if (catalogResult.status === "fulfilled" && Array.isArray((catalogResult.value as { skills?: unknown }).skills)) {
    skills = (catalogResult.value as { skills: Array<Record<string, unknown>> }).skills;
  } else {
    catalogReason = "The packaged catalog did not return a skill list.";
  }

  const [issues, pulls] = await Promise.all([loadCollection("issues"), loadCollection("pulls")]);
  observedAt = new Date().toISOString();
  const issueItems = issues.items;
  const pullItems = pulls.items;
  const events = buildGithubActivity(issueItems ?? [], pullItems ?? []);
  const githubState = combinedState([issues.state, pulls.state]);
  const githubReason = [issues.reason, pulls.reason].filter(Boolean).join(" ") || null;
  const openIssues = issueItems?.filter((item) => {
    if (!item || typeof item !== "object") return false;
    const value = item as { state?: unknown; pull_request?: unknown };
    return value.state === "open" && !value.pull_request;
  }) ?? null;
  const mergedPulls = pullItems?.filter((item) => Boolean(item && typeof item === "object" && (item as { merged_at?: unknown }).merged_at)) ?? null;

  const catalogDomains = skills?.map((skill) => skill.domain)
    .filter((domain): domain is string => typeof domain === "string" && domain.length > 0) ?? [];
  const skillCount = skills?.filter((skill) => skill.kind === "skill").length ?? null;
  const workflowCount = skills?.filter((skill) => skill.kind === "workflow").length ?? null;

  const data = {
    asOf: observedAt,
    snapshotState: githubState === "UNAVAILABLE" ? "UNAVAILABLE" as SourceState
      : githubState === "PARTIAL" || runtimeInfo?.attestationStatus !== "VERIFIED" ? "PARTIAL" as SourceState
      : "VERIFIED" as SourceState,
    staleReason: null as string | null,
    sources: {
      github: {
        state: githubState as SourceState,
        asOf: githubState === "UNAVAILABLE" ? null : observedAt,
        reason: githubReason,
        issues: sourceSnapshot({ state: issues.state, items: issueItems, asOf: (issues.items === null ? null : observedAt) as string | null, reason: issues.reason }),
        pulls: sourceSnapshot({ state: pulls.state, items: pullItems, asOf: (pulls.items === null ? null : observedAt) as string | null, reason: pulls.reason }),
      },
      runtime: {
        state: skills === null ? "UNAVAILABLE" as SourceState : runtimeInfo?.attestationStatus === "VERIFIED" ? "VERIFIED" as SourceState : "PARTIAL" as SourceState,
        asOf: skills === null ? null : runtimeAsOf,
        reason: catalogReason ?? runtimeReason ?? (runtimeInfo?.attestationStatus === "VERIFIED" ? null : "Catalog is available; deployed runtime identity is not attested."),
        identity: runtimeInfo,
      },
    },
    metrics: {
      skills: skillCount,
      workflows: workflowCount,
      domains: skills === null ? null : new Set(catalogDomains).size,
      openIssues: openIssues?.length ?? null,
      mergedPullRequests: mergedPulls?.length ?? null,
    },
    roadmap: openIssues?.filter((item) => {
      const row = item as { html_url?: unknown; title?: unknown; number?: unknown };
      return typeof row.title === "string"
        && Number.isSafeInteger(Number(row.number))
        && repositoryUrl(row.html_url, "issues", Number(row.number)) !== null;
    }).map((item) => {
      const row = item as { html_url: string; title: string; number: number; labels?: Array<{ name?: string } | string>; created_at?: string; milestone?: { title?: string; due_on?: string } | null };
      return {
        number: row.number,
        title: row.title.slice(0, 500),
        url: repositoryUrl(row.html_url, "issues", row.number)!,
        workArea: workAreaFromLabels(row.labels),
        priorityLabel: priorityLabelFromLabels(row.labels),
        createdAt: row.created_at ?? null,
        milestone: row.milestone?.title ?? null,
        milestoneDue: row.milestone?.due_on ?? null,
        projectFields: "UNAVAILABLE" as const,
      };
    }) ?? null,
    events,
    limitations: {
      projectV2: "UNAVAILABLE: native Project fields and iterations are not exposed by this source.",
      deployments: "UNAVAILABLE: no deployment event reader is enabled.",
      workflowTelemetry: "UNAVAILABLE: runtime tool execution is not historical workflow telemetry.",
      supabase: "UNAVAILABLE: no safe aggregate read endpoint was verified.",
    },
  };
  return {
    data,
    readFailed: isReadFailure(issues) || isReadFailure(pulls),
    readFailureReason: [issues, pulls].filter(isReadFailure).map((source) => source.reason).filter(Boolean).join(" ") || null,
  };
}

export async function GET(request: Request) {
  if (!(await getChatGPTUser())) return json({ error: "Authenticated Site user required." }, 401);

  const key = cacheKey(request);
  const previous = await readCachedSnapshot(key);
  const now = Date.now();
  if (previous && now - previous.savedAt < CACHE_TTL_MS) return json(previous.data);
  if (previous?.nextRetryAt && now < previous.nextRetryAt && now - previous.savedAt < LAST_KNOWN_GOOD_TTL_MS) {
    const reason = `GitHub reads are paused until ${new Date(previous.nextRetryAt).toISOString()} UTC after the previous failure.`;
    return json(previous.data.snapshotState === "UNAVAILABLE"
      ? previous.data
      : staleSnapshot(previous, reason));
  }

  const snapshotPromise = inFlightSnapshot ?? (inFlightSnapshot = buildSnapshot());
  let current: Awaited<ReturnType<typeof buildSnapshot>>;
  try { current = await snapshotPromise; }
  finally {
    if (inFlightSnapshot === snapshotPromise) inFlightSnapshot = null;
  }

  if (current.readFailed) {
    const failureReason = current.readFailureReason ?? "Source read failed; last-known-good data is historical.";
    const retryAtMatch = failureReason.match(/retry after (\d{4}-\d{2}-\d{2}T[^ ]+)/i);
    const retryAt = retryAtMatch ? Date.parse(retryAtMatch[1]) : now + CACHE_TTL_MS;
    const nextRetryAt = Number.isFinite(retryAt) ? retryAt : now + CACHE_TTL_MS;
    if (previous && now - previous.savedAt < LAST_KNOWN_GOOD_TTL_MS) {
      const historical = staleSnapshot(previous, failureReason);
      await writeCachedSnapshot(key, previous.data, previous.savedAt, nextRetryAt);
      return json(historical);
    }
    const currentData = current.data as unknown as Record<string, unknown>;
    await writeCachedSnapshot(key, currentData, now, nextRetryAt);
    return json(currentData);
  }
  const currentData = current.data as unknown as Record<string, unknown>;
  await writeCachedSnapshot(key, currentData, now);
  return json(currentData);
}
