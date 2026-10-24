# Fundamental Intelligence (P1 core, not production)
Source-backed benchmark computations, not an LLM guessing ratios. Python 3.10+; `openpyxl` for XLSX. Run: `cd skills/investing/fundamental-intelligence && python -m unittest -v`.

Invariants: no fictitious Damodaran numbers, source dates checked for lookahead, no incompatible unit/definition comparisons, no silent missing-value fills. Parser uses explicit sheet/columns, source URL, SHA-256, cell coordinates and PROVISIONAL-by-default status. Damodaran industry averages **cannot** generate peer percentiles. A minimum of five real company observations is required.

This PR is a scoped implementation foundation. **NOT YET IMPLEMENTED**: verified real 2026 Damodaran XLSX fixture/column map, annual ingestion job, release snapshots, Supabase migration/API, industry mapping, complete metric registry, scoring profiles, downstream workflow wiring, runtime tests. Do not label this production ready. No portfolio state changes.
