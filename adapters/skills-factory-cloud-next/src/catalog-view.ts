import { SKILL_CATALOG } from "./skill-catalog";

export const CATALOG = SKILL_CATALOG;
export const PROVENANCE_CLASSIFICATIONS = ["OWN", "EXTENDED", "IMPORTED", "COMPOSED", "UNKNOWN"] as const;

export type CatalogFilterEntry = {
  name: string;
  kind: string;
  domain?: string;
  description: string;
  canonical_source?: string;
  provenance?: { classification?: string };
};

export function filterCatalog<T extends CatalogFilterEntry>(
  entries: readonly T[],
  filters: { query?: string; classification?: string; domain?: string },
): T[] {
  const needle = (filters.query || "").trim().toLocaleLowerCase();
  return entries.filter((item) => {
    const state = item.provenance?.classification || "UNKNOWN";
    const text = [item.name, item.domain, item.kind, item.description, item.canonical_source, state].join(" ").toLocaleLowerCase();
    return (!needle || text.includes(needle))
      && (!filters.classification || filters.classification === "all" || state === filters.classification)
      && (!filters.domain || filters.domain === "all" || (item.domain || "unknown") === filters.domain);
  });
}
