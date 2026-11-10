# Isolated Marp adapter

This adapter consumes canonical DeckSpec v1 and emits Marp CLI 4.5.1 output. It is deliberately not registered in Lab, Site, the runtime registry, or a production package. Its CLI requires the output mode explicitly:

```sh
node src/adapter.js render --input fixtures/canonical-deck-v1.json --output-dir .tmp/render --mode html
```

Supported modes are `html`, `pdf`, `pptx_flattened`, and `pptx_editable_experimental`. Standard Marp PPTX is image backed and supports presenter notes. Experimental editable output requires LibreOffice Impress and must be inspected for native objects; fidelity can be lower, complex CSS may be incomplete, and presenter notes are not supported. There is no fallback between modes.

## Runtime and security

The renderer image starts from Marp CLI 4.5.1 pinned by OCI digest. Debian packages come from snapshot `20261109T000000Z`; LibreOffice Impress is pinned to Debian `4:7.4.7-1+deb12u14`, Tesseract to `5.3.0-2`, and Python to `3.11.2-1+b1`. The runner uses Node `22.23.3`; the OCI image fixes the internal Node and Chromium versions. Preflight records exact Marp and Node versions, Chromium path/version/binary SHA-256, LibreOffice version/package version and Docker image ID. It refuses a missing or mismatched runtime for the requested mode.

HTML generation does not require a browser; PDF and either PPTX mode do. The CI screenshot/reopen workflow uses Chromium for HTML inspection. Rendering uses Docker with outbound networking disabled, a read-only root filesystem, unprivileged UID, no Linux capabilities, no-new-privileges, CPU/memory/process/file-size limits, a temporary filesystem, read-only input, writable output and a 120 second process timeout. Deck input is limited to 5 MiB/50 slides; local assets are limited to 50 files, 2 MiB each and 10 MiB total; charts are limited to eight data points; output is limited to 100 MiB. The canonical schema/semantic validator runs before conversion. Diagnostics are bounded and redact filesystem paths.

Only the bundled `sf-editorial` theme is supported. Local asset manifest paths must be normalized relative paths to regular files within the input root; remote paths, symlinks, traversal, active SVG and oversized/unrecognized content are blocked. SVG is restricted to passive geometry/text elements and attributes. Data charts are rendered as deterministic local SVG from finite canonical numeric references. Text is escaped as plain Markdown text; unsupported exhibit types stop conversion.

## Acceptance evidence

The CI job generates four output modes from the same three-slide synthetic 16:9 fixture. It reopens HTML in pinned Chromium, PDF in Poppler, and both PPTX variants in LibreOffice Impress. It checks page count, slide ID/order in receipts, aspect ratio, text/data/units/provenance, native shapes, flattened slide images, presenter notes and their expected loss in experimental mode. It runs Tesseract OCR on LibreOffice-reopened PPTX pages to inspect visible slide content. A second HTML render must yield identical per-slide PNG SHA-256. Cross-format normalized mean absolute error is capped at 0.20 after resizing to 1280×720; the per-slide measurements are archived. `fc-match` records which installed font resolves a deliberately missing font.

The synthetic fixture contains no customer or production information. A green adapter CI run proves this renderer increment only. It does not prove the native Figma Slides/client acceptance still required by parent issue #283.
