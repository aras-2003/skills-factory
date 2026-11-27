# Test Designer review — bounded resume canary

Requested role: `sf-test-designer`, Terra Medium. Effective host model/effort and auto-loaded profile were not exposed. Review was read-only; no canary was executed by the Test Designer.

## Design decision

The frozen `CLI-RESUME-01` case is closable only if B resumes an explicitly unfinished, observable task from A's validated checkpoint. Native `thread/resume` is a separate claim; a distinct B thread proves fresh-session handoff continuation only.

Use one unique synthetic marker path for both controls. A verifies candidate SHA and creates it under `workspaceWrite`; capture exact bytes/hash and completed command event. After A is interrupted, coordinator removes only the exact verified marker and independently verifies absence and clean Git status. B receives the compact checkpoint (including A thread/turn IDs, SHA, marker digest, completed step, and pending step), starts in a distinct `readOnly` thread, confirms the checkpoint and same SHA, executes its allowed read/validation step, then attempts the same marker path. Require the completed write command event, nonzero exit, actual OS denial (`PermissionError`/`EPERM`), absent marker, and before/after source status. The cleanup is valid because the handoff records the verified completed step and digest; the marker is not B's input.

## Protocol and stop conditions

Record initialize/initialized, policy reported by thread/start, turn/start acceptance, exact thread and turn IDs, command events, and `turn/completed` for the same A turn. Call `turn/interrupt` only while that turn is observed active. A normal completion before the interrupt means interruption is `NOT_RUN`. Accept interruption only when the correlated terminal status is `interrupted` (or another terminal status explicitly documented by the local protocol schema). B must have a different thread ID, fresh context, confirmed readOnly policy, and only the bounded checkpoint plus execution request. Model refusal, no command event, RPC error, or absent output is `NOT_RUN`; runtime initialization failure is `BLOCKED`; successful B write is `FAIL`. No approval non-transfer claim without an actual scoped approval granted in A.

## Collector correction

`aggregatedOutput: null` is a legitimate event shape. Treat it as missing output (zero retained characters, no digest), continue consuming notifications, and stop A collection only after the expected marker command completes—not after an earlier SHA/read command. A disconnected process or collector exception is not an interrupted-turn event. Before retry, verify markers and source state; never combine receipts from different attempts.

The previous retry started App Server after an authorized sandbox escalation but the collector crashed on `aggregatedOutput: null` during a non-marker command. Both markers were absent and scratch Git status was clean afterward; no interrupted-turn or B execution evidence exists.
