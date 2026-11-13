# Canonical provenance registry

`registry.yaml` is the single source of provenance metadata for skill and workflow records. It is a sidecar to executable instructions so that taxonomy, rights and external-source lineage do not get confused with maturity, channel support, security assessment or runtime availability.

## Classification rules

- `OWN`: repository-authored and maintained without an external skill as a functional base. Requires reviewed evidence; never inferred from a missing source URL.
- `IMPORTED`: an upstream skill is retained with only minimal packaging or compatibility changes. Pin its URL/provider/path and exact upstream content hash.
- `EXTENDED`: an external skill remains a functional base and material local behavioral changes are documented.
- `COMPOSED`: a capability structurally combines at least two registered components. Child records remain canonical and their origin/revision is expanded in generated projections.
- `UNKNOWN`: source or lineage is not verified. This is the migration default and makes no ownership, license or attribution claim.

If an external skill is a functional base and local changes are material, use `EXTENDED`. If multiple components form a new capability, use `COMPOSED` and keep each child source linked. If evidence cannot distinguish those cases, use `UNKNOWN`. Inspiration alone is not imported lineage.

License state and SPDX identifiers are separate from provenance class. An SPDX identifier and attribution are included only when verified. Unknown records use manual review updates; no import or update is executed by these scripts.

## Reconciliation and derived data

Run `python scripts/provenance/migrate.py` to refresh source identities, add new records, and regenerate `migration-audit.json`. Existing reviewed records are preserved. Removed source paths remain in the registry and fail validation until explicitly reconciled. Run `python scripts/provenance/migrate.py --check` for a non-writing consistency check.

Run `python scripts/catalog/generate_catalog.py` to generate `CATALOG.md` and `docs/catalog.json`. Package builders project the same validated records into Lab/production `capabilities.json` and `release-manifest.json`. Do not hand-edit generated files or duplicate classifications in channel-specific metadata.
