# Cloud Next adapter and Site source

The Cloud Next MCP adapter source lives in `adapters/skills-factory-cloud-next/`. The standalone Site application lives in `sites/skills-factory-site/`. Skills Factory remains the single authoring repository for the adapter, Site UI, dependencies, tests and build configuration. The provider-managed Git checkout is a deployment mirror; it is not a second source of truth.

## Build and validation

The dedicated `.github/workflows/ci-site.yml` workflow runs on Site source pull requests and on changes to the Site build inputs. It builds Lab from the exact source revision, generates the MCP catalog and canonical source attestation, then typechecks, tests contracts and source synchronization, lints and builds the Worker. It does not upload test or runtime artifacts.

For a local build from the monorepo root:

```bash
python scripts/package/build_lab_plugin.py --output .tmp/cloud-next-lab
python scripts/package/build_cloud_next_site.py --lab-artifact .tmp/cloud-next-lab --write-generated
pnpm --dir sites/skills-factory-site install --frozen-lockfile
pnpm --dir sites/skills-factory-site exec tsc --noEmit --incremental false
pnpm --dir sites/skills-factory-site exec node ../../adapters/skills-factory-cloud-next/scripts/check-contracts.mjs
pnpm --dir sites/skills-factory-site exec node --test tests/source-sync.test.mjs
pnpm --dir sites/skills-factory-site lint
pnpm --dir sites/skills-factory-site build
```

The generated `sites/skills-factory-site/lib/skills-factory-adapter/` bundle is ignored build output. It contains adapter modules plus the catalog and provenance generated from the same Lab build and full Skills Factory Git SHA. A published runtime reports the provider mirror commit, canonical Skills Factory commit and embedded Lab release separately.

## Deployment boundary

Merging a source PR does not deploy the Site. The official Sites workflow generates the adapter bundle from the merged Skills Factory revision, synchronizes the reviewed Site workspace into the provider-managed deployment mirror, then runs native Site build and deployment checks. Keep provider-only release notes in that checkout; they are excluded from the source transfer. For the current operational procedure, follow the repository's maintained Sites publication runbook and use its native deployment tools.
