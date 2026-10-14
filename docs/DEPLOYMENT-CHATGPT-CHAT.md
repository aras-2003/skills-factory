# Deploying production skills to ordinary ChatGPT Chat

## Goal

Keep GitHub as the single source of truth while supporting two independent delivery paths:

1. **Plugin bundle** for Work / Codex and other plugin-capable surfaces.
2. **Individual ChatGPT Skills** for ordinary Chat, when the account/surface exposes the native Skills feature.

This avoids relying on local-marketplace plugin skill exposure inside ordinary
Chat and removes the local MCP dependency from the portable path.

For mobile Chat, use the `skills-only` profile or the individual native skill
ZIPs. A custom MCP App is not a mobile delivery mechanism: OpenAI currently
documents MCP Apps as web-only.

## Why dual deployment

OpenAI currently documents that skill availability, installation and syncing can differ by product and surface. A local or repo marketplace plugin can be installed correctly and still expose its bundled skills only in some runtimes.

Therefore the production branch generates both:

```
skills/<domain>/<skill>/
        |
        +--> plugins/skills-factory/skills/<skill>/   # Work / Codex plugin
        |
        +--> dist/chatgpt-skills/<skill>.zip          # native ChatGPT Skill upload
```

No skill logic is duplicated manually. Both artifacts are built from the same production source folder.

## Personal ChatGPT bundle format

Each generated ZIP contains exactly one top-level skill folder:

```
executive-role-evaluator.zip
└── executive-role-evaluator/
    ├── SKILL.md
    ├── references/
    ├── scripts/
    └── assets/
```

Only runtime files are included. Test and evaluation folders are intentionally excluded.

The format follows the Agent Skills bundle convention and is suitable for native skill upload where that feature is available.

## Production pipeline

```
feature branch
  -> PR to main
  -> validation + behavioral eval
  -> promotion to production
  -> release-production-plugin.yml
  -> plugins/skills-factory/

  -> package-chatgpt-skills.yml
  -> dist/chatgpt-skills/*.zip
```

Only skills with:

```yaml
metadata:
  maturity: production
```

are exported.

## Install into ordinary Chat

When the native Skills page is available on the active ChatGPT account/surface:

1. Open **Plugins**.
2. Open the **Skills** tab.
3. Select **Create**.
4. Select **Upload from your computer**.
5. Upload the required ZIP from `dist/chatgpt-skills/`.
6. Complete the scan/install flow.
7. Start a new ordinary Chat conversation and test the skill.

For the current career workflow, install at minimum:

- `executive-role-evaluator.zip`
- `company-context-research.zip`

The diagnostic skill is useful during setup:

- `skills-factory-diagnostic.zip`

## Updating a skill

The repository remains authoritative.

After a production change:

1. GitHub regenerates the ZIP.
2. Download the updated ZIP from `production/dist/chatgpt-skills/` or the latest workflow artifact.
3. Update/re-upload the corresponding native ChatGPT Skill using the Skills UI available to the account.

Do not edit the installed ChatGPT copy as the primary source; any emergency UI edit should be backported to GitHub.

## Availability limitation

OpenAI currently states that Personal Skills are generally available to ChatGPT Business, Enterprise, Healthcare and Edu users, and that availability varies by workspace, role and product surface.

If the active account does not expose the relevant plugin/Skills surface, this
repository can still generate valid skill bundles, but it cannot force-enable a
ChatGPT product feature or make a custom MCP App available on mobile.

In that case the supported options are:

- use the plugin bundle in a surface where it is exposed, such as Work/Codex;
- use a workspace/account where native Skills are enabled;
- publish the plugin through OpenAI's supported plugin distribution flow if broader Chat surface availability is required.

## Verification

For a native ordinary-Chat installation, test in a new Chat without selecting Work.

Diagnostic prompt:

```
Use the skills-factory-diagnostic skill.
```

Expected behavior:

```
SKILLS_FACTORY_ACTIVE
skills-factory-diagnostic
```

For `executive-role-evaluator`, the response should begin with its required decision header.
