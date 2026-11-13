"use client";

import { useMemo, useState } from "react";
import { CATALOG } from "@/lib/skills-factory-adapter/cloud-tools";

const classifications = ["OWN", "EXTENDED", "IMPORTED", "COMPOSED", "UNKNOWN"] as const;
type ComponentLineageRecord = {
  name: string;
  kind: string;
  source: string;
  source_sha256: string;
  classification: string;
  components: ComponentLineageRecord[];
};
const catalog = CATALOG as unknown as readonly {
  name: string;
  kind: string;
  domain: string;
  description: string;
  version: string;
  maturity: string;
  canonical_source: string;
  canonical_source_revision: string;
  source_status: string;
  runtime_registration: string;
  lab_inclusion: string;
  declared_channels: Record<string, string>;
  required_dependencies: string[];
  optional_dependencies: string[];
  capability_assessment: string;
  provenance: {
    classification: string;
    source: string;
    source_sha256: string;
    upstream: null | { provider?: string; url?: string; path?: string; commit?: string; version?: string; content_sha256?: string };
    components: ComponentLineageRecord[];
    dependencies: string[];
    basis_evidence: string[];
    local_modifications: { status: string; items: string[] };
    license: { status: string; spdx_id: string | null; attribution: string[] };
    update_policy: string;
    verification: { state: string; reviewed_at: string | null; owner: string };
  };
}[];

function safeHttps(value: string | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function sourceUrl(entry: (typeof catalog)[number]): string | null {
  return canonicalSourceUrl(entry.canonical_source || entry.provenance?.source, entry.canonical_source_revision);
}

function canonicalSourceUrl(source: string | undefined, revision: string): string | null {
  if (!source || !/^(skills|workflows)\/[A-Za-z0-9._/-]+\.md$/.test(source) || source.split("/").includes("..")) return null;
  return `https://github.com/aras-2003/skills-factory/blob/${revision}/${source}`;
}

function ComponentLineage({ component, revision }: { component: ComponentLineageRecord; revision: string }) {
  const href = canonicalSourceUrl(component.source, revision);
  return <li>{href ? <a href={href} target="_blank" rel="noreferrer">{component.name} · {component.source}</a> : `${component.name} · ${component.source}`} <b className={`provenance-badge provenance-${(component.classification || "UNKNOWN").toLowerCase()}`}>{component.classification || "UNKNOWN"}</b>
    {component.components?.length ? <ul>{component.components.map((child) => <ComponentLineage key={`${child.kind}:${child.source}`} component={child} revision={revision}/>)}</ul> : null}
  </li>;
}

export function CatalogBrowser() {
  const [query, setQuery] = useState("");
  const [classification, setClassification] = useState("all");
  const [domain, setDomain] = useState("all");
  const domains = useMemo(() => [...new Set(catalog.map((item) => item.domain || "unknown"))].sort(), []);
  const visible = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    return catalog.filter((item) => {
      const state = item.provenance?.classification || "UNKNOWN";
      const text = [item.name, item.domain, item.kind, item.description, item.canonical_source, state].join(" ").toLocaleLowerCase();
      return (!needle || text.includes(needle)) && (classification === "all" || state === classification) && (domain === "all" || (item.domain || "unknown") === domain);
    });
  }, [query, classification, domain]);

  return <section className="catalog-browser" aria-labelledby="catalog-heading">
    <div className="catalog-heading-row"><div><p className="eyebrow">SOURCE LINEAGE</p><h2 id="catalog-heading">Katalog umiejętności i workflowów</h2><p className="catalog-intro">Pochodzenie, licencja, dojrzałość i dostępność są osobnymi informacjami. Żaden status nie oznacza automatycznie gotowości produkcyjnej.</p></div><span className="catalog-total" aria-live="polite">{visible.length} z {catalog.length}</span></div>

    <div className="catalog-legend" aria-label="Objaśnienie klasyfikacji pochodzenia">
      {classifications.map((state) => <span key={state}><b className={`provenance-badge provenance-${state.toLowerCase()}`}>{state}</b><small>{state === "OWN" ? "lokalne źródło" : state === "EXTENDED" ? "lokalne zmiany źródła zewnętrznego" : state === "IMPORTED" ? "źródło zewnętrzne" : state === "COMPOSED" ? "złożone z komponentów" : "nieustalone"}</small></span>)}
    </div>

    <div className="catalog-filters">
      <label>Szukaj<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nazwa, opis lub źródło" /></label>
      <label>Pochodzenie<select value={classification} onChange={(event) => setClassification(event.target.value)}><option value="all">Wszystkie klasyfikacje</option>{classifications.map((state) => <option key={state} value={state}>{state}</option>)}</select></label>
      <label>Domena<select value={domain} onChange={(event) => setDomain(event.target.value)}><option value="all">Wszystkie domeny</option>{domains.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
      <button type="button" className="catalog-reset" onClick={() => { setQuery(""); setClassification("all"); setDomain("all"); }}>Wyczyść filtry</button>
    </div>

    {visible.length ? <div className="catalog-cards">{visible.map((entry) => {
      const provenance = entry.provenance;
      const state = provenance?.classification || "UNKNOWN";
      const upstreamUrl = safeHttps(provenance?.upstream?.url);
      const canonicalUrl = sourceUrl(entry);
      return <article className="catalog-card" key={`${entry.kind}:${entry.name}`}>
        <div className="catalog-card-top"><div><span className="catalog-kind">{entry.kind === "workflow" ? "WORKFLOW" : "SKILL"} · {entry.domain || "unknown"}</span><h3>{entry.name}</h3></div><span className={`provenance-badge provenance-${state.toLowerCase()}`}>{state}</span></div>
        <p className="catalog-description">{entry.description}</p>
        <div className="catalog-statuses" aria-label="Status katalogowy"><span><b>Dojrzałość</b>{entry.maturity || "UNKNOWN"}</span><span><b>Źródło</b>{entry.source_status || "UNKNOWN"}</span><span><b>Pakiet Lab</b>{entry.lab_inclusion || "NOT_RECORDED"}</span><span><b>Rejestracja workflow</b>{entry.runtime_registration || "NOT_RECORDED"}</span><span><b>Weryfikacja provenance</b>{provenance?.verification?.state || "NOT_RECORDED"}</span></div>
        <details className="catalog-details"><summary>Szczegóły pochodzenia i dostępności</summary><dl>
          <dt>Źródło kanoniczne</dt><dd>{canonicalUrl ? <a href={canonicalUrl} target="_blank" rel="noreferrer">{entry.canonical_source}</a> : entry.canonical_source || "NOT_RECORDED"}</dd>
          <dt>Wersja źródła</dt><dd><code>{entry.canonical_source_revision || "NOT_RECORDED"}</code></dd>
          <dt>Hash źródła</dt><dd><code>{provenance?.source_sha256 || "NOT_RECORDED"}</code></dd>
          <dt>Upstream</dt><dd>{provenance?.upstream ? <>{provenance.upstream.provider || "provider unknown"}{provenance.upstream.path ? ` · ${provenance.upstream.path}` : ""}{provenance.upstream.commit ? ` · commit ${provenance.upstream.commit}` : ""}{provenance.upstream.version ? ` · wersja ${provenance.upstream.version}` : ""}{provenance.upstream.content_sha256 ? ` · SHA-256 ${provenance.upstream.content_sha256}` : ""}{upstreamUrl ? <> · <a href={upstreamUrl} target="_blank" rel="noreferrer">otwórz źródło upstream</a></> : ""}</> : "NOT_RECORDED"}</dd>
          <dt>Licencja</dt><dd>{provenance?.license?.status || "UNKNOWN"}{provenance?.license?.spdx_id ? ` · ${provenance.license.spdx_id}` : ""}{provenance?.license?.attribution?.length ? ` · ${provenance.license.attribution.join(", ")}` : ""}</dd>
          <dt>Ostatni przegląd</dt><dd>{provenance?.verification?.reviewed_at || "NOT_RECORDED"}</dd>
          <dt>Lokalne modyfikacje</dt><dd>{provenance?.local_modifications?.status || "UNKNOWN"}{provenance?.local_modifications?.items?.length ? ` · ${provenance.local_modifications.items.join("; ")}` : ""}</dd>
          <dt>Komponenty</dt><dd>{provenance?.components?.length ? <ul className="lineage-tree">{provenance.components.map((component) => <ComponentLineage key={`${component.kind}:${component.source}`} component={component} revision={entry.canonical_source_revision}/>)}</ul> : "NONE_RECORDED"}</dd>
          <dt>Zależności</dt><dd>{provenance?.dependencies?.join(", ") || "NONE_RECORDED"}</dd>
          <dt>Deklarowane kanały</dt><dd>{Object.keys(entry.declared_channels || {}).length ? Object.entries(entry.declared_channels).map(([channel, status]) => `${channel}: ${status}`).join(" · ") : "NOT_RECORDED"}</dd>
          <dt>Ocena zdolności</dt><dd>{entry.capability_assessment || "UNASSESSED"}</dd>
          <dt>Polityka aktualizacji</dt><dd>{provenance?.update_policy || "NOT_RECORDED"}</dd>
        </dl></details>
      </article>;
    })}</div> : <p className="catalog-empty" role="status">Brak wyników dla tych filtrów. Zmień wyszukiwanie lub wyczyść filtry.</p>}
  </section>;
}
