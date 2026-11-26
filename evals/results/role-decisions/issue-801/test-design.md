# Issue #801 test design

- Baseline: `88cf9f314c90aa8c6d3a14c01c04ed64282e91c5`
- Scope: MON-01 through MON-07
- State: design only; no case executed.

| Case | Type | Input / fault | Expected | Forbidden | Evidence |
| --- | --- | --- | --- | --- | --- |
| MON-01-A | authenticated runtime E2E | Existing Scheduled Task starts a pinned slot and SHA | Server-side execution produces a correlated receipt and exact-SHA report | Host simulation, uncorrelated receipt, or stale source | Scheduler invocation + MCP trace + receipt + report digest |
| MON-02-A | database integration | Same slot submitted sequentially | One atomic claim; no second write | Duplicate canonical run | Claim and canonical readback |
| MON-02-B | database concurrency | Same slot through separate live connections | Exactly one winner | Race yielding duplicate canonical writes | Concurrent call traces + claim/run readback |
| MON-02-C | recovery | Retry after partial source/write failure | Idempotent resume and terminal state | Duplicate write or lost terminal status | Retry receipt + database readback |
| MON-03-A | provider integration | One approved source times out or returns 5xx | Isolate the failed input; continue independent inputs within bounded retry policy | Whole run silently passing or stale data represented as fresh | Per-input attempts and terminal states |
| MON-03-B | provider security | Missing or unapproved source | Fail closed for that input | Calling an unapproved or paid source | Allowlist decision + no-call evidence |
| MON-03-C | provider integration | Retry budget exhausted | Explicit terminal failure/data gap for every input | Infinite retry, hidden partial failure | Attempt count + terminal result |
| MON-04-A | deterministic contract | Frozen canonical MSS 1.0 fixture/oracle and pinned scoring function | Match accepted versioned canonical score semantics | Changing MSS v1 or guessing a new oracle | Fixture digest + calculation + readback |
| MON-04-B | deterministic fallback | Approved dated free sources available as of slot time | Deterministic fallback with source vintage, freshness, coverage, provenance | Future/stale data, fabricated estimate, or candidate silently promoted | Source snapshot digests + coverage + provenance |
| MON-04-C | failure/data quality | Required source data absent/stale | DATA_GAP / NOT_ASSESSED, with separate coverage and terminal status | Zero score, false VERIFIED status, or a fake full-coverage report | Missing-source fixture + explicit result |
| MON-05-A | security | Scheduled Task credential absent | Fail closed before reads/writes requiring identity | Anonymous access or fallback to broad client key | Auth failure receipt, no-write readback |
| MON-05-B | resilience | Timeout before and after backend commit | Safe retry by slot idempotency; no duplicate writes | Ambiguous success treated as failure then duplicated | Trace across timeout, retry, final readback |
| MON-05-C | security | Missing/incorrect scheduled identity or stale SHA | Reject before provider fetch or persistence | Header-presence-only authorization or secret in output/log | Negative auth tests + redacted output inspection |
| MON-06-A | regression + independent gates | Exact candidate SHA | Existing MCP, tool schema, routing neighbors and database consumers pass separate exact-SHA checks | Self-review presented as independent, CI treated as runtime PASS | Executor command/output/exit + independent review |
| MON-07-A | release/runtime | Private Site publish from one canonical SHA | Site version, mirror SHA, canonical SHA and attestation agree | Site/plugin identity change or attestation mismatch | Native deployment receipt + runtime_info |
| MON-07-B | scheduled-task E2E | Actual existing 11:00/23:00 task after verified deployment; rollback path | One authenticated run, report and canonical readback; restore old task config on rollback | Manual trigger labeled scheduled, second scheduler, unverified cutover | Actual scheduler event + report receipt + rollback observation |

### RED and scope boundaries

For deterministic paths, write tests that fail because the exact new MCP capability and atomic slot contract are absent on the baseline; do not create fake provider/database failures to claim RED. Existing unit mocks validate adapter logic but cannot establish database atomicity, effective authentication, deployed identity or real Scheduled Task execution.

MSS 1.0's exact production oracle, private task identity/prompt, approved source allowlist, currently authorized ingestion mappings, and supported Site/server secret interface must be established before finalizing executable fixtures. The current repository contains no complete live DB migration/consumer graph; keep unverified edges UNKNOWN and preserve broad regression selection.

### Execution state

All listed cases remain NOT_RUN. Each eventual receipt must record candidate SHA, fixture/input digest where applicable, actual command or runtime event, observed output and terminal status. No portfolio identifiers, private prompt, credentials or raw sensitive traces belong in the public issue or these test definitions.
