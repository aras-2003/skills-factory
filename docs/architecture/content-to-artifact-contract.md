# Analysis → Communication Artifacts: Cross-OS Contract (candidate v0.2; Interactive Experience extension proposal)

## Decision and ownership

**Source-domain OS** (Strategy, OAF, Investing, Commerce or other subject specialist) owns **analytical truth, substantive options, recommendations, uncertainty and approvals**. **Report OS**, **Presentation OS** and the proposed **Interactive Experience OS** (IEX-01) are independent consumers that structure and render communication artifacts. Interactive controls may explore *approved supplied data/models* but may not invent new domain strategy, calculations, assumptions or recommendations. Output medium never authorizes the downstream creator to alter analytical conclusions. The user may request any one or any explicitly specified combination of outputs, or only an answer.

This is an **interoperability design proposal**, not an installed global schema, database, automatic runtime router or published API. Finalize names and compatibility with planned STR-16 and actual domain stores before implementing a shared adapter.

## Minimal versioned handoff

`DomainResult{`
- `domain, source_workflow?, result_id, source_revision, analysis_as_of, scope, governing_question, audience_constraints?`
- `findings:[{finding_id, claim, epistemic_status, evidence_ids[], as_of?, units?, comparator?, uncertainty?}]`
- `evidence:[{evidence_id, source_locator, obtained_at?, publication_date?, license?, confidentiality?, transform?}]`
- `options:[{option_id, finding_ids[], tradeoffs[], feasibility?, choice_state{HYPOTHESIS|PROPOSED|RECOMMENDED|USER_APPROVED|REJECTED|UNKNOWN}}]` when domain supports options
- `recommendations:[{recommendation_id, option_ids[], finding_ids[], rationale, status, owner?}]` where applicable
- `limitations[], contradictions[], method_notes?, domain_validation_state{PASS|FAIL|NOT_RUN|BLOCKED|UNVERIFIED}, revision_history[]`
`}`.

All downstream outputs link claim/exhibit/section/slide/**web view or scenario output** to **stable IDs and version**. Domain pack is *read-only* for report/deck/web composition. A detected material conflict returns `UPSTREAM_REVIEW_REQUIRED{source_id, evidence, proposed_change}`; only the domain owner may adopt a substantive correction. Do not silently elevate `HYPOTHESIS` into `RECOMMENDED`, user-provided into independently verified, or a rhetorical claim into a fact. User can approve a communication artifact without approving an underlying recommendation.

## Media-specific output models

| Concern | Report OS | Presentation OS | Interactive Experience OS (planned IEX-01) | Existing composer/visual |
| --- | --- | --- | --- | --- |
| User goal | Sustained reading, traceable depth, decision record | Live narration or slide-based decision support | Explorable findings, cross-filtered views, bounded scenario comparison and decision support | Chat-native compact/structured reporting |
| Plan | Sections, subheads, evidence distribution, appendices | Ghost deck, action titles, slide roles/transitions | Reader journey, coordinated views, navigation, controls→validated state/data transforms→actual visual change | Inline report sections, *single* local visual slots |
| Native artifact | Editable DOCX / optional Google Docs; PDF as consumption output | Figma Slides / Canva native deck; PPTX where supported | Self-contained offline HTML MVP; optional hosted web experience with explicit deploy/auth/backend | Native chat surface |
| Quality review | Page breaks, table splitting, TOC, cross-references, citations, font/links, full-page readability | Slide design, montage, story pacing, editability, PPTX export | Actual browser UI, functional interaction, responsive/mobile, accessibility, privacy, scenario correctness and citations | Actual inline-rendered evidence |
| Runtime proof | Create/open/render DOCX and PDF, page-by-page inspection, content/links parity receipts | Native deck creation, screenshots, PPTX reopen receipts | HTML artifact, browser render, control state-change tests; deployment, refresh and user-visible reachability *separately* when requested | Real emitted native visual payload |
| Non-goals | No deck-by-default, no reanalysis | No long document-by-default, no strategy design | No duplicate chart engine, no unverified simulation/live data, no automatic public hosting | No implicit external artifact |

`report-composer` remains the existing reusable semantic report composition layer, especially **for chat**. Its external-artifact option is not evidence that page-layout, native DOCX creation, or PDF round-trip already work. `visual-output-design` owns supported chart/diagram **and single local interactive slot** encoding, not domain analysis, chapter/slide planning or whole-site interaction architecture. Planned web-design quality checks should be reused; IEX-01 must not become a second generic website builder.

## Optional interactive data and behavior contract

Only when interactivity is requested and supported:
`ExperienceSpec{source_result_refs[],snapshot_as_of,views:[{view_id,purpose,claim_ids[],finding_ids[],source_ids[],chart_or_component_specs[]}],controls:[{control_id,label,allowed_input_domain,affected_views[],deterministic_transform_or_validated_domain_model_id?,expected_state_change}],scenarios?:[{scenario_id,model_version,assumptions[],input_bounds,outputs[],source_refs[]}],access_policy,offline_capability,hosting_target?,freshness_semantics,quality_receipts[]}`.

`Scenario` outputs are **derived** from approved/validated domain formulas or deterministic code, never evidence observed in the world. A `what-if` control does not create an authorized strategic decision; decision alternatives and their approval status remain upstream-owned. Reject invalid inputs instead of silently implying confidence. If no valid scenario model exists, provide sourced comparison/filtering only, not a fake simulation.

Choose the lightest warranted delivery profile:
- `EMBEDDED`: host-native interactive visual **only** if an actual emitted UI component can be observed; no fabricated widget API.
- `STATIC_SHAREABLE`: offline-first HTML with versioned snapshot and working controls; **recommended MVP**, no backend or authentication assumed.
- `HOSTED_REFRESHING`: authenticated/authorized site with live refresh and secure storage, only when explicitly requested and validated, with budget/hosting/privacy implications.

Security: HTML/JS static bundles are inspectable by recipients; **do not embed secrets or undisclosed confidential data**. A link to a build file is not a deployed, accessible site. `HTML_CREATED`, `BROWSER_RENDERED`, `INTERACTIONS_TESTED`, `RESPONSIVE_CHECKED`, `A11Y_CHECKED`, `DEPLOYED`, `LIVE_REFRESH_VERIFIED` and `CLIENT_DISPLAY_OBSERVED` require independent receipts.

## Intent router

1. **Analyze**: request is for solving/evaluating subject matter → source domain owns it. Respond directly or use `report-composer` when user did not ask for a file.
2. **Report**: explicit substantial written/document deliverable → Report OS. Use supplied/canonical domain result, delegating missing subject analysis only when user actually requests or it is needed to answer.
3. **Presentation**: explicit deck/slides/live talk → Presentation OS, same upstream governance.
4. **Interactive**: explicit explorable HTML/site/decision-room, or a request where interactivity is clearly the output itself → Interactive Experience OS only after checking actual host/browser/build and privacy capabilities; a single chart still routes to visual-output-design.
5. **Combination**: consume a single compatible, versioned domain result for any explicitly requested document/deck/web combination; produce outputs **independently** with medium-specific design and QA. Never report combined PASS when any one output is blocked.
6. **Narrow**: a short executive decision memo → PRO-04/report-composer; an article → Writing; an existing deck slide edit → deck specialist; one chart → visual-output-design. Do not start a full long-document or slide production pipeline.

## Capability, permissions and evidence

Preflight current runtime **per capability**, not product marketing: source retrieval, text edits, DOCX build, PDF render/export, Google Docs, Canva presentation create/edit, Figma Slides, charts, **actual HTML build and browser interaction test**, optional web hosting/auth/data-refresh, upload/privacy, reopen/inspection. `CONNECTED` for one read action does **not** imply `NATIVE_CREATED`, `EDITABLE` or `EXPORT_VERIFIED`. External transfer of private sources requires applicable authorization. If a necessary action is unavailable, return `BLOCKED` or `NOT_RUN` with missing prerequisite, no fictitious URL/file.

Release requires **separate subject-domain quality** and **medium-specific communication/artifact quality** receipts. No style critique may substitute for Strategy challenge, and no analytically rigorous result constitutes a finished DOCX, deck, working interactive web experience or deployed site.
