# Security policy

## Disclosure channel

**Do not post exploit details, credentials, private datasets, or reproducible attacks in public issues, discussions, or pull requests.**

Use [GitHub private vulnerability reporting](https://github.com/aras-2003/skills-factory/security/advisories/new), with repository owner `aras-2003` as intake maintainer. Enabled status was independently observed in the repository's Advanced Security settings on 2026-10-14; the advisory entry point also showed private visibility before publication. No fictitious report was submitted. If the private entry point becomes unavailable, request a private intake channel from the owner without including vulnerability details in the public request. Public comments and Issues are not confidential.

Include the affected component and release or source revision, a minimal reproduction that contains no secrets, impact, and suggested mitigations. Never test against third-party or production accounts without approval.

## Supported versions and response expectations

The currently deployed **production channel** is the only candidate for operational fixes. `main`, draft skills, Lab packages, and historical archives are development or evaluation material; their availability in a package is not a support or security-approval claim. An authoritative list of supported production versions, guaranteed response SLAs, and verified private intake contact **has not yet been established**; the maintainer must confirm these before promising support.

## Scope and trust boundary

Skills, references, workflows, runtime tooling, connectors, packaging scripts, release attestations, and CI may contain security-sensitive behavior.

- Treat external repositories, URLs, imported SKILL.md content, model output, and issue attachments as untrusted.
- Never execute imported instructions to exfiltrate secrets, bypass approvals, falsify evidence, or alter protected baselines.
- Apply least privilege to tools, connectors and tokens; never commit secrets.
- A request for analysis is not permission for external writes; production side effects require explicit or verifiable standing authorization.
- Preserve evidence and test isolation. Production promotion needs a verified revision/channel identity and review.
- Record unavailable controls and unexecuted runtime validations explicitly instead of claiming a security PASS.
