# ARC-05 — OAF source-derived architecture explorer

Issue #378; parent #373. Uses the shared canonical IR and ARC-03 isolated renderer.

## Scope and evidence

The PoC reads only the nested entries in `evals/oaf/wave4/case-capability-map-001.md`. That file is a synthetic evaluation fixture, not an organization's verified enterprise architecture repository. Explicitly identified entries are typed as owner, process or application; other entries remain map capabilities because the source presents them inside a capability-map extract. Every observed node and containment edge cites its exact source line and commit.

The explorer does not infer application-to-data or application-to-owner relationships. Incomplete ownership is shown with unresolved edges; the absent data-lineage layer and absent TO-BE model are called out in the summary. Impact traversal follows evidenced containment edges only. This is a fixture-backed PoC, not native ArchiMate or a complete EA repository.

## Validation

- Unit tests exercise exact Git provenance, typed entities, semantic containment, unknown links, impact traversal and source/schema failure cases.
- CI runs the sample through the pinned ARC-03 sandbox renderer and browser-check, then archives the canonical model, summary and renderer receipts.
- No production organization data or private portfolio context is used. Runtime remains `NOT_RUN`.
