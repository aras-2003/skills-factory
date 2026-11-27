"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildHeatmap,
} from "@/lib/product-intelligence.mjs";

type SourceState = "VERIFIED" | "PARTIAL" | "STALE" | "UNAVAILABLE";
type SourceSnapshot = { state: SourceState; asOf: string | null; reason: string | null; count?: number | null };
type RoadmapItem = { number: number; title: string; url: string; workArea: string; priorityLabel: string; createdAt: string | null; milestone: string | null; milestoneDue: string | null; projectFields: "UNAVAILABLE" };
type DashboardData = {
  asOf: string;
  snapshotState?: SourceState;
  staleReason?: string | null;
  sources: {
    github: SourceSnapshot & { issues: SourceSnapshot; pulls: SourceSnapshot };
    runtime: SourceSnapshot & { identity: Record<string, unknown> | null };
  };
  metrics: { skills: number | null; workflows: number | null; domains: number | null; openIssues: number | null; mergedPullRequests: number | null };
  roadmap: RoadmapItem[] | null;
  events: ActivityEvent[];
  eventCoverage: Record<ActivityEvent["type"], SourceState>;
  limitations: Record<string, string>;
};

type ActivityEvent = { id: string; sourceId: number; type: "issue_opened" | "issue_completed" | "pr_merged"; date: string; occurredAt: string; workArea: string; number: number; title: string; url: string };
type HeatmapData = { bins: Array<{ key: string; label: string; from: string; to: string }>; types: ActivityEvent["type"][]; cells: Array<{ type: ActivityEvent["type"]; date: string; count: number }>; complete: boolean; completeByType: Record<ActivityEvent["type"], boolean>; state: SourceState };
type WindowDays = 7 | 14 | 30;
type Aggregation = "day" | "week" | "month";

const stateLabels: Record<SourceState, string> = {
  VERIFIED: "Zweryfikowane",
  PARTIAL: "Częściowe",
  STALE: "Nieaktualne",
  UNAVAILABLE: "Niedostępne",
};
const eventLabels: Record<ActivityEvent["type"], string> = {
  issue_opened: "Nowe Issues",
  issue_completed: "Obecnie zamknięte jako ukończone",
  pr_merged: "Zmergowane PR",
};
const periods: WindowDays[] = [7, 14, 30];

function formatDate(value: string | null | undefined, withTime = false) {
  if (!value) return "—";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(date) + " UTC";
}

function StateBadge({ state }: { state: SourceState }) {
  return <span className={`pi-state pi-state-${state.toLowerCase()}`}>{stateLabels[state]}</span>;
}

function MetricCard({ label, value, detail }: { label: string; value: number | null; detail: string }) {
  return <article className="pi-metric"><span>{label}</span><strong>{value === null ? "—" : value.toLocaleString("pl-PL")}</strong><small>{detail}</small></article>;
}

function RuntimeIdentity({ identity }: { identity: Record<string, unknown> | null | undefined }) {
  if (!identity) return <small className="pi-reason">Wersje runtime niedostępne.</small>;
  const canonical = typeof identity.canonicalSourceRevision === "string" ? identity.canonicalSourceRevision : null;
  const lab = typeof identity.packagedLabRevision === "string" ? identity.packagedLabRevision : null;
  const mirror = typeof identity.siteMirrorRevision === "string" ? identity.siteMirrorRevision : null;
  const labMismatch = Boolean(canonical && lab && canonical !== lab);
  const revisionLink = (revision: string | null) => revision
    ? <a href={`https://github.com/aras-2003/skills-factory/commit/${revision}`} target="_blank" rel="noreferrer">{revision.slice(0, 12)}</a>
    : "Niedostępny";
  return <dl className="pi-identity">
    <dt>Canonical source</dt><dd>{revisionLink(canonical)}</dd>
    <dt>Embedded Lab</dt><dd>{revisionLink(lab)}</dd>
    <dt>Site mirror revision</dt><dd>{mirror ? <code>{mirror.slice(0, 12)}</code> : "Niedostępny"}</dd>
    <dt>Canonical ↔ Lab</dt><dd>{labMismatch ? "Rozbieżność wykryta" : canonical && lab ? "Zgodne" : "Nie można potwierdzić"}</dd>
    <dt>Mirror evidence</dt><dd>{mirror ? "Porównaj z rewizją zarejestrowaną przez workflow wdrożenia" : "Brak rewizji mirror"}</dd>
  </dl>;
}

function dateWindow(days: WindowDays) {
  const end = new Date();
  const endDay = end.toISOString().slice(0, 10);
  const start = new Date(`${endDay}T00:00:00.000Z`);
  start.setUTCDate(start.getUTCDate() - (days - 1));
  return { from: start.toISOString().slice(0, 10), to: endDay };
}

function validDateRange(from: string, to: string) {
  const validDay = (value: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const parsed = new Date(`${value}T00:00:00.000Z`);
    return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
  };
  if (!validDay(from) || !validDay(to) || from > to) return false;
  return (Date.parse(`${to}T00:00:00.000Z`) - Date.parse(`${from}T00:00:00.000Z`)) / 86_400_000 < 90;
}

function Heatmap({ data, range, aggregation, selectedTypes, onSelect, historical }: {
  data: DashboardData;
  range: { from: string; to: string };
  aggregation: Aggregation;
  selectedTypes: ActivityEvent["type"][];
  onSelect: (from: string, to: string, type: ActivityEvent["type"] | null) => void;
  historical: boolean;
}) {
  const sourceDate = data.sources.github.asOf?.slice(0, 10) ?? data.asOf.slice(0, 10);
  const clippedTo = range.to > sourceDate ? sourceDate : range.to;
  const eventCoverage = Object.fromEntries(Object.entries(data.eventCoverage).map(([type, state]) => [type, historical && state !== "UNAVAILABLE" ? "STALE" : state]));
  const heatmap: HeatmapData = buildHeatmap(data.events, {
    from: range.from,
    to: clippedTo,
    sourceState: historical && data.sources.github.state !== "UNAVAILABLE" ? "STALE" : data.sources.github.state,
    sourceStates: eventCoverage,
    period: aggregation,
  });
  if (!validDateRange(range.from, range.to)) return <div className="pi-empty" role="alert">Zakres musi być prawidłowy, chronologiczny i krótszy niż 90 dni.</div>;
  if (range.from > sourceDate) return <div className="pi-empty" role="status">Wybrany zakres zaczyna się po ostatnim odczycie źródła. Przyszłe daty nie są traktowane jako zero.</div>;
  if (data.sources.github.state === "UNAVAILABLE") {
    return <div className="pi-empty"><strong>Heatmapa niedostępna</strong><p>{data.sources.github.reason ?? "Źródło GitHub nie zwróciło danych."}</p></div>;
  }

  const counts = new Map(heatmap.cells.map((cell) => [`${cell.type}:${cell.date}`, cell.count]));
  const max = Math.max(1, ...heatmap.cells.map((cell) => cell.count));
  if (!selectedTypes.length) return <div className="pi-empty">Wybierz co najmniej jeden typ zdarzenia.</div>;
  return <div className="pi-heatmap-wrap">
    <div className="pi-heatmap-grid" style={{ gridTemplateColumns: `150px repeat(${heatmap.bins.length}, minmax(22px, 1fr))` }} role="group" aria-label={`Aktywność GitHub ${aggregation === "day" ? "dzienna" : aggregation === "week" ? "tygodniowa" : "miesięczna"}, daty UTC`}>
      <span aria-hidden="true" />
      {heatmap.bins.map((bin) => <span className="pi-date-heading" key={bin.key} title={`${bin.from} – ${bin.to} UTC`}>{bin.label}</span>)}
      {heatmap.types.filter((type) => selectedTypes.includes(type)).map((type) => <FragmentRow key={type} type={type} bins={heatmap.bins} counts={counts} max={max} complete={heatmap.completeByType[type]} onSelect={onSelect} />)}
    </div>
    <p className="pi-legend">Wartości liczą zdarzenia osobno. Puste przedziały pokazujemy jako zero wyłącznie przy zweryfikowanym, kompletnym odczycie danego typu. Zamknięcia oznaczają obecnie zamknięte Issues; bez historii ponownych otwarć ich pokrycie jest częściowe. Wszystkie granice są w UTC. {range.to > sourceDate ? `Zakres przyszły został ograniczony do ostatniego odczytu ${sourceDate}.` : ""}</p>
  </div>;
}

function FragmentRow({ type, bins, counts, max, complete, onSelect }: {
  type: ActivityEvent["type"]; bins: HeatmapData["bins"]; counts: Map<string, number>; max: number; complete: boolean;
  onSelect: (from: string, to: string, type: ActivityEvent["type"] | null) => void;
}) {
  return <>
    <span className="pi-row-label">{eventLabels[type]}{complete ? "" : " · obserwowane"}</span>
    {bins.map((bin) => {
      const count = counts.get(`${type}:${bin.key}`);
      if (count === undefined && !complete) return <span key={bin.key} role="img" className="pi-heat-cell pi-heat-unknown" aria-label={`${eventLabels[type]}: brak kompletnego odczytu dla ${bin.from}–${bin.to} UTC`} />;
      const value = count ?? 0;
      const level = value === 0 ? 0 : Math.min(4, Math.ceil((value / max) * 4));
      return <button
        key={bin.key}
        type="button"
        className={`pi-heat-cell pi-heat-${level}`}
        aria-label={`${eventLabels[type]}: ${complete ? value : `co najmniej ${value}`} w zakresie ${bin.from}–${bin.to} UTC`}
        title={`${bin.from}–${bin.to} UTC · ${eventLabels[type]}: ${complete ? value : `co najmniej ${value}`}`}
        onClick={() => onSelect(bin.from, bin.to, type)}
      >{value || ""}</button>;
    })}
  </>;
}

export default function IntelligenceDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const dataRef = useRef<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historical, setHistorical] = useState(false);
  const [range, setRange] = useState(() => dateWindow(30));
  const [aggregation, setAggregation] = useState<Aggregation>("day");
  const [selectedTypes, setSelectedTypes] = useState<ActivityEvent["type"][]>(["issue_opened", "issue_completed", "pr_merged"]);
  const refreshSequence = useRef(0);
  const [eventFilter, setEventFilter] = useState<{ from: string; to: string; type: ActivityEvent["type"] | null } | null>(null);
  const [roadmapQuery, setRoadmapQuery] = useState("");
  const [workAreaFilter, setWorkAreaFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");

  const refresh = useCallback(async (signal?: AbortSignal) => {
    const requestId = ++refreshSequence.current;
    if (!dataRef.current) setLoading(true);
    else setRefreshing(true);
    try {
      const response = await fetch("/api/intelligence", { cache: "no-store", signal });
      if (requestId !== refreshSequence.current) return;
      if (response.status === 401 || response.status === 403) {
        dataRef.current = null;
        setData(null);
        setHistorical(false);
        throw new Error("Brak autoryzacji Site. Zaloguj się ponownie, aby odczytać Product Intelligence.");
      }
      if (!response.ok) throw new Error("Nie udało się odczytać źródeł Product Intelligence.");
      const next = await response.json() as DashboardData;
      if (requestId !== refreshSequence.current) return;
      dataRef.current = next;
      setData(next);
      if (next.snapshotState === "STALE") {
        setError(next.staleReason ?? "Wyświetlany snapshot jest historyczny.");
        setHistorical(true);
      } else {
        setError(null);
        setHistorical(false);
      }
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      if (requestId !== refreshSequence.current) return;
      const message = cause instanceof Error ? cause.message : "Nie udało się odczytać źródeł.";
      setError(message);
      if (dataRef.current) setHistorical(true);
    } finally {
      if (requestId === refreshSequence.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const initial = window.setTimeout(() => void refresh(controller.signal), 0);
    const interval = window.setInterval(() => void refresh(), 60_000);
    return () => { controller.abort(); window.clearTimeout(initial); window.clearInterval(interval); };
  }, [refresh]);

  const filteredEvents = useMemo(() => {
    const events = [...(data?.events ?? [])].reverse();
    if (!eventFilter) return events.slice(0, 10);
    return events.filter((event) => event.date >= eventFilter.from && event.date <= eventFilter.to && (!eventFilter.type || event.type === eventFilter.type));
  }, [data, eventFilter]);

  const roadmapOptions = useMemo(() => ({
    workAreas: [...new Set(data?.roadmap?.map((item) => item.workArea) ?? [])].sort(),
    priorities: [...new Set(data?.roadmap?.map((item) => item.priorityLabel) ?? [])].sort(),
  }), [data]);
  const filteredRoadmap = useMemo(() => (data?.roadmap ?? []).filter((item) => {
    const needle = roadmapQuery.trim().toLocaleLowerCase();
    return (!needle || `#${item.number} ${item.title}`.toLocaleLowerCase().includes(needle))
      && (workAreaFilter === "all" || item.workArea === workAreaFilter)
      && (priorityFilter === "all" || item.priorityLabel === priorityFilter);
  }), [data, roadmapQuery, workAreaFilter, priorityFilter]);

  if (loading && !data) return <main className="pi-page"><header className="pi-header"><Link href="/" className="brand"><span className="mark">S</span><span>Skills Factory <strong>Cloud</strong></span></Link><span>Product Intelligence</span></header><div className="pi-loading" role="status">Odczytuję źródła…</div></main>;

  const visibleGithubState = historical && data?.sources.github.state !== "UNAVAILABLE" ? "STALE" : data?.sources.github.state ?? "UNAVAILABLE";
  const openIssueState = historical && data?.sources.github.issues.state !== "UNAVAILABLE" ? "STALE" : data?.sources.github.issues.state ?? "UNAVAILABLE";
  const mergedPrState = historical && data?.sources.github.pulls.state !== "UNAVAILABLE" ? "STALE" : data?.sources.github.pulls.state ?? "UNAVAILABLE";
  const visibleRuntimeState = historical && data?.sources.runtime.state !== "UNAVAILABLE" ? "STALE" : data?.sources.runtime.state ?? "UNAVAILABLE";
  const runtimeIdentity = data?.sources.runtime.identity;
  const runtimeAttestation = typeof runtimeIdentity?.attestationStatus === "string" ? runtimeIdentity.attestationStatus : "unknown";

  return <main className="pi-page">
    <header className="pi-header">
      <Link href="/" className="brand" aria-label="Skills Factory Cloud — strona główna"><span className="mark">S</span><span>Skills Factory <strong>Cloud</strong></span></Link>
      <nav aria-label="Nawigacja główna"><Link href="/">Katalog Lab</Link><span aria-current="page">Product Intelligence</span></nav>
    </header>
    <div className="pi-content">
      <div className="pi-title-row">
        <div><p className="eyebrow">SKILLS FACTORY / PRODUCT INTELLIGENCE</p><h1>Centrum rozwoju produktu</h1><p className="pi-lead">Prywatny widok zmian z GitHub i wersjonowanego katalogu MCP, z widoczną świeżością oraz granicami danych.</p></div>
        <button className="pi-refresh" type="button" title="Sprawdza stan cache; GitHub REST jest odświeżany najwyżej co 10 minut." onClick={() => void refresh()} disabled={refreshing}>{refreshing ? "Odświeżam widok…" : "Odśwież widok"}</button>
      </div>

      {error && <div className={`pi-alert ${historical ? "pi-alert-stale" : ""}`} role="status"><strong>{historical ? "Pokazuję poprzedni odczyt" : "Odczyt nie powiódł się"}</strong><span>{error}{historical && data ? ` Snapshot pochodzi z ${formatDate(data.asOf, true)} i jest utrzymywany tylko w cache serwera lub stanie tej karty.` : ""}</span></div>}

      <section className="pi-overview" aria-labelledby="overview-heading">
        <div className="pi-section-head"><div><h2 id="overview-heading">Executive overview</h2><p>Ostatnia aktualizacja: {formatDate(data?.asOf, true)} · odczyty i grupowanie dat w UTC</p></div><StateBadge state={visibleGithubState} /></div>
        <div className="pi-metrics">
          <MetricCard label="Skills" value={data?.metrics.skills ?? null} detail="Wersjonowany katalog MCP" />
          <MetricCard label="Workflows" value={data?.metrics.workflows ?? null} detail="Zadeklarowane w katalogu" />
          <MetricCard label="Domeny katalogu" value={data?.metrics.domains ?? null} detail="Wartość z metadanych MCP" />
          <MetricCard label="Otwarte Issues" value={data?.metrics.openIssues ?? null} detail={stateLabels[openIssueState]} />
          <MetricCard label="Zmergowane PR" value={data?.metrics.mergedPullRequests ?? null} detail={stateLabels[mergedPrState]} />
          <MetricCard label="Native Project WIP" value={null} detail="Natywne pola i iteracje: niedostępne" />
        </div>
      </section>

      <section className="pi-sources" aria-label="Stan źródeł danych">
        <article className="pi-source-card"><div><h2>GitHub</h2><StateBadge state={visibleGithubState} /></div><p>Issues i Pull Requests repozytorium <a href="https://github.com/aras-2003/skills-factory" target="_blank" rel="noreferrer">aras-2003/skills-factory</a>.</p><small>Issues: {stateLabels[openIssueState]} · {formatDate(data?.sources.github.issues.asOf, true)}</small><small>Pull Requests: {stateLabels[mergedPrState]} · {formatDate(data?.sources.github.pulls.asOf, true)}</small>{data?.sources.github.issues.reason && <small className="pi-reason">Issues: {data.sources.github.issues.reason}</small>}{data?.sources.github.pulls.reason && <small className="pi-reason">Pull Requests: {data.sources.github.pulls.reason}</small>}</article>
        <article className="pi-source-card"><div><h2>Site MCP</h2><StateBadge state={visibleRuntimeState} /></div><p>Katalog jest odczytywany lokalnie w istniejącym runtime Site.</p><small>Tożsamość wdrożenia: {historical ? "historyczna" : runtimeAttestation === "VERIFIED" ? "zweryfikowana" : "niepotwierdzona"}</small><small>Ostatni odczyt: {formatDate(data?.sources.runtime.asOf, true)}</small><RuntimeIdentity identity={runtimeIdentity} />{data?.sources.runtime.reason && <small className="pi-reason">{data.sources.runtime.reason}</small>}</article>
        <article className="pi-source-card"><div><h2>Project V2 i operacje</h2><StateBadge state="UNAVAILABLE" /></div><p>{data?.limitations.projectV2}</p><small>{data?.limitations.workflowTelemetry}</small></article>
      </section>

      <section className="pi-panel" aria-labelledby="heatmap-heading">
        <div className="pi-section-head"><div><h2 id="heatmap-heading">Heatmapa zdarzeń GitHub</h2><p>Issues i PR z osobnymi typami zdarzeń. Etykiety GitHub opisują obszary pracy, nie domeny biznesowe.</p></div></div>
        <div className="pi-heat-controls">
          <label>Od (UTC)<input type="date" max={data?.sources.github.asOf?.slice(0, 10) ?? undefined} value={range.from} onChange={(event) => { setRange((current) => ({ ...current, from: event.target.value })); setEventFilter(null); }} /></label>
          <label>Do (UTC)<input type="date" max={data?.sources.github.asOf?.slice(0, 10) ?? undefined} value={range.to} onChange={(event) => { setRange((current) => ({ ...current, to: event.target.value })); setEventFilter(null); }} /></label>
          <div className="pi-periods" role="group" aria-label="Szybki zakres">{periods.map((period) => <button key={period} type="button" aria-pressed={range.from === dateWindow(period).from && range.to === dateWindow(period).to} onClick={() => { setRange(dateWindow(period)); setEventFilter(null); }}>{period} dni</button>)}</div>
          <label>Agregacja<select value={aggregation} onChange={(event) => setAggregation(event.target.value as Aggregation)}><option value="day">Dzienna</option><option value="week">Tygodniowa</option><option value="month">Miesięczna</option></select></label>
        </div>
        <div className="pi-event-filters" role="group" aria-label="Typy zdarzeń heatmapy">{Object.entries(eventLabels).map(([type, label]) => { const value = type as ActivityEvent["type"]; const checked = selectedTypes.includes(value); return <button key={type} type="button" aria-pressed={checked} onClick={() => setSelectedTypes((current) => checked ? current.filter((item) => item !== value) : [...current, value])}>{label}</button>; })}</div>
        {data ? <Heatmap data={data} range={range} aggregation={aggregation} selectedTypes={selectedTypes} historical={historical} onSelect={(from, to, type) => setEventFilter({ from, to, type })} /> : <div className="pi-empty">Brak odczytu.</div>}
        <p className="pi-legend">Zmiany capabilities, deploymenty, testy runtime, workflow runs, błędy i regresje nie są dostępne w tym przyroście.</p>
      </section>

      <section className="pi-panel" aria-labelledby="roadmap-heading">
        <div className="pi-section-head"><div><h2 id="roadmap-heading">Roadmap Explorer</h2><p>Otwarty backlog GitHub i natywne Project pola pozostają osobnymi źródłami.</p></div><a className="pi-inline-link" href="https://github.com/users/aras-2003/projects/1" target="_blank" rel="noreferrer">Otwórz GitHub Project</a></div>
        <div className="pi-boundary"><strong>Ograniczenie źródła</strong><span>Lista poniżej obejmuje otwarte GitHub Issues. Nie odzwierciedla natywnego statusu Project V2, iteracji ani estymacji. Milestone i termin pokazujemy tylko wtedy, gdy są zapisane bezpośrednio w Issue.</span></div>
        {data?.roadmap === null || data?.roadmap === undefined ? <div className="pi-empty"><strong>Roadmap niedostępna</strong><p>{data?.sources.github.issues.reason ?? "Nie uzyskano potwierdzonego odczytu Issues."}</p></div> : data.roadmap.length === 0 ? <div className="pi-empty"><strong>Brak otwartych Issues w odczytanym zakresie</strong><p>{openIssueState === "VERIFIED" ? "Kompletny odczyt zwrócił zero otwartych Issues." : "Częściowy odczyt nie pozwala potwierdzić zera."}</p></div> : <>
          <div className="pi-roadmap-filters"><label>Szukaj Issue<input type="search" value={roadmapQuery} onChange={(event) => setRoadmapQuery(event.target.value)} placeholder="Numer lub tytuł" /></label><label>Obszar pracy<select value={workAreaFilter} onChange={(event) => setWorkAreaFilter(event.target.value)}><option value="all">Wszystkie</option>{roadmapOptions.workAreas.map((value) => <option key={value} value={value}>{value}</option>)}</select></label><label>GitHub priority label<select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)}><option value="all">Wszystkie</option>{roadmapOptions.priorities.map((value) => <option key={value} value={value}>{value}</option>)}</select></label></div>
          <p className="pi-legend">Priorytet i obszar pochodzą z etykiet GitHub; nie są natywnymi polami Project. {filteredRoadmap.length} z {data.roadmap.length} Issues w tym odczycie.</p>
          {filteredRoadmap.length === 0 ? <div className="pi-empty">Brak Issues pasujących do filtrów.</div> : <div className="pi-table-wrap"><table className="pi-table"><thead><tr><th>Issue</th><th>Obszar pracy</th><th>Priority label</th><th>Milestone</th><th>Termin milestone</th><th>Project status</th></tr></thead><tbody>{filteredRoadmap.map((item) => <tr key={item.number}><td><a href={item.url} target="_blank" rel="noreferrer"><strong>#{item.number}</strong> {item.title}</a></td><td>{item.workArea}</td><td>{item.priorityLabel}</td><td>{item.milestone ?? "—"}</td><td>{formatDate(item.milestoneDue)}</td><td><span className="pi-unavailable">Niedostępny</span></td></tr>)}</tbody></table></div>}
        </>}
      </section>

      <section className="pi-panel" aria-labelledby="events-heading">
        <div className="pi-section-head"><div><h2 id="events-heading">Ostatnie zmiany</h2><p>{eventFilter ? `Filtr: ${eventFilter.from}–${eventFilter.to} UTC · ${eventFilter.type ? eventLabels[eventFilter.type] : "wszystkie typy"}` : "Najnowsze zdarzenia z dostępnego odczytu"}</p></div>{eventFilter && <button className="pi-reset" type="button" onClick={() => setEventFilter(null)}>Wyczyść filtr</button>}</div>
        {!data?.events.length ? <div className="pi-empty"><strong>Brak zdarzeń do pokazania</strong><p>{data?.sources.github.state === "VERIFIED" ? "Kompletny odczyt nie zawiera zdarzeń w zakresie." : data?.sources.github.reason ?? "Dane źródłowe są niedostępne."}</p></div> : filteredEvents.length === 0 ? <div className="pi-empty">Brak zdarzeń dla wybranej komórki heatmapy.</div> : <ul className="pi-events">{filteredEvents.map((event) => <li key={event.id}><time dateTime={event.occurredAt}>{formatDate(event.occurredAt, true)}</time><span className="pi-event-type">{eventLabels[event.type]}</span><span className="pi-event-area">{event.workArea}</span><a href={event.url} target="_blank" rel="noreferrer">#{event.number} {event.title}</a></li>)}</ul>}
      </section>

      <section className="pi-limits" aria-label="Źródła niedostępne">
        <h2>Źródła poza P0</h2><div><span>{data?.limitations.deployments}</span><span>{data?.limitations.supabase}</span><span>Wartość biznesowa i koszty wykonania: brak zweryfikowanego źródła metryk.</span></div>
      </section>

      <footer className="pi-footer">Widok sprawdza serwer co 60 s; GitHub REST jest pobierany najwyżej co 10 min i może pochodzić z cache. Cache LKG może zostać usunięty po evikcji · dane ze snapshotu {formatDate(data?.asOf, true)}</footer>
    </div>
  </main>;
}
