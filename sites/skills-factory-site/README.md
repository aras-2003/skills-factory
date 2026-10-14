# Skills Factory Site

This Next/Vinext application is a standalone workspace in the `aras-2003/skills-factory` monorepo. Its remote MCP facade is maintained separately in `adapters/skills-factory-cloud-next/` and bundled into the Site build. The Site provider's Git repository is a deployment mirror maintained by the official Sites workflow.

## Build from Skills Factory

From the monorepo root, install the hash-locked Python dependencies from `requirements-dev.lock`, then build the Lab artifact and generate the Site catalog and provenance for the same commit:

```bash
python scripts/package/build_lab_plugin.py --output .tmp/cloud-next-lab
python scripts/package/build_cloud_next_site.py --lab-artifact .tmp/cloud-next-lab --write-generated
```

Then install the Site's pinned dependencies and run its checks:

```bash
pnpm --dir sites/skills-factory-site install --frozen-lockfile
pnpm --dir sites/skills-factory-site exec tsc --noEmit --incremental false
pnpm --dir sites/skills-factory-site exec node ../../adapters/skills-factory-cloud-next/scripts/check-contracts.mjs
pnpm --dir sites/skills-factory-site lint
pnpm --dir sites/skills-factory-site build
```

The generated directory `lib/skills-factory-adapter/` is ignored build output. It is created from the adapter source, Lab artifact and full Skills Factory Git SHA; do not edit or commit it by hand. A published runtime reports three distinct identities: the Cloudflare Site mirror commit, canonical Skills Factory commit and embedded Lab release commit.

## MCP contract

The Cloud Next adapter exposes six stateless, read-only tools: `runtime_info`, `list_skills`, `load_skill`, `route_investment_request`, `render_bar_chart`, and `render_line_chart`. The host model executes loaded instructions. The MCP routes and renders explicit caller data; it does not fetch portfolio data, trade, infer missing chart values, or claim that the client rendered an SVG.

For source ownership and release boundaries, see [`docs/SITE-CANONICAL-SOURCE.md`](../../docs/SITE-CANONICAL-SOURCE.md). Use the official Sites workflow and native deployment tools to publish; do not edit the provider-managed source mirror as the canonical project source.
