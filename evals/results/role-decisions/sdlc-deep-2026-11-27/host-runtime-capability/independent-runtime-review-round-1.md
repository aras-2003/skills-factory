# Independent review — runtime evidence, round 1

Reviewer role requested: `sf-independent-reviewer`, `gpt-6.1-terra` / high. Effective model and automatic profile loading were not exposed in the reviewer response. The review was read-only and checked exact source candidate `f51c4fad6aceeab545943812794f6f44132239fc`, the linked #820 evidence, role records and the first App Server ACL receipt.

## Findings

- **P1 — ACL denial evidence was too broad in the first receipt.** It stored only a boolean matched against several generic stderr phrases. A hash did not show which phrase occurred or distinguish an ordinary permission error. Initial disposition: `PARTIAL`.
- **P1 — interruption/resume was overstated.** The sanitized B stream showed a distinct thread and a successful read-classified command, but not the exact source/base/AGENTS content. A ended with `turn.completed`, not a host-reported `interrupted` status. No marker-write attempt occurred in B. `CLI-RESUME-01` remains `INCOMPLETE`.
- **P2 — the probe source was temporary and the evidence hash is not a host signature.** A local hash supports byte consistency, not authenticated provenance.

The reviewer confirmed that PR #820 and its source-level test/review/rework evidence do not establish a full runtime Developer→Executor→Reviewer→rework cycle. Developer High model and effort are independently reported by the App Server thread/start response; profile auto-loading remains `UNKNOWN`. Approval non-transfer, Desktop per-child ACL and MCP-tool denial remain `NOT_RUN`/`UNKNOWN`.

After this review, the coordinator reran the same positive/negative ACL operation and retained a redacted `PermissionError`, `errno=1` (`EPERM`), and `Operation not permitted` category. The bounded-resume claims were narrowed. Independent re-review of these corrections is pending.
