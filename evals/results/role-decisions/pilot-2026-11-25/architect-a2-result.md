# Architect A2 contract recommendation

Decision: retain schema v1.0 compatibility and emit v1.1 for new role observations. Keep exact host event times nullable; add coordinator request/observation bounds and evidence references rather than filling exact host timestamps from a local clock. Execution state can remain ACCEPTED/COMPLETED when returned by the host while start/end event times remain unknown with an explicit reason. Timing becomes UNKNOWN unless strict exact times or non-overlapping bounds prove ordering.

For v1.1, `ON_TIME`/`EARLY` require accepted dispatch before action; `LATE` requires action proven before decision/dispatch; an acknowledgment observed after action does not prove late dispatch. `MISSED` requires a qualifying action after SKIP; `CORRECT_SKIP` requires reviewer confirmation and no action evidence. Retry attempts retain immutable decision identity, explicit links, unique IDs and cycle checks even when event times are unknown. Do not treat Codex MCP receipts as subagent telemetry.

Architect confirmed this is A2 because it changes a shared receipt/validator contract and CI evidence interpretation. This summary is a sanitized reference to the Architect result, not proof of effective host model/effort.
