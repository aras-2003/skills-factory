# ENG-22 local Phoenix trajectory verification — 2026-10-28

## Result

A fresh, local run of the exact committed Cloud Next package for canonical Skills Factory source `ad9c7305d22d4ac276bf2762207a79b081888730` (release `1.38.387+ad9c7305d22d`) produced a real parent OpenTelemetry span containing three real embedded MCP handler calls: `runtime_info`, `list_skills`, and `load_skill`. All child spans shared the parent trace ID, and each tool receipt `run_id` matched it. The trace was exported to the locally hosted Arize Phoenix `20.26.1` instance and inspected in its UI; Phoenix showed the parent and all three children.

This proves the repository runtime can join calls when a host creates and propagates an OpenTelemetry context. It does not prove MCP wire transport or ChatGPT conversation correlation: the local Python host created the parent span. Do not close ENG-22 on this evidence.

## Safety and privacy

Phoenix listened only on `127.0.0.1:6006`, with telemetry disabled, remote export disabled, external resources disabled, and an ephemeral local working directory. The actual MCP handlers performed no external reads or writes. The checked trace carries tool/capability identity and hashes; it does not contain prompt text, raw tool inputs, skill instructions, secrets, or model reasoning.

## Evidence

- `assessment.json` records canonical source, package release, trace ID, three handler spans, receipt identity match, and scope limit.
- `phoenix-trace.ax.txt` and `phoenix-trace.png` show the observed Phoenix trace and tool-child rows.
- The runner and full raw receipts remain in the local acceptance directory used for this run. The repository artifact is a bounded, redacted verification record.

## Remaining acceptance

ENG-22 remains in Verification. The MCP host still needs to supply a stable conversation/run context for separate ChatGPT tool calls, and a fresh model-level campaign must exercise forbidden production actions and expected tool paths with real receipts. No production access or writes were performed.
