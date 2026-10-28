# Financial modeling: synthetic-input provenance gate

## Observation

On 2026-10-28, the Cloud Chat at https://chatgpt.com/c/6ae1c20b-57cc-83ed-8970-79a29144baf2 received synthetic cash flows `[-100, 60, 60]`, a 10% per-period discount rate and an annual period convention, but no currency, as-of date, source IDs or publication dates.

This started as a complete-input probe, but browser text entry submitted the first paragraph at a newline and left the JSON payload in the composer. It is not a valid execution of the planned golden case. The actually submitted missing-metadata request is preserved as an exploratory negative observation.

The response calculated NPV `4.13`, displayed discounted cash flows, acknowledged the missing metadata and used `ARITHMETIC_VERIFIED / MODEL_INPUT_INCOMPLETE`. That response violates the candidate's required rejection of incomplete inputs. It did not invent the missing metadata.

The response claimed Lab 1.38.386, financial-modeling v0.1.0 and canonical source `f72983dc`. The visible processing disclosure did not expose raw MCP tool calls. These claims alone do not establish which instructions the Chat executor actually loaded; this is not a verified end-to-end MCP campaign result.

## Independent machine evidence

Direct live MCP calls independently identified canonical source `f72983dc5d5a94c56b7e02f9c425707f88dd184b`, Lab 1.38.386 and Site mirror `d4f1608a6f481a3b1d8f8b42b4b4b2004f2b6182`. All four strategy calculators returned by `load_skill` matched their canonical source bytes. Executing those returned sources against the canonical unit suites passed 30 tests (financial 13, market 4, strategy 4, value 9). This proves calculator transport and tested deterministic behavior, not Chat workflow acceptance. The financial engine SHA-256 was `90afb3a8fcc75061e9c6d0545db9cff0a4488f3ddd880a0b1ded849ccb9e5769`.

## Change and remaining gate

Candidate v0.1.1 explicitly stops before arithmetic when required metadata is missing, including synthetic/educational inputs, and forbids a disclaimer-based partial calculation. The negative case now contains actual numbers and that temptation. Campaign input/instruction hashes are refreshed. Arithmetic code is unchanged.

Runtime acceptance of v0.1.1 remains NOT_RUN and release approval remains false. Re-run the complete positive input and strengthened negative case with independently observable tool execution after publication. This report does not close #448 or #450.
