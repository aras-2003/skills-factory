# Skills Factory — Output Systems Portfolio (decision architecture, 2026-10-10)

This is an **index of GitHub issues**, not an independent backlog, Project field state, or deployment proof. GitHub Issues are the intended work-item source; [legacy reconciliation #160](https://github.com/aras-2003/skills-factory/issues/160) is unfinished. Priority in titles/bodies is **not evidence of synchronized GitHub Projects priority fields**.

## Principle: separate the analysis from its delivery medium

**Domain systems** (Strategy OS, OAF, Investing, Commerce, Career etc.) own the business/technical question, evidence, decision alternatives, constraints, substantive recommendations and validation. A communication format may highlight flaws but cannot silently change source conclusions.

**Four delivery modes are useful now:** direct chat and `report-composer`, Report OS (long DOCX/PDF), Presentation OS (slides), Interactive Experience OS (explorable web). The **fifth** — spreadsheet/model delivery — is an **optional thin adapter**, not a new active OS; P2 value assessment / P3 build only if justified. Single charts remain `visual-output-design`. Generic marketing/company websites remain web-design; an article remains Writing.

Consumers can be combined **only when requested**. They share the same source result revision and IDs but have separate reading/interaction models, permissions and QA. No automatic cross-format publishing or source reanalysis.

## Prioritized execution and exact GitHub links

| Priority | ID / GitHub issue | Scope | Stage / dependency |
| --- | --- | --- | --- |
| **P1** | [OUT-01 #297](https://github.com/aras-2003/skills-factory/issues/297) | Source-owned versioned `DomainResult` / evidence/result pack | Design candidate in [draft PR #295](https://github.com/aras-2003/skills-factory/pull/295); reconcile with STR-16. No global store |
| **P1** | [OUT-02 #298](https://github.com/aras-2003/skills-factory/issues/298) | Explicit output policy/router incl. combinations & blocked capabilities | **First deterministic source-only dev** here. Source OS output parsing is still deferred |
| **P1** | [OUT-03 #299](https://github.com/aras-2003/skills-factory/issues/299) | Common source/medium/delivery quality receipts | Design first; real provider checks separately |
| **P1** | [PRES-01 #283](https://github.com/aras-2003/skills-factory/issues/283) | Slides, Canva/Figma, editable deck, PPTX target QA | [Draft PR #284](https://github.com/aras-2003/skills-factory/pull/284), NOT runtime validated |
| **P1** | [REP-01 #293](https://github.com/aras-2003/skills-factory/issues/293) | Long-form DOCX/PDF professional document | [Draft PR #295](https://github.com/aras-2003/skills-factory/pull/295), NOT runtime validated |
| **P1 design / P2 pilot** | [IEX-01 #296](https://github.com/aras-2003/skills-factory/issues/296) | Verified HTML explorer/decision room, not generic site builder | Static/offline first; web rendering not demonstrated |
| **P2** | [OUT-04 #300](https://github.com/aras-2003/skills-factory/issues/300) | Versioned artifact manifest, stale dependency map & authorized refresh | After two producer pilots and OUT-01/03 |
| **P2 discovery / P3 optional** | [SHEET-01 #301](https://github.com/aras-2003/skills-factory/issues/301) | Optional thin XLSX/Sheets adapter for domain-validated models; likely supplements Interactive/others | **PARK development** until use cases/ROI justify |
| **Existing / shared** | [STR-16 #225](https://github.com/aras-2003/skills-factory/issues/225), [CORE-02 #183](https://github.com/aras-2003/skills-factory/issues/183), [EXI-04 #244](https://github.com/aras-2003/skills-factory/issues/244), [PRO-08 #201](https://github.com/aras-2003/skills-factory/issues/201) | Domain-to-domain handoff, evidence validation, composer/visual portability, website QA | Reuse/assess before new skills |

## Minimal dependency path

1. Agree OUT-01 semantics and ensure it does not compete with **domain-to-domain** STR-16. PR #295 currently owns the *proposal*, not a production schema. No need to block pure policy tests until full source contract is agreed.
2. Validate OUT-02 deterministic policy on **preclassified** intent, correct absent/multi output behavior and operator permissions. Do not call it a working natural language classifier.
3. Align the media-specific quality receipts under OUT-03 and test each actual provider independently.
4. Limit source WIP to at most two implementation issues (see [Scrumban #233](https://github.com/aras-2003/skills-factory/issues/233)); pick ONE consumer pilot after shared contracts, not full parallel development of all OSes.
5. Only later consider IEX static-first pilot, OUT-04 refresh and optional SHEET-01 discovery; do not over-plan dated sprints.

## Backlog / implementation honesty

No automatic XLSX writer, Canva PPTX exporter, domain-to-output adapter, interactive website or file round-trip is claimed from a plan. Existing R18 campaign freeze remains protected; all new tool/model E2E requires a separate version-pinned campaign. Source/unit tests validate only the deterministic scripts they run. **GitHub Project priority/iteration fields have not been verified by this page**.
