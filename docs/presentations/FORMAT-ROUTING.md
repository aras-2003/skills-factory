# Presentation format routing contract (PRES-04)

This routing contract selects a delivery path from user intent and observed runtime capabilities. It does not claim that any connected destination exists or that a planned renderer has produced an artifact.

## Separate profile from delivery format

The profile controls story, density and review: `executive`, `technical`, `teaching`, or `interactive_report`. It does not silently select an export format. Preserve an explicit user platform/format choice when the current runtime can satisfy it; otherwise return `BLOCKED_CAPABILITY` and state the available choices.

## Intent and format decision matrix

| User intent / requested output | Preferred route | Conditions and limits |
| --- | --- | --- |
| Interactive report or dashboard | Web/report renderer | Use for interactive controls, filters or live data. Do not turn a report into slides unless the user requests a deck. |
| Native editable presentation | One verified native destination: Figma Slides, Canva, or Google Slides | Choose one primary platform after preflight of the exact create/edit/export actions. Report actual object coverage. Connector presence or read access alone is not create/edit capability. |
| HTML presentation or PDF from canonical DeckSpec | Marp HTML/PDF | Use the pinned adapter/runtime. Report renderer and version. PDF is static; it does not carry presentation interactions. |
| PPTX, editing not required | Marp flattened PPTX | The deck is image-backed; report flattened coverage and the fidelity/notes caveat. Never label it editable. |
| PPTX, native editability required | Native editable PPTX route | Use a verified native authoring/export path. If unavailable, block rather than flatten. |
| PPTX, user explicitly opts into the experimental Marp route | Marp editable PPTX via LibreOffice | Requires the distinct `marp_editable_pptx_libreoffice` capability, compatible browser and Impress preflight. Label EXPERIMENTAL, report observed object coverage and lower-fidelity/unsupported-CSS caveats, and state that presenter notes are not supported. It is an opt-in alternative, never an automatic replacement for native editing. |
| Requested route unavailable or preflight UNKNOWN | No substitution | Return `BLOCKED_CAPABILITY`; do not imply that an alternative was created. Offer verified options and ask only for the choice that changes the route. |

The route applies the strongest constraint first: explicit user format/platform, then required editability, then observed capability, then profile-appropriate design. Profiles change content and craft, not the meaning of “editable”. `PREFERRED` is not proof of editability; it permits a clearly disclosed alternative only when the user accepts it.

## Required preflight

Record each exact operation independently as `AVAILABLE`, `UNAVAILABLE`, or `UNKNOWN`: native create, native edit, requested export, render/reopen, browser, LibreOffice Impress, and any selected web renderer. Include observed version and receipt when available. Never infer create/export from search, read, brand-name presence, or an unrelated tool call. A missing capability stays blocked; do not change the requested mode behind the user's back.

Distinct renderer capabilities are:

- `native_editable_pptx`: verified native authoring/export to PPTX with editable objects.
- `marp_flattened_pptx`: Marp standard PPTX path; image-backed, not editable.
- `marp_editable_pptx_libreoffice`: experimental Marp editable conversion with compatible browser and LibreOffice Impress.

## Output manifest

Every selected route emits a `FormatRouteManifest`, including blocked routes:

```yaml
schema_version: "1"
intent: native_presentation
profile: technical
requested_format: pptx
desired_editability: NATIVE_REQUIRED
route_status: RENDERED # PLANNED | BLOCKED_CAPABILITY | RENDERED | VERIFIED
renderer: native_destination
renderer_version: observed-version-or-null
capabilities:
  native_create: AVAILABLE
  native_pptx_export: AVAILABLE
  object_editability_inspection: UNKNOWN
effective_format: pptx
editable_object_coverage: UNKNOWN # verified object classes or UNKNOWN
fidelity_caveats: []
fallback:
  offered: []
  selected: null
  explicit_user_opt_in: false
receipts: []
```

For Marp flattened output set `editable_object_coverage: NONE_FLATTENED` and state image-backed output and notes behavior in `fidelity_caveats`. For experimental LibreOffice output set the route/capability name explicitly, retain the user's opt-in receipt, and include observed object classes, visual comparison findings, unsupported CSS, and presenter-notes loss. `VERIFIED` requires actual output plus reopen/inspection receipts; it cannot be assigned at planning or export invocation.

The route manifest complements the existing artifact QA receipt. It does not replace DeckSpec, the evidence ledger, renderer receipt, export receipt, round-trip checks, or client-display observation.

## Acceptance examples

The workflow cases in `workflows/presentation-production/tests/cases.yaml` cover:
- executive/technical/teaching profiles and interactive reports as distinct intent/format combinations;
- native-editable PPTX preference over flattened output when `NATIVE_REQUIRED`;
- Marp editable LibreOffice only after explicit opt-in and successful browser/Impress preflight;
- unavailable/unknown capabilities produce BLOCKED without silent downgrade;
- every selected or blocked route carries a manifest with renderer/version, object coverage, caveats and route receipts.

The tests are route-decision fixtures. Runtime evidence is still required before a route can be called rendered or verified.
