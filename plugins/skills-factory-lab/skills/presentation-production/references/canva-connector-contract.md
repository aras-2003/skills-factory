# Canva Presentation Provider — Capability Contract (draft)

## What the connected Canva plugin can actually expose

Provider inspection is per **current conversation/runtime**, not a permanent platform promise. The Canva tool namespace can expose:
- **Read:** `search_designs`, `get_design`, `get_design_pages` (page thumbnails), `get_design_content` (text), `get_presenter_notes`.
- **New presentation:** `create_design` with `format:"Presentation"`, a self-contained brief and optional user-provided/approved `outline.sections[]`. It returns a **generation job**, not a finished deck. The result is real only after its asynchronous completion receipt returns an actual design ID and link; respect per-response polling instructions.
- **Existing-brand designs:** `search_brand_templates`, `create_design_from_brand_template`, or legacy branded generation only when user asks for on-brand assets/template and provider contract permits. `create_design` cannot apply a brand kit directly.
- **Revise:** `start_editing_transaction` → `perform_editing_operations` (draft, uncommitted) → preview with transaction-aware thumbnail(s) → **show user preview and obtain explicit approval** → `commit_editing_transaction`. Without explicit approval, do not commit or call changes saved. The operation set includes text replacement/formatting, media replace/insert/resize/position, not arbitrary new vector/chart authoring. Do not claim every type of graph is editable.
- **Page composition:** `merge_designs` can combine/reorder/delete pages **only with explicit approval of the exact page operations**, independently of the general request for a deck.

## Why account connection is not export proof

`search_designs` returning user-account design metadata proves a read access channel. It does **not** establish `create_design` success, per-slide editability, animation, PDF/PPTX export or client visibility.

The Canva connector tools available at the design checkpoint **do not expose a direct `export PPTX` operation**. Treat this state as `PPTX_EXPORT=UNAVAILABLE_OR_UNKNOWN` until a *documented, actually callable* export action or other user-authorized verified mechanism is identified. Official product availability or Canva editor's own Download menu does not satisfy API/tool capability. Do not silently claim presentation-to-PPTX roundtrip; return native Canva URL plus a truthful missing-export note or a verified alternate export path.

Do not use generated images to encode factual chart series. Canva may generate a native design using supplied descriptions, but do not infer accurate chart values, source mapping, native object editability or brand fidelity without inspecting actual pages and comparing against evidence ledger. For quantitative exhibits, prefer validated numeric renderer and appropriately embedded/native chart action if actually callable.

## Receipt fields and status boundaries

`CanvaCapabilityPreflight{read_designs,create_design,inspect_pages,edit_elements,commit_requires_user_preview_approval,brand_kit,generate_job_polling,pptx_export,pdf_export,notes,asset_import,privacy_permissions}` with per-capability status `AVAILABLE|UNAVAILABLE|UNKNOWN` and `tool_name + observed_or_schema_only`.

`CanvaDeckReceipt{generation_job_id?,job_completed,design_id?,url?,slide_thumbnail_receipts[],content_inspection_receipts[],edit_transactions[],user_approvals[],native_editability_per_exhibit[],export_path?,export_receipts[],roundtrip_receipts[],unverified_features[]}`.

**State discipline:**
- `PLUGIN_READ_OBSERVED` ≠ `NATIVE_DESIGN_CREATED`.
- `NATIVE_DESIGN_CREATED` ≠ `PAGE_QA_APPROVED`.
- `DRAFT_TRANSACTION_PREVIEWED` ≠ `REVISION_COMMITTED`.
- `NATIVE_DESIGN_CREATED` ≠ `PPTX_EXPORTED` ≠ `PPTX_ROUNDTRIP_CHECKED`.
- No client-display PASS without an independent client rendering observation.

The user may want a deck **without** PPTX export; deliver native Canva link with truthful limitations if this meets their explicit output request. If PPTX is essential, the capability is a release blocker for that output until verified.
