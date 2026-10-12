# Project metadata automation

**Status:** workflow merged and live metadata readback verified during the 2026-10-12 backlog review. This is metadata automation, not iteration acceptance enforcement.

- Target: user Project https://github.com/users/aras-2003/projects/1 and Issues in `aras-2003/skills-factory`.
- GitHub's built-in Auto-add handles Issue membership. This workflow **does not** add items; it waits for built-in Auto-add.
- Issue labels are source for `priority:P0..P3`, `area:<exact option>`, `size:XS..XL`. If absent, strictly parse the migration Issue body header `historical priority: **P1**`, `size: L`, and legacy ID in issue title for Area. Missing metadata stays blank.
- No `Type` field: GitHub reserves this for native Issue Types.
- GitHub Project **Size** exists; no duplicate `Effort` field.
- Workflow triggers when issues open/edit/labels change, or manually via workflow_dispatch for a specific issue number.
- A new issue may need a few seconds to be automatically attached before sync. The action retries up to 50 seconds and fails visibly if the item is still absent.
- A dedicated `Project status:` marker or explicit status label controls `Status`; historical narrative status is not authoritative. Keep exactly one current marker and avoid conflicting labels. It does not set native `Iteration`, enforce scope locks, validate iteration closure, write backlog JSON, create/close issues, promote releases or touch evidence.
- After updates, verify workflow completion and the real Project field. Issue closure events are not included in this workflow; keep the current marker and Project Done consistent and verify the configured Project workflows.
- See [iteration delivery policy](ITERATION-DELIVERY.md) for work transitions and iteration gates.

## Required one-time authentication
GitHub Actions default `GITHUB_TOKEN` cannot reliably write to a user-owned Project V2. Configure an account-scoped credential **as an Actions secret called `PROJECTS_TOKEN`** under repository Settings → Secrets and variables → Actions. Prefer a narrowly scoped GitHub App installation token with owner project write access; otherwise use a **fine-grained PAT** authorized for account Projects (write), and read Issues/metadata for the repo. Exact permission options are determined by the current GitHub UI; check the token is limited to the correct owner, repository, and project. Never commit or post the token.

If `PROJECTS_TOKEN` is absent the job **fails closed** (no silent green success). Restrict who may modify workflows and review third-party code before enabling a Project-writer token.

## Historical rollout checklist (retain as provenance)
1. Review PR, run offline syntax/unit tests, merge after approval.
2. Configure secret in GitHub UI, run manual dispatch for issue #162.
3. Confirm that Priority=P1, Area=Engineering, Size=L appear in Project #1. If not, inspect Action logs for missing GraphQL schema/permission/option mapping.
4. Repeat for #163–#165 and issue with explicit labels. Verify reruns make no unwanted changes.
5. Only after receipts are recorded, move to complete backlog import; do not claim automatic metadata sync before this verification.

## Risks
- The current mapping treats legacy PRO/LIF/WRI/CON as Other until an explicit `area:...` label is applied; do not invent unsupported Area values.
- Updating an Issue description/labels triggers refresh; existing manually set Project values are left unchanged only if source metadata is absent. Do not overwrite discretionary triage labels without review.
- A user-owned Project requires correct permission to read and update fields; credentials are not installed by this PR.
