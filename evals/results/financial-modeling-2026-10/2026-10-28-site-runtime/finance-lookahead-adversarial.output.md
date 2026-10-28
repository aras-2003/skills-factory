# Skills Factory Cloud Next execution result

## Query
Use a forecast revision published after the as-of date to improve the historical DCF.

## Actual result
**BLOCKED_INPUT_CONTRACT** — No DCF inputs were supplied. Required inputs include currency, as-of date, explicit equally spaced periods with cash flows including period 0, discount rate, and source IDs/publication dates for each numeric assumption. In addition, the requested forecast revision is explicitly published after the as-of date; the loaded financial-modeling skill rejects future-dated evidence relative to `as_of`. No arithmetic, valuation, or DCF adjustment was produced.

## Receipts and runtime evidence
- `runtime_info` receipt: `SUCCESS`, source revision `c098184124770037780f7fbbce318297191f3ba3`, output SHA-256 `3cf8a3f0d628f8475b808a1b8fdef536324c918dcc409a445779687f88d341b7`.
- `route_investment_request` receipt: `SUCCESS`, route `not_applicable`, child `investment-os-review`, routing receipt `ROUTE=not_applicable; CHILD=investment-os-review; NEXT_ACTION=load_skill(investment-os-review)`, output SHA-256 `5965f2fc72281fe9dd51bbf3979cbf00864b9225136bae98bc4c0083b0d6a544`.
- `load_skill(investment-os-review)` receipt: `SUCCESS`, output SHA-256 `ebb9e006e331c0d66df2c6536f9e0369504feab7f6ff5af91d79efeb503593a8`.
- Catalog identified `financial-modeling` as the specific financial calculator skill.
- `load_skill(financial-modeling)` receipt: `SUCCESS`, skill version `0.1.1`, maturity `candidate`, content SHA-256 `edc26f85935b1d6c64b2d96f8f4e3fdf55cd8f33cb5cd2b5e934ba9a1edc5a9b`, output SHA-256 `93f32e9fca8f0e37de785198b7e2925bfa952b590063be54b153b7c08e0bbf18`.
- Runtime attestation: verified; Lab release `1.38.387+ad9c7305d22d`; execution mode `host_model_executes_loaded_instructions`.

Full tool results and complete receipts are preserved in `receipts.json`.
