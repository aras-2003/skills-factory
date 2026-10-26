# OAF Health Check — frozen runtime negative examples

These examples come from the real unassisted R4 FAIL for `fallback-strategy-production-002` at behavior source `28a7681cf024bb7aaad7a979e7ce7253139d5bd4`.

They are validation examples only. Their presence in source or static tests is **not** runtime evidence that the new behavior is fixed.

## Disabled specialist claimed as available

In the Lab fallback retest on 2026-10-22, the user had disabled `strategy-to-execution-diagnostic`, but the `oaf-health-check` answer claimed to have used strategy-to-execution diagnostics. This is a runtime FAIL: source/package presence is not proof that a specialist is available in the current session, and an unavailable branch must not be simulated or claimed as run. The regression fixture is `fallback-strategy-disabled-lab-001`.

## Unsupported mechanism in executive diagnosis

> Firma ma strategię, ale nie ma stabilnego mechanizmu przekładania jej na porównywalne decyzje portfelowe i roadmapy.

Why invalid: the input establishes reactive initiative selection, quarterly priority changes and roadmap/outcome disconnect. It does not establish absence of a stable mechanism.

Required rewrite pattern: keep the observed symptoms as observed claims; express absence/failure of a mechanism only as a hypothesis unless direct evidence establishes it.

## Unsupported consequence in heatmap

> Zespoły nie mają wspólnego mechanizmu oceny postępu

Why invalid: inability to link roadmap to measurable strategic outcomes does not establish absence of a shared progress-assessment mechanism.

Required rewrite pattern: split the observed roadmap/outcome disconnect from any hypothesised mechanism or consequence.

## Reviewer unknown converted to organisational ambiguity

> Nie wiadomo, kto ma mandat do zmiany priorytetów, finansowania i pojemności

Why invalid when treated as an organisational finding: the evaluator/runtime lacks decision evidence. That means the mandate is **unknown to the review**, not that the organisation's mandate is confirmed unclear.

Required rewrite pattern: state the evidence gap and, if material, a hypothesis about decision-rights ambiguity.

## Sample sufficiency overclaim

> Ten mały przekrój rozstrzygnie

Why invalid: a bounded sample can test competing hypotheses but may remain inconclusive.

Required rewrite pattern: specify what the sample can discriminate and when expansion is required.

## Reviewer evidence gap converted to organisational absence

> Portfolio nie ma obecnie wystarczająco porównywalnych danych do rzetelnego priorytetyzowania — wynika z braku wskazanych outcome’ów, właścicieli, kosztu, capacity, zależności i kosztu opóźnienia.

Why invalid: the run did not collect initiative records. The cited basis proves only that those fields were not supplied to the review. It does not prove the organisation or portfolio lacks them.

Required rewrite pattern: “this review cannot rank initiatives from the supplied evidence”; if organisational data absence is plausible, keep it as a hypothesis until organisation-level evidence establishes it.

