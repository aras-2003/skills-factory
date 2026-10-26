# Financial Quality Engine — stage 1

Standalone source-only diagnostics for the eight ratios in Feroldi's
Buffett-inspired income-statement visual and selected cash-flow safeguards.

## Scope
- Gross margin; SG&A/gross profit; R&D/gross profit; depreciation/gross profit.
- Interest/operating income and inverse coverage; effective tax rate.
- Net income margin; diluted EPS growth (undefined for nonpositive base EPS).
- Operating margin, FCF and FCF conversion.
- **EBIT/invested capital is explicitly only a proxy, NOT ROIC**.
  Full ROIC needs NOPAT and average invested capital.
- No hard coded >40%, <30%, >20% thresholds; those lack sector portability.
- Undefined ratios return null; no synthetic quality score or recommendations.

Use `scripts/investing/financial_quality.py` with validated reporting periods.
Test: `python -m unittest discover -s tests/investing -p 'test_financial_quality.py'`.

## Not yet integrated
Financial statement data provider, automated taxonomy mappings, TTM chronology,
sector peer cohorts, persistence and graphical trend dashboard. These are follow-up
gates, not implied by this PR. Do not claim production Investment OS integration.

## Historical margin visualization (stage 1)
`scripts/investing/financial_quality_visual.py` renders a source-only accessible SVG for three or more chronological, comparable observations. The chart shows gross, operating, net and FCF margin trends, keeps gaps unconnected, flags missing series and avoids invented scores. No direct UI embedding or live data loading is implied. Test with `python -m unittest discover -s tests/investing -p 'test_financial_quality_visual.py'`.
