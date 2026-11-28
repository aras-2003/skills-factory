# Architect A3 decision: canary Seatbelt boundary

## Decision

Keep Codex's `readOnly` thread policy and exact-file turn grant. Extend the outer local-mock Seatbelt profile to permit writes only beneath the disposable canonical runtime root, while denying outbound network except TCP to the numeric fixture endpoint. Treat Codex turn grants and outer OS enforcement as separate gates.

## Runtime finding

The local fixture receives a turn-scoped marker grant and the scripted tool result reports the exact marker profile before the fixture returns `exec_command`. A later command output is classified as denied; marker is unchanged and no `commandExecution` item is observed. A separate direct write under `(allow default) (deny network-outbound)` returned exit 71 and created no file. This does not identify where the write was rejected: exit 71 may indicate a Seatbelt launcher failure (`sandbox_apply`) before the payload starts. Require an in-child sentinel and actual errno classification before treating it as an OS denial.

Pinned source explains that App Server serializes the permission response before the fixture returns its command; Core intersects that response with the originating environment; the command handler can consume an implicit turn grant while baseline remains `readOnly`:

- [App Server permission response handling](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/app-server/src/bespoke_event_handling.rs#L1819)
- [Core turn grant handling](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/core/src/session/mod.rs#L3057)
- [Command handler turn-grant path](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs#L307)
- [Prior sandbox launcher failure evidence](../sdlc-deep-2026-11-27/host-runtime-capability/architect-runtime-review.md#L13)

## Candidate profile

Bind separate `-D CANARY_ROOT=<realpath>` and `-D FIXTURE_ENDPOINT=127.0.0.1:<port>` arguments. Use the same root as cwd, marker parent, `HOME`, `CODEX_HOME`, and `TMPDIR`.

```scheme
(version 1)
(allow default)
(deny file-write* (require-not (subpath (param "CANARY_ROOT"))))
(allow file-write* (subpath (param "CANARY_ROOT")))
(deny file-write-unlink (require-all (literal (param "CANARY_ROOT")) (vnode-type DIRECTORY)))
(deny system-fcntl (fcntl-command 80 110))
(deny network-outbound)
(allow network-outbound (remote tcp (param "FIXTURE_ENDPOINT")))
```

Pass `-D CANARY_ROOT=<canonical-root>` and `-D FIXTURE_ENDPOINT=127.0.0.1:<port>` as separate `sandbox-exec` definition arguments. Explicitly allow writes beneath the root after the broad outside-root deny. Preserve the root directory and lock/fcntl boundary. `allow default` still permits reads, so this does not establish host-file read isolation. If that is needed, use a separately verified read policy or a dedicated credential-free macOS identity/VM. Do not expand the writable root after a failed preflight.

## Required evidence before runtime acceptance

1. Under the exact profile, environment and cwd, prove child entry, exclusive create and append inside root.
2. Prove exclusive create and append outside root fail with `EPERM`/`EACCES` for a safe writable sibling, leaving it absent/unchanged; also test a symlink to that sibling and relevant `/tmp` aliases.
3. Prove IPv4 fixture HTTP succeeds. Test live wrong IPv4 port and `::1` at the fixture port, with `IPV6_V6ONLY`; controller connections to those decoys must succeed while sandboxed probes fail and fixture ingress remains zero. Retain the existing other-address negative. Add UDP negative if claiming TCP-only egress.
4. Prove nested Codex execution with a harmless read-only command before interpreting permission cases. If sandbox setup fails or the child sentinel is absent, mark BLOCKED; exit 71 alone is not an OS file denial.
5. Re-run exact A grant/active write/interruption, fresh B empty grant/non-transfer, and C exact denied write. Preserve exact candidate SHA, macOS build, CLI version, profile identity, probe exits/error categories, decoy ingress counts, sanitized correlation hashes, marker digest, and cleanup verification.

## Limits

This is source-based architecture advice. The proposed Seatbelt profile, nested execution, turn-grant behavior and non-transfer remain unverified. Effective Architect model and reasoning effort remain `UNKNOWN` because the collaboration host does not expose them.

## Follow-up implementation note

The canary now builds this profile with an explicit in-root write allow, separate `-D` values, a root-scoped filesystem probe and an exact-profile nested Codex `true` command positive control. This is implementation only: until the credential-free runtime run produces child-entry, errno and host command-event evidence, the Seatbelt and nested-execution decisions remain unverified. The current network probes still cover only the fixture endpoint plus other IPv4 destinations; IPv6 and UDP remain `UNKNOWN` and must not be described as closed.
