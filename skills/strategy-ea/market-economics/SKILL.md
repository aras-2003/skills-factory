---
name: market-economics
description: Reconcile explicit market sizing and customer-segment evidence, calculate SAM/SOM and white space, and state transferability limits. Use for market size, needs-based segmentation or whitespace economics; do not invent demand, infer evidence, or duplicate competitive-intelligence research.
---

# Market economics

Use dated, sourced inputs to keep top-down TAM and bottom-up TAM separate, compare their difference, and calculate segment-derived SAM/SOM and uncovered serviceable value. The calculator requires an explicit as-of date, currency, source ID and publication date for each number. It rejects future evidence and invalid shares, leaves unknown segments unknown, and does not convert currencies or assume cross-market transferability.

Define segments by the supplied customer need/JTBD evidence and explain inclusion criteria in the narrative. Do not call an addressable estimate a forecast, or infer a customer voice from market totals. Reuse canonical competitive-intelligence and strategic-position work for competitor facts and transferability judgments.

Run `python engine.py input.json` (or provide JSON on stdin) for deterministic arithmetic. Treat the output as a sizing aid, not a market fact or investment decision. The original upstream source corpus and license baseline were unavailable for this candidate; no upstream content is copied or claimed equivalent.
