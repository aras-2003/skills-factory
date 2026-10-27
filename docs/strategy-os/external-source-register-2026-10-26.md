# Strategy OS — external reference-source register (2026-10-26; verified 2026-10-27)

This document is the **provenance register** for the seven-ZIP comparison corpus. On 2026-10-27, each archive was re-fetched from its listed public source and its SHA-256 matched the previously recorded archive byte-for-byte. The 350-member file index and archive manifest were generated from those verified bytes. GitHub sources are pinned to the commits recorded below; a later change to a branch URL fails the archive hash check. ZIP members were read in place without extraction.

The repository stores only source URLs, license findings, archive/member hashes and paths; it does not redistribute the third-party ZIPs or skill text. The three Oria pages describe free downloads but the ZIPs include no license file, and three community repositories likewise contain no license file. Treat those five packages as reference-only and do not copy their prose or code. The two MIT repositories permit reuse subject to preserving their license notices; that permission does not imply official McKinsey, BCG, Accenture or Bain authorship. The downloaded ZIPs remain temporary local audit inputs, not a durable binary archive. Re-fetch and verify against the manifest before a later review.

For exact paths and per-file SHA-256 values, use `strategy-source-manifest.json` and `strategy-source-file-index.csv`. They are committed traceability artifacts derived from the archive bytes whose hashes appear below.

| Verified archive | SHA-256 | Source | GitHub commit | License file in archive |
|---|---|---|---|---|
| `21-strategy-skills-for-claude-skills.zip` | `8a1c43d39328927ce58fba294010ab1f977e903fe2fe0f7e02c321e8c21a96b7` | https://www.oria.one/resources/21-strategy-skills-for-claude | — | not found |
| `tier-one-strategy-skills-for-claude-skills.zip` | `fcc70c0a7460fdb421cdd2a384c47c4c6b453c3c99ce30c41fcacb6de0827e69` | https://www.oria.one/resources/tier-one-strategy-skills-for-claude | — | not found |
| `excel-inspired-claude-skills-strategy-skills.zip` | `e7a2a8a12f4eb97f8e3e4ac042d499424917ae9ba57a3911e5ce73557574f221` | https://www.oria.one/resources/excel-inspired-claude-skills-strategy | — | not found |
| `mckinsey_skills-main.zip` | `fcc531bb6015d9482f40b3cd3e0b54b760f0a6acdb4e3b5477a32b7744f19285` | https://github.com/callmeramzo/mckinsey_skills | `5023cc979fa88dc4c64f804f12aa9682d330606f` | not found |
| `mckinsey-bcg-consulting-main.zip` | `d6365ef2783139227b2ef1301672cab78c958ffbfa920e9dcd6bd5230fdaba38` | https://github.com/MichaelRochonnn/mckinsey-bcg-consulting | `3ca573be6ae3b216c959cbb865c4eaf7d62fd0bb` | not found |
| `business-consulting-main.zip` | `e47518d78bd5d987b51f03159b7ad77973893dbe771acbcb3b9bef77ea609ea9` | https://github.com/abinauv/business-consulting | `8808ffb170bd4f8d8fadcc7e107cc9d124837570` | MIT |
| `consultant-main.zip` | `af3eb3252085b6c49d6f6aba4af5fe45ed00e676c82ce976c321ab5c401f76b7` | https://github.com/yoichiojima-2/consultant | `9a1ea0e2dac27be0b7448677ac47db4b2044b4af` | MIT |

## Non-negotiable benchmark practices
1. Skills Factory/OAF and proposed Strategy OS are **separate** evaluation columns; roadmap is not implementation.
2. McKinsey-style community packages and mixed McKinsey/BCG are **not** official McKinsey/BCG outputs. Consultant mentions Accenture and Bain but is not a provenance substitute for their branded packs.
3. Per competency, record exact `archive`, internal `path`, SHA-256, license, referenced STR issue, method version, source methodology, and independent observed test outcomes.
4. Rate 1–5 separately for method and AI implementation with `N/O` for missing source or unexecuted tests.
5. No silent third-party code or prose imports to this public repo without reviewed rights. Two archives contain an MIT LICENSE, five have no standalone LICENSE in the ZIP; treat the latter as reference-only and do not redistribute excerpts without permission.
6. Golden/negative/adversarial cases should compare a frozen imported baseline with final Strategy OS output; preserve inputs, outputs, provenance, model/date, calculation tool receipts, reviewer score, and regression status.
