# Controlled domain review protocol

Issue #227 (ENG-19). Source basis: main `a752b553cc16d026408a379cfa3654c15f447171`, `docs/LIFECYCLE.md`, `docs/roadmap/2026-10-05/README.md`, and the current GitHub operating model. A review produces an evidence-backed assessment and small change/test plan; it does not promote, downgrade, publish or merge a component.

## Entry gate and current quality closeout

Before starting a domain review, record the final disposition, exact scope, evidence and follow-up owner for every current quality process/campaign. A final assessment may be PASS, FAIL, ITERATE, BLOCKED or MISMATCH; it must not imply that an unresolved defect passed. A completed assessment and its open remediation issue are distinct. Do not demand closure of every linked defect as an unstated replacement for this gate.

| Process | Final disposition and evidence | Remaining work |
| --- | --- | --- |
| #311 historical campaign | Owner explicitly authorized archival on 2026-10-24: “Archiwizuj stary przebieg bez zmiany wyników”. #311 is Completed/Done. Versioned record: PR #412, head `993647850c7942b2640a8d617bf475722cad0a94`; 122 PASS / 44 FAIL / 72 BLOCKED unchanged. | Archival does not declare historical defects fixed. Three owner-excluded cases stay excluded. |
| #289 bounded current regression | Completed/Done: six frozen routing cases PASS on installed Lab 1.38.320, verified package digest and receipts in #253 comment `6373446394`. This is the owner-approved basic regression, not certification of 54 skills. | Broader behavioral certification is not claimed. |
| #237 matched evaluation | Completed/Done: independent blind review under Luna orchestration, 57 assertions / nine aggregates / 41 quote spans, PR #410 head `5f30ed45`; no-skill 0/3, 0.3.4 1/3, proposed 0.3.5 2/3; final ITERATE. | Candidate hardening remains draft #410; no promotion. |
| #253 paired runtime assessment | Finished run: MISMATCH / compatibility NOT_VERIFIED. Exact inputs, identities and receipts in merged PR #411. Lab 1.38.320 vs Site v46 / 1.38.313; portfolio child selection differs. | #253 stays open. Source correction #411 merged at `a752b553`; package PR #413, installation, approved Site publication and exact-pair retest remain. Publication route is blocked by platform review. |

The dispositions above finish the current assessment runs; they do not convert failures into passes. The review-entry decision was independently checked by the Luna campaign-disposition reviewer against #227/#232 and the canonical roadmap wording. Its conclusion: final evidence-backed dispositions are required; blanket closure of all remediation issues is not.

## One-domain execution

Review WIP is **one implemented domain**. Record the chosen domain, reviewer, start, source revision and reason before analysis. Choose by actual use, risk and dependencies after quality closeout, not by sweeping the whole roadmap. The authorized next review is Meta (#232), because it defines evaluation, packaging and release boundaries used by other domains. Other domain reviews remain queued.

Freeze scope from actual source paths and catalog domains, including workflow entrypoints and shared capabilities. Reconcile source membership with the runtime catalog; do not infer membership or availability from counts. A planned or placeholder capability is not implemented scope.

## Required component record

For every existing skill/workflow, record:

- canonical path, owner, version, maturity and exact Git revision/content hash;
- channel/package availability, runtime load receipts, release/source/payload identity and differences;
- responsibility, positive intent, adjacent/competing intent and explicit handoff/stop boundaries;
- component/workflow/tool/reference dependencies, capability permissions and private-data or untrusted-input handling;
- source tests, executable validators/CI gates, exact runtime evidence, scope/age and missing evidence;
- source-to-build-to-package-to-manifest checks, keeping verified unsigned package integrity separate from deployment attestation and installer behavior;
- executor/evaluator separation and any independent review evidence, with missing isolation evidence marked unverified;
- recommendation: retain, adopt, adapt, update, defer or no-change; rationale, smallest change, tests, dependencies and acceptance criteria.

Do not fabricate a tool, source, execution, receipt or test result. A source test is source evidence; an installed load is availability/content evidence; only actual workflow execution supports behavior claims. Keep absent runtime evidence NOT_RUN/UNVERIFIED. A different version or similar passing case does not overwrite a failed receipt.

## Review and delivery gates

Inspect actual instructions, references, manifests, builders, validators, tests and workflow configuration. Compare semantic requirements, not just matching words. Identify stale or contradictory instructions with source locations. Verify permissions and external-action authorization; never infer publication authority from a release recommendation or a successful build.

Save a versioned inventory, findings and adoption/update plan. Recommendations require a reason, a narrow implementation/test slice, dependency and observable acceptance. A retain/no-change decision still needs evidence and limitations. Do not add a framework or skill when an existing contract or deterministic validator suffices.

A review is complete when all in-scope components have records, findings and evidence gaps are explicit, the minimal plan is reviewable, and an independent reviewer checks coverage and unsupported claims. Completion may conclude that updates or runtime verification are needed. It never silently changes maturity. Implement any accepted behavior change on its own scoped branch/PR, with frozen regression criteria and separate explicit merge/release authorization.

Use the existing lifecycle and readiness validators for promotion. Known high-severity failures block promotion; historical summaries and owner archival decisions are not new runtime PASS receipts. Keep production publication separate from Done, and preserve source, package, manifest and deployed identities independently.
