# Deploying production skills to ChatGPT / Codex

## Goal

Keep GitHub as the source of truth and expose production-ready skills through
surface-specific profiles: a skills-only profile for ordinary Chat portability,
a remote-MCP profile for supported web/desktop/Work execution, and a local
profile for Desktop/Work capabilities that require the machine.

## Why dual deployment

The skills-only profile is the portable core. It prevents a local `stdio` MCP
dependency from making ordinary Chat or mobile unusable. The remote profile adds
server-backed tools where the host supports HTTPS MCP. The local profile remains
the full desktop development/runtime package.

Ordinary Chat can expose skills differently from Work/Codex. To avoid coupling
daily Chat usage to a local runtime, production also generates one native skill
ZIP per production skill.

MCP Apps are currently web-only in ChatGPT. Mobile Chat must therefore use the
skills-only profile; mobile cannot be listed as a supported MCP surface.

See `DEPLOYMENT-CHATGPT-CHAT.md` for the ordinary-Chat installation path.

## Production packaging flow

```
feature branch
  -> PR to main
  -> static validation
  -> behavioral eval
  -> release review
  -> promotion to production
  -> release-production-plugin.yml
  -> plugins/skills-factory/
  -> repo marketplace
```

Only skills whose frontmatter contains:

```yaml
metadata:
  maturity: production
```

are copied into the installable plugin.

The packaging step flattens the repository's domain structure:

```
skills/career/role-fit-analysis/
```

into the plugin format required by OpenAI:

```
plugins/skills-factory/skills/role-fit-analysis/
```

so every bundled skill is an immediate child of `skills/`.

### Build the three profiles

```bash
# ordinary Chat / mobile-safe profile
python scripts/package/build_plugin.py \
  --runtime-mode skills-only --output .tmp/chat-mobile

# supported web/desktop/Work profile with a deployed HTTPS MCP service
python scripts/package/build_plugin.py \
  --runtime-mode remote \
  --remote-mcp-url https://<your-host>/mcp \
  --output .tmp/chat-web

# existing local profile for Desktop/Work
python scripts/package/build_plugin.py \
  --runtime-mode local --output .tmp/desktop
```

The remote endpoint must be deployed separately and exposed over HTTPS using a
supported streamable HTTP MCP transport. The repository does not pretend that
an unconfigured placeholder endpoint is deployable.

## Initial installation

On a supported ChatGPT desktop/Codex environment, add the Git-backed marketplace:

```bash
codex plugin marketplace add aras-2003/skills-factory --ref production
```

Then refresh/restart the ChatGPT desktop app and install **Skills Factory** from that marketplace if the client still asks for confirmation.

The marketplace declares `INSTALLED_BY_DEFAULT`. This is useful for supported local/repo marketplace clients, but it is not the same as an account-wide cloud installation policy.

## Updating

Refresh the Git marketplace:

```bash
codex plugin marketplace upgrade
```

or:

```bash
codex plugin marketplace upgrade skills-factory
```

Then restart/refresh the desktop client if needed.

## Important limitation

OpenAI currently documents automatic installation policies for managed workspaces and local/repo marketplaces, but no public API that lets a personal GitHub Actions workflow silently install or replace a skill on an individual ChatGPT account.

Therefore:
- production packaging can be fully automated in GitHub;
- marketplace distribution/update can be automated;
- the initial account/client installation still may require explicit user action;
- account-wide silent installation should not be assumed unless OpenAI exposes that capability for the active account/workspace.

## Native Skills page

When the active account exposes the native Skills page, use the generated bundles in `dist/chatgpt-skills/` for ordinary Chat.

Lifecycle and versioning remain centralized in GitHub; the uploaded ChatGPT copy is a deployment target, not the source of truth.

## Release rule

Never package from `main`.
The installable plugin always tracks `production`.
