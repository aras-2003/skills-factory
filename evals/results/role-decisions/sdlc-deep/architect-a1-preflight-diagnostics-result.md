# Architect assessment: preflight failure diagnostics

## Scope reviewed

Candidate source revision: `dc7c99bb5adfcdf8d7d181a6b0385601a127b45b`.

The exact-SHA credential-free local-mock run returned `runtime_process_started=false`, permission cases `NOT_RUN`, and a generic precondition/protocol reason. It did not include filesystem or network boundary results. The observed failure phase is unknown; do not infer an OS sandbox denial from this receipt.

## Recommendation

**Architect routing for the proposed implementation is A1 / trigger NONE / SKIP.** The planned change adds two optional fields to the existing local-mock receipt. Repository search found no strict consumer or parser for this receipt, and aggregation reads the existing boundary and case statuses only.

Set a fixed allowlisted phase immediately before each operation: `runtime_setup`, `candidate_check`, `runtime_check`, `fixture_setup`, `profile_setup`, `filesystem_preflight`, `network_preflight`, `app_server_start`, or `protocol`. On the existing exception handler, add only `failure_phase` and `failure_class` using fixed values. The phase means where the exception surfaced, not its root cause.

Classify `TimeoutError` and `subprocess.TimeoutExpired` before broader exception families. Use only fixed classes such as `os_error`, `timeout`, `subprocess_error`, `value_error`, `type_error`, `key_error`, `runtime_error`, and `other`. Never serialize exception messages, class names from arbitrary subclasses, traceback, exception arguments, file paths, commands, environment, or fixture payloads.

Preserve the existing catch set, generic reason, cleanup, launch behavior, status logic, and all permission gates. Tests should inject hostile exception text, assert only fixed labels appear, prove preflight failure prevents App Server launch, and verify BLOCKED/FAIL aggregation is unchanged. Reassess routing if a strict downstream consumer or behavior change appears.

This is source-only advice. The effective model, effort, and loaded profile are not exposed by the collaboration host (`UNKNOWN`).
