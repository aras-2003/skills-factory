# Architect A3 review: diagnostic continuation after network block

## Trigger and exact candidate

The exact local-mock canary proved filesystem enforcement but remained blocked on its network gate because `localhost:<port>` reached the live IPv6 same-port decoy. Candidate under review: `3b4503b3b49f2d548e7a49e22d8500fbb9e07763` plus the diagnostic-continuation working diff. The coordinator added an opt-in `--diagnostic-continue-after-network-block` path before routing this A3 trigger. It is restricted to credential-free local mock and must leave network and aggregate acceptance blocked.

## Review requested

Assess whether continuing the scripted App Server permission diagnostic under this known localhost family limitation is safe and useful. Verify that the option cannot be used without `--local-mock`, cannot mark network or overall status PASS, carries no credentials, and only runs fixed fixture commands. Specify additional conditions or recommend removal.

## Architect assessment

**Disposition: ADAPT.** Keep the option only if preflight positively classifies the result as `KNOWN_IPV6_SAME_PORT_ONLY`. Before starting App Server, require filesystem PASS, successful exact-profile launch, correlated allowed IPv4 fixture HTTP, controller-positive wrong-port/UDP/other-local-IPv4 decoys with sandbox denials and baseline-only ingress, a live IPv6 same-port connection with separate controller/sandbox ingress, and verified decoy cleanup. The IPv6 same-port connection is the sole exception. Any FAIL, missing/malformed/unknown observation, other boundary leak, or cleanup uncertainty must stop before App Server; retain FAIL as FAIL and BLOCKED as BLOCKED. The network gate remains BLOCKED and aggregate acceptance cannot PASS.

The existing receipt is **ineligible**: it records IPv6 same-port CONNECTED, but also same-port other-local-IPv4 CONNECTED and an uncorrelated/failed controller baseline. For permission-flow debugging, stopping after correlated A readback may be sufficient; avoid the marker command where possible. Keep the fixed scripted sequence, no credentials, empty MCP set, read-only policy, and exact candidate setup. If the narrow exception cannot be established, remove the option and use an isolated guest.

The coordinator tightened the predicate and added tests for the eligibility allowlist, malformed/failed observations, cleanup and CLI side effects. This does not make the current receipt eligible and does not authorize running App Server on this host.

## Routing chronology

This A3 security-boundary trigger was recognized after the code change and its unit tests. The decision is recorded as late; exact edit time was not captured. Architect follow-up was source-only; no runtime was run with the diagnostic continuation option.
