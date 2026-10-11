# Using Skills Factory by runtime channel

## Source of truth

GitHub source defines procedures. Runtime availability is determined by the generated package, not by a hand-maintained allow-list in this document.

Check:
- `CATALOG.md` for source discovery;
- `workflows/runtime-registry.yaml` for workflow dependencies/channel constraints;
- the installed artifact's `capabilities.json` for what that exact channel contains;
- `release-manifest.json` for source revision and release identity.

## Plugin channel

The production plugin packages production-maturity skills plus production workflow entrypoints whose `plugin` channel is `supported`.

Optional workflow dependencies carry an explicit reduced-scope behavior. Missing required dependencies fail the build.

## Lab channel

Use the Lab for isolated behavioral evaluation. Lab 0.35.0 packages every source skill and workflow registered for the Lab channel, irrespective of maturity, plus registered executor-only `.input.md` eval fixtures. Its bundled MCP catalog exposes that same complete package inventory.

Do **not** enable the Lab and production plugin together for the same evaluation session when they expose duplicate names. The Lab manifest records this session rule.

Evaluator rubrics are repository-side only and must not be loaded into the executor context.

## ChatGPT ZIP channel

This channel packages individual production skills as deterministic ZIPs.

Workflow availability is not assumed. Check the ZIP channel `capabilities.json`/index: workflows marked `unavailable` require a plugin/workflow-capable channel instead of being silently omitted.

## Routing

For normal work, describe the goal rather than a skill name. The runtime should choose the smallest suitable capability.

Explicit names are appropriate for:
- behavior regression tests;
- debugging;
- forcing a known procedure;
- version comparison;
- skill development.

Natural-routing evidence is a separate test mode. A description-only selector or deterministic expected-target check is a proxy, not proof that a native runtime selected correctly.

## Context economy

1. Load only the capability needed for the current task.
2. Load references/scripts only when the procedure calls for them.
3. Keep project facts in the Project/context, not reusable skills.
4. Use workflow stop gates before expensive research.
5. Do not use evaluator rubrics as executor context.

## Version verification

Before comparing behavior, record:
- package/release ID;
- source revision;
- component version/content digest;
- runtime/model identity;
- available catalog.

See `docs/RUNTIME-EVALS.md`.
