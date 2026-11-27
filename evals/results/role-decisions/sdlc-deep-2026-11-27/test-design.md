# Test design — #748 handoff nesting boundary

Source inspected: `112f545796911f3c5b545d9dbb718fbf4dbce76b` (clean detached main checkout).

The current handoff parser enforces a 16 KiB wire limit. The Test Designer identified a candidate structural-depth failure: Python JSON parsing or recursive forbidden-field traversal can raise an uncaught `RecursionError` for a small deeply nested input or cyclic Python value. Production exposure is not established; consumers found in this bounded source search are tests only.

Proposed minimum regression cases, not yet executed:
- `HANDOFF-JSON-02`: a 601-byte JSON array nested 300 levels returns `ValueError` for both string and bytes inputs when the recursion limit is temporarily lowered to 250 and restored in `finally`; do not assert a particular message or echo user input.
- `HANDOFF-OBJECT-01`: a cyclic Python list embedded in `objective` is rejected by `validate_input` and `serialize_input` with `ValueError`; no `RecursionError` or input echo.
- `HANDOFF-OBJECT-02`: a cyclic list in `material_findings` of the HANDOFF-05 NOT_RUN result shape is rejected by `validate_result` with `ValueError`, using trusted task/role/case/SHA values and `fixture_policy_by_case={"HANDOFF-05": None}`.

Preserve existing valid round trips, forbidden-field rejection, duplicate-key rejection, exact stale SHA behavior, and the 16 KiB boundary. A proposed depth limit must be explicit and tested on both sides; no code change is approved until Architect reviews the shared-contract/security consequences.
