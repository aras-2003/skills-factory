# Paired runtime probes

The same synthetic inputs were sent to installed Lab 1.38.320 and Site v46 / 1.38.313. `paired-probes.json` preserves exact inputs, runtime identities, outputs and receipts. No private data was read and no child workflow executed.

| Probe | Observed result |
| --- | --- |
| Identity | MISMATCH: Lab 1.38.320 vs Site 1.38.313. Lab package integrity verified; Lab host attestation unavailable. Site deployment attestation verified. |
| architecture-review load | Identical content hash `7b51635affc6fc4006410cb77c9345b377e16bee7efb566d0642535dd5536993`; this establishes content loading, not architecture-analysis behavior. |
| Line chart | Both renderers execute with the supplied four values. Lab returns PNG; Site returns SVG. Inline client visibility is not asserted. |
| Portfolio routing | Lab returns `unknown` / investment-os-review; Site returns portfolio-review / investment-portfolio-review. A real child-selection mismatch. |

The canonical Python router recognizes “review my portfolio” but misses the unambiguous “review my investment portfolio”. The scoped correction recognizes review of my/this/the investment portfolio while preserving negated alternatives. Local canonical router tests: 23/23 PASS; Site adapter contract suite: 26/26 PASS. Tests include the observed full input and a discovery request that explicitly excludes portfolio review.

These are local source checks, not an installed-runtime retest of the fix. The source change is not merged, packaged for installation or deployed. #253 remains Verification until the approved exact package is installed/deployed and paired cases pass. This finding does not rewrite the earlier six-case earnings regression or historical campaign totals.
