# Architect review — bounded handoff recursion failures

Source: `112f545796911f3c5b545d9dbb718fbf4dbce76b`. Requested role/profile: `sf-architect`, `gpt-6.2-sol` / high. Host reported model `gpt-6.2-sol`; effective effort and named TOML profile loading remain UNKNOWN.

**Decision: A1 / EXTEND.** The handoff parser has a real malformed-input error-contract defect by source inspection. `read_input` catches `JSONDecodeError` but not `RecursionError`; `_required_object` recursively scans for forbidden fields before checking shape and may likewise leak `RecursionError`. This can affect JSON strings/bytes and Python object callers of `validate_input`, `serialize_input`, and `validate_result`.

The bounded source search found direct consumers in the handoff and Developer scope test suites. Production runtime exposure is UNKNOWN; this review does not establish a production call path or permission bypass.

Recommended narrow fix: normalize `RecursionError` to fixed, redacted `ValueError` at JSON decode, forbidden-field traversal, and JSON serialization boundaries. Do not change valid v1 payloads, the 16 KiB wire limit, recursion settings, or introduce a new depth threshold as part of this error-normalization fix.

Test IDs: `HANDOFF-JSON-02` (deep JSON string/bytes under an isolated low recursion limit), `HANDOFF-OBJECT-01` (cyclic input through validation/serialization), `HANDOFF-OBJECT-02` (cyclic result rejection). Also preserve existing valid roundtrip, forbidden/duplicate-key, size, stale-SHA, full handoff, Developer scope, governance and runtime-campaign coverage. Refresh only the exact approved source pins for changed parser/test/ADR/governance files. Keep historical campaign manifests unchanged; continuation remains `INTEGRATION_ISOLATED`, runtime `NOT_RUN`, release approval `false`.

No files or tests were changed/run during this architecture review. Rollback parser, tests and coupled source pins atomically. No migration is needed; malformed pending handoffs should be regenerated from trusted task scope.
