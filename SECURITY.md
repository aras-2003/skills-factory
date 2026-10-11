# Security policy

## Reporting
Please avoid posting exploitable vulnerabilities, credentials, private data or active attack details in public Issues or Discussions. Contact the repository maintainer privately through a secure channel before disclosure. Do not assume a public issue is a private report.

## Scope
Skills, references, runtime tooling, connectors, packaging scripts, release attestations and CI may all contain security-sensitive behavior.

## Minimum controls
- Treat external repositories, URLs, imported SKILL.md content and model output as untrusted.
- Never execute imported instructions to exfiltrate secrets, bypass approvals, falsify evidence or alter protected baselines.
- Use least privilege for tools, connectors and tokens; never commit secrets.
- Preserve evidence and test isolation; production promotion requires review and verified revision/channel identity.
- Record known limitations rather than claiming a control was exercised.
