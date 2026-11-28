# Architect follow-up: Seatbelt localhost restriction

## Decision

The parser-valid native candidate is `(allow network-outbound (remote tcp (param "FIXTURE_ENDPOINT")))` with `FIXTURE_ENDPOINT=localhost:<port>`, after `(deny network-outbound)`. Keep the App Server HTTP base URL at numeric `127.0.0.1:<port>`. The prior numeric host in this Seatbelt predicate was rejected by macOS (`host must be * or localhost in network address`, exit 65).

`localhost:<port>` may admit both IPv4 `127.0.0.1` and IPv6 `::1`, so this is not proof of address-family isolation. Architect proposed adding `(deny system-socket (socket-domain AF_INET6))` as a bounded native candidate. A harmless host experiment showed AF_INET6 socket creation still succeeds under that rule (exit 0, both AF_INET and AF_INET6 sockets created). The rule did not enforce the intended boundary and is removed.

Keep the IPv6 same-port `IPV6_V6ONLY` decoy, controller-positive baseline, live wrong-port TCP decoy, UDP decoy, and in/out filesystem controls. If localhost TCP reaches the IPv6 decoy, the network boundary gate must remain `BLOCKED`; do not weaken the result or remove the check. Test a same-port decoy on another local IPv4 interface if one is available; otherwise the exact-host claim remains `UNKNOWN`. The pinned provider uses HTTP `base_url`; no supported Unix-socket Responses transport was identified.

## Evidence and limits

- macOS 26.7.2 arm64 rejected the numeric remote host before child entry (receipt on candidate 779b2cdc: exit 65).
- Harmless parser checks accepted both `remote tcp "localhost:43210"` and `remote ip "localhost:43210"`; no network connections were made.
- A harmless socket-family experiment showed `(deny system-socket (socket-domain AF_INET6))` did not prevent IPv6 socket creation. This experiment was uncommitted when run; it is diagnostic evidence, not exact-SHA acceptance.
- Architect source review: pinned Codex 0.159.1 uses `remote ip "localhost:<port>"`; upstream Seatbelt evidence reports that localhost admits both IPv4 and IPv6 loopback.
- Network policy and App Server runtime behavior remain unverified. Effective Architect model and effort are `UNKNOWN`.

Pinned sources: [Codex 0.159.1 Seatbelt policy](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/sandboxing/src/seatbelt.rs#L319), [IPv4/IPv6 localhost behavior report](https://github.com/openai/codex/issues/42925), [Codex provider base URL](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/model-provider-info/src/lib.rs#L122).
