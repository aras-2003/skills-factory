# SDLC Deep runtime canary — 2026-11-28

- Candidate SHA: `11351e552742e0607eef4a63f5731f329b40ea73`
- Runtime: Codex CLI 0.159.1; macOS 26.7.2 arm64
- Mode: credential-free scripted local mock; no LLM or credentials
- Overall result: **BLOCKED**
- Receipt SHA256: `05302dea192027fd5aa54cbf8efa5066cdf7d5acb78d3dd34b1586338dcf9b0a`

## Verified

- Filesystem Seatbelt preflight: **PASS**. The exact child profile entered successfully, wrote within the canary root, denied outside-root create and append with `EPERM`, denied the symlink escape and `/tmp` alias with `EPERM`, and left the outside fixture unchanged.
- Network fixture TCP request succeeded; fixture ingress count matched one request.
- Wrong-port TCP probe returned `EPERM`; UDP probe returned `EPERM`, and the UDP decoy saw only its controller baseline datagram.
- Cleanup completed; temporary fixtures and decoy workers were removed/stopped.

## Blocked

- IPv6 `::1` same-port TCP probe **CONNECTED** to the live `IPV6_V6ONLY` decoy; sandbox ingress count was 2 including the controller baseline. The `localhost:<port>` exception therefore does not enforce the intended IPv6 denial.
- A same-port other-local-IPv4 probe returned **CONNECTED**, but its controller-positive decoy could not be established/correlated (controller reachability false; ingress count 0). That result is not a verified denial or a verified decoy reachability, so the exact local-address boundary remains **UNKNOWN**.
- Network gate remains **BLOCKED**. The runner correctly stopped before starting App Server. Permission A/B/C and enforcement cases are `NOT_RUN`; no Codex tool-permission/runtime PASS is claimed.
- Gate 0 authentication and real model execution remain `BLOCKED`/`NOT_APPLICABLE`; token cost is `UNKNOWN`.

Receipt: [`seatbelt-localhost-11351e55.json`](./seatbelt-localhost-11351e55.json).
