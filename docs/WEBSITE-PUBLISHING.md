# Public catalog updates

GitHub Pages serves `main:/docs`. A passing PR merged into main triggers the existing Pages publication. This site is a source catalog; it is separate from the private Cloud Next MCP deployment.

- `scripts/catalog/generate_catalog.py` regenerates `CATALOG.md` and `docs/catalog.json`, including every source skill and workflow. The preserved catalog source revision describes that source snapshot; refresh it deliberately when publishing a newly verified source snapshot.
- `docs/processes.json` contains curated reading paths. Cover new domains with their actual source skills, stage gates and source links; keep draft maturity visible. `docs/index.html` supplies Polish domain labels and renders the full workflow list directly from generated catalog data, so source workflow discovery does not depend on curated path coverage.
- `docs/lab-release.json` is the manifest of the last verified immutable Lab build. Copy it from the matching validated artifact, not from an older tracked plugin snapshot. CI packaging uploads its new receipt as an artifact without updating this branch. The current public receipt records Lab 0.34.0 built from `9b457bd68bcd9ff00aece141dbf7f0864b88a723`.
- `docs/cloud-release.json` is a dated, public-safe snapshot of the last verified private MCP deployment. Refresh it only after native deployment success and live identity/catalog checks. Record the Site version/SHA separately from embedded Lab and draft source provenance. Exclude tokens, user identities, private inputs and access policies. Counts distinguish source skills/workflows from runtime entrypoints: currently 64 source skills, 19 source workflows and 82 private runtime entrypoints (70 Lab + 12 explicit draft test entries).

Do not infer model quality or native authoring/export success from loader checks. The public receipt must preserve NOT_RUN for those campaigns until real evidence exists.

Before merging, run the site catalog contract tests, regenerate the catalog and check the diff. Inspect desktop and mobile behavior in the app browser, including domain names, new reading paths, workflow search, source links and modal details. After merging, verify the Pages build and the actual published page. This update does not change Pages hosting, access rules or private MCP publication.
