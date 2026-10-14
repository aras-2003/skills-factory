# Cloud Next Site source

The complete Cloud Next Site and MCP Worker source lives in `sites/skills-factory-cloud-next/`. Skills Factory is the single authoring repository for the Site's application, tool contracts, dependencies, tests and build configuration. The provider-managed Git checkout is a deployment mirror; it is not a second source of truth.

## Build and validation

The dedicated `.github/workflows/validate-cloud-next-site.yml` workflow runs on Site source pull requests and on changes to the Site build inputs. It builds Lab from the exact source revision, generates the MCP catalog and canonical source attestation, then typechecks, tests contracts and source synchronization, lints and builds the Worker. It does not upload test or runtime artifacts.

For a local build from the monorepo root:

```bash
python scripts/package/build_lab_plugin.py --output .tmp/cloud-next-lab
python scripts/package/build_cloud_next_site.py --lab-artifact .tmp/cloud-next-lab --write-generated
pnpm --dir sites/skills-factory-cloud-next install --frozen-lockfile
pnpm --dir sites/skills-factory-cloud-next exec tsc --noEmit --incremental false
pnpm --dir sites/skills-factory-cloud-next exec node scripts/check-contracts.mjs
pnpm --dir sites/skills-factory-cloud-next exec node --test tests/source-sync.test.mjs
pnpm --dir sites/skills-factory-cloud-next lint
pnpm --dir sites/skills-factory-cloud-next build
```

The generated `lib/skill-catalog.ts` and `lib/canonical-provenance.ts` files are ignored build inputs. They must be generated from the same Lab build and full Skills Factory Git SHA. A published runtime reports the provider mirror commit, canonical Skills Factory commit and embedded Lab release separately.

## Deployment boundary

Merging a source PR does not deploy the Site. The official Sites workflow synchronizes the reviewed Site subtree from the merged Skills Factory revision into the provider-managed deployment mirror, then runs the native Site build and deployment checks. Keep provider-only release notes in that checkout; they are excluded from the public source transfer. For the current operational procedure, follow the repository's maintained Sites publication runbook and use its native deployment tools.
