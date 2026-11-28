# Architect A3 review: diagnostic continuation after network block

## Trigger and exact candidate

The exact local-mock canary proved filesystem enforcement but remained blocked on its network gate because `localhost:<port>` reached the live IPv6 same-port decoy. Candidate under review: `3b4503b3b49f2d548e7a49e22d8500fbb9e07763` plus the diagnostic-continuation working diff. The coordinator added an opt-in `--diagnostic-continue-after-network-block` path before routing this A3 trigger. It is restricted to credential-free local mock and must leave network and aggregate acceptance blocked.

## Review requested

Assess whether continuing the scripted App Server permission diagnostic under this known localhost family limitation is safe and useful. Verify that the option cannot be used without `--local-mock`, cannot mark network or overall status PASS, carries no credentials, and only runs fixed fixture commands. Specify additional conditions or recommend removal.

## Architect assessment

**Disposition: ADAPT.** Keep the option only if preflight positively classifies the result as `KNOWN_IPV6_SAME_PORT_ONLY`. Before starting App Server, require filesystem PASS, successful exact-profile launch, correlated allowed IPv4 fixture HTTP, controller-positive wrong-port/UDP/other-local-IPv4 decoys with sandbox denials and baseline-only ingress, a live IPv6 same-port connection with separate controller/sandbox ingress, and verified decoy cleanup. The IPv6 same-port connection is the sole exception. Any FAIL, missing/malformed/unknown observation, other boundary leak, or cleanup uncertainty must stop before App Server; retain FAIL as FAIL and BLOCKED as BLOCKED. The network gate remains BLOCKED and aggregate acceptance cannot PASS.

The existing receipt is **ineligible**: it records IPv6 same-port CONNECTED, but also same-port other-local-IPv4 CONNECTED and an uncorrelated/failed controller baseline. For permission-flow debugging, stopping after correlated A readback may be sufficient; avoid the marker command where possible. Keep the fixed scripted sequence, no credentials, empty MCP set, read-only policy, and exact candidate setup. If the narrow exception cannot be established, remove the option and use an isolated guest.

The coordinator initially tightened the predicate and committed it as `e0eead51bb7a2c3fa245745e35b253e7bc565ad6`. Independent review of that exact SHA failed: actual UDP observations are strings while the predicate accepts only dictionaries, so the allowlist could never match real evidence; also, the live IPv6 listener is closed before App Server starts, so endpoint control is not retained. Synthetic tests masked the first mismatch. Reviewer effective model and effort were not exposed (`UNKNOWN`). The reviewer's attempt to validate this record was `NOT_RUN` because the environment lacked the `jsonschema` package.

**Coordinator resolution: REJECT the diagnostic continuation flag.** It has been removed; the existing fail-closed preflight remains. No App Server runtime was run with this option. A future attempt needs a reviewed design that keeps control of any reachable endpoint for the entire process lifetime and tests against the actual probe result schema, or an isolated guest runtime.

## Routing chronology

This A3 security-boundary trigger was recognized after the code change and its unit tests. The decision is recorded as late; exact edit time was not captured. Architect and independent review were source-only; no runtime was run with the diagnostic continuation option.
