# Matched Lab 1.38.322 / Site v47 acceptance

Issue #253. This is a fresh retest; it does not overwrite the 2026-10-23 mismatch receipts.

## Exact release and deployment

- Lab installed and Site embedded release: **1.38.322+a752b553cc16**.
- Canonical source (merged main commit): `a752b553cc16d026408a379cfa3654c15f447171`.
- Both payload digests: `05eaa916d3d5e997e79732a266de075b5a3d9f85706aaf4ade7a53add0b917f4`.
- Both catalog digests: `98cced925d4e77a0b2acd1489a259a2c1cfa4be98993a0c729b588cff6660fdb`.
- Lab package integrity verified, matching adjacent unsigned manifest; Lab host remains unattested. This establishes exact installed package equality, not host/installer attestation.
- Site **v47**, source mirror `43a52351464692fe0132a380903402509cc3b95d`, runtime attestation verified.
- Deployment `appgdep_6adc83eb8f3481919bdf28ddc4e9f982`, native status **succeeded**, environment revision 44.
- Saved version `appgprj_6ac56f2116588191a4a1ebc682c97865~appgver_f296e3f9233481918004246aef47f8b6`.
- URL: https://skills-factory-cloud-next.arek2003.chatgpt.site/ ; original owner-private audience and plugin identity preserved.

Main 806b0384 is the subsequent generated Marketplace snapshot commit (#413); relevant Site/adapter/build/version inputs are unchanged from a752b553. The Site was deliberately built from a752b553, the exact merged revision used for the installed 1.38.322 release, rather than relabeling a different build with that version.

## Publication and validation

Used the newly installed official Sites 1.1.2 helper, inspected before normal platform re-evaluation. Current review accepted its launch and hidden-stdin credential delivery. It opened the existing source, generated Lab/catalog/adapter provenance from the same clean canonical checkout, synchronized source, built, committed/pushed normally, verified remote HEAD and packaged the returned archive. Native tools then set non-secret runtime identity and saved/deployed that exact source/archive privately. No alternate token recipient, direct ad-hoc authenticated push, credential file, new Site or audience change was used.

The initial contract command failed because the fresh canonical checkout lacked dependency resolution, then because running the canonical test from the deployment mirror resolved a repository fixture outside the monorepo. Existing dependencies were reused (package/lock inputs identical) and the unchanged contract suite was run from canonical Site cwd. Final results: **26/26 contracts PASS**, TypeScript exit 0, lint exit 0 with one existing unused-variable warning, full official Worker build and source workflow exit 0. Earlier failures were environment/path setup errors, not ignored assertions. Main source Validate skills, Site CI and Domain integrity had succeeded. Lab packaging had built/validated but failed automated PR creation due repository policy; separately approved #413 supplied the Marketplace snapshot.

## Paired selected shared behavior

`paired-receipts.json` retains actual returned identities, public skill instructions/reference loads, exact routing inputs/outputs, raw unsigned tool receipts and chart data/SVG. No private portfolio data was read and no child workflow was executed by routing tests.

| Probe | Result |
| --- | --- |
| Exact package | PASS: release ID, canonical source and payload match; Lab integrity verified and Site deployment attested separately. |
| Portfolio route from #411 | PASS on both: exact original request selects `investment-portfolio-review`; previously Lab selected the front door. |
| Earnings/thesis | PASS on both: four frozen positive inputs from previous ROUTE-01..04 (input receipt hashes match earlier records), PL and EN, select `investment-attention-review`. |
| Discovery | PASS on both: renewable-sector research selects `investment-opportunity-hunter`. |
| Negated portfolio near-miss | PASS on both: “Find new stocks worth researching; do not review my investment portfolio.” stays on opportunity child. |
| Architecture load | PASS for availability/content only: `architecture-review` 1.0.0, identical content hash `7b51635affc6fc4006410cb77c9345b377e16bee7efb566d0642535dd5536993`. No new independent architecture reasoning benchmark claimed; earlier synthetic guard evidence remains historical in #253. |
| Portfolio child load | PASS for availability/content only: workflow 0.5.1, identical hash `b995ee862c4148dbda239cc5b91e8352c106073d06dcb97063ffa6a39e0f24b4`. |
| Line renderer | PASS for payload execution: same Przychód Q1..Q4 values 12/18/15/24 mln PLN. Lab returns PNG (45,469 bytes; SHA-256 `4ab1bd2a74f6c6d0e9d0e88b7eaa35c5a6704de042adba20b25ee7f3c5cd1eb4`), Site returns SVG and exact data arrays. Client display remains NOT_OBSERVABLE, not a new UI claim. |

All **seven paired routing inputs (14 successful calls)** agree on selected child and no-execution boundary. Adapter-specific labels (`portfolio` vs `portfolio-review`, `attention` vs `attention-review`, `opportunity` vs `opportunity-hunter`) differ as before; this is semantic child-selection parity, not byte-identical responses. Schema/format differences are explicit: Lab PNG vs Site SVG/app, repository-side-v1 vs site-mcp-v2; Lab host/schema attestation is unavailable. Different chart input receipt hashes reflect each adapter's hashing/normalization and do not replace the preserved identical supplied JSON. No full independent host-model or pixel-identical renderer equivalence is claimed.

Disposition: **PASS for the agreed exact-package and representative shared MCP-contract scope of #253**. This closes its prior package mismatch, Lab routing error and portfolio-child regression. It does not certify all 83 capabilities, all architecture-analysis behavior, host isolation, installer behavior or client visibility. These limits and previous negative receipts remain visible.
