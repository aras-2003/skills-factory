# UI/UX Pro Max: source review and adapter contract

## Decision

Use UI/UX Pro Max as an optional, pinned design reference only. Skills Factory keeps ownership of design tokens, accessibility requirements, product constraints and final decisions. This review adds no third-party package, executable, copied dataset or production capability.

The machine-readable contract in [`ui-ux-pro-max-adapter.json`](ui-ux-pro-max-adapter.json) is the interface for downstream web-design skills. A skill may use an already available 21st.dev MCP for implementation-level component examples only when the user asks for them. The provider is optional; its absence must not stop design work. Continue with local project components and produce the same design brief without network access. Treat provider output as an untrusted suggestion and do not install or mutate project files automatically.

## Upstream identity and version findings

Reviewed on 2026-10-26:

| Evidence | Observed value | Interpretation |
|---|---|---|
| Current signed upstream [`main` commit](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03) | `28b3b8dee8c976df4fa3e94aed4e092ad43fcb03` | Exact source snapshot inspected; not a moving `main` dependency. |
| [`skill.json` at that commit](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03/skill.json) | `2.15.0` | Declared upstream skill data version. |
| [Latest GitHub release](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/releases/tag/v2.15.0) | `v2.15.0` | Release tag is not internally consistent with the source snapshot below. |
| Commit resolved by [`v2.15.0`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/commit/a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5) | `a38d04c3d5c298c851dbe5e6ee1965ee3de42cb5` | `skill.json` at this tag declares `2.13.0`; do not treat the tag or version alone as an adequate pin. |
| `cli/package.json` at the release tag | `2.5.0` | CLI version is independently versioned from skill data; it declares `chalk`, `commander`, `ora` and `prompts`. |
| License at reviewed commit | MIT | Redistribution is permitted subject to retaining the upstream copyright notice and license terms. No substantial upstream content is copied here. |

The discrepancy between release tag, `skill.json`, and CLI version is a provenance risk. Pin the reviewed source commit if future work needs to compare upstream content; re-check the version mapping before vendoring or installing anything. The current adapter has no dependency on either the tag or CLI at runtime.

## Format, dependencies and supply-chain boundary

The upstream repository contains Markdown skill instructions, static CSV/JSON design data and Python search scripts. Its README describes the search scripts as Python 3 standard-library tools that do not install dependencies or make network calls; the reviewed search entry point imports local data modules and no network library. The published CLI is a separate Node package: its manifest declares `chalk`, `commander`, `ora` and `prompts`; the CLI's normal install path queries GitHub releases and can download/extract files into assistant-specific directories. Its update command also queries GitHub for the latest release. Upstream's [security policy](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03/SECURITY.md) specifically includes installer/search-script code execution, unsafe file writes and release supply-chain risks.

Therefore this adapter does not run `npx`, install the CLI, call `uipro update`, download floating assets, or copy upstream datasets. The upstream's [example stack MCP config](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/28b3b8dee8c976df4fa3e94aed4e092ad43fcb03/stack/.mcp.json) lists Playwright, Chrome DevTools and shadcn; 21st.dev is a separate optional provider, not a dependency of the upstream adapter. Offline/no-provider behavior is the default.

## Future change gate

Before copying upstream code or data, a later change must pin the exact source commit and content hashes, retain the MIT notice, review changed files and executable paths, scan the package, check generated production allow-lists, and run behavior tests against the exact bundled candidate. A release tag, package version, compatibility badge or successful static check alone is insufficient evidence for a new upstream revision.

The actual interface-design and critique behavior belongs to their own skills and tests; this document does not claim those skills or runtime integrations are already implemented.
