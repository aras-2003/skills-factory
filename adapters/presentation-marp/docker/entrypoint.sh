#!/bin/sh
set -eu
mode=${2:-}
if [ "${1:-}" = sf-preflight ]; then
  marp_output=$(node /home/marp/.cli/marp-cli.js --version 2>&1)
  marp_version=$(printf '%s' "$marp_output" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true)
  node_version=$(node --version | sed 's/^v//')
  browser_version=''; if [ -x "$CHROME_PATH" ]; then browser_version=$($CHROME_PATH --version | sed 's/^[^ ]* //'); fi
  browser_sha256=''; if [ -n "$browser_version" ]; then browser_sha256=$(sha256sum "$CHROME_PATH" | cut -d' ' -f1); fi
  lo_version=''
  lo_package=''
  if command -v dpkg-query >/dev/null 2>&1 && command -v libreoffice >/dev/null 2>&1; then lo_package=$(dpkg-query -W -f='${Version}' libreoffice-impress 2>/dev/null || true); fi
  if command -v libreoffice >/dev/null 2>&1; then lo_version=$(libreoffice --headless --version | sed 's/^LibreOffice //'); fi
  printf '{"marp":"%s","node":"%s","browser":"%s","browser_path":"%s","browser_sha256":"%s","libreoffice":"%s","libreoffice_package":"%s","image":"ghcr.io/marp-team/marp-cli:v4.5.1@sha256:3cf660df7b9737f875e57f7169dff0b08d1d3ab604ea2d655ab761102942fa42"}\n' "$marp_version" "$node_version" "$browser_version" "$CHROME_PATH" "$browser_sha256" "$lo_version" "$lo_package"
  exit 0
fi
case "${1:-}" in
  sf-inspect-html) exec node /usr/local/bin/sf-inspect-html.cjs "$2" "$3" "$4" ;;
  sf-inspect-pptx) exec python3 /usr/local/bin/sf-inspect-pptx "$2" "$3" ;;
  sf-inspect-pdf) exec python3 /usr/local/bin/sf-inspect-pdf.py "$2" "$3" "$4" "${5:-text}" ;;
  sf-reopen-pptx) exec /usr/local/bin/sf-reopen-pptx.sh "$@" ;;
  sf-compare-images) exec python3 /usr/local/bin/sf-compare-images.py "$2" "$3" "$4" "$5" ;;
  sf-font-fallback) exec /usr/local/bin/sf-font-fallback.sh "$@" ;;
esac
if [ "${1:-}" != sf-render ] || [ -z "$mode" ]; then echo 'invalid renderer command' >&2; exit 2; fi
cd /work/input
case "$mode" in
  html) node /home/marp/.cli/marp-cli.js deck.md --theme-set ./sf-editorial.css --output /work/output/deck.html ;;
  pdf) node /home/marp/.cli/marp-cli.js deck.md --theme-set ./sf-editorial.css --output /work/output/deck.html || { echo SF_PDF_STAGE:html_generation >&2; exit 1; }; find /work/input -maxdepth 1 -type f ! -name 'deck.md' ! -name 'deck.json' ! -name 'sf-editorial.css' -exec cp {} /work/output/ + || { echo SF_PDF_STAGE:asset_copy >&2; exit 1; }; slide_count=$(node -p "require('./deck.json').slides.length") || { echo SF_PDF_STAGE:slide_count >&2; exit 1; }; node /usr/local/bin/sf-render-pdf.cjs /work/output/deck.html /work/output/deck.pdf "$slide_count" ;;
  pptx_flattened) node /home/marp/.cli/marp-cli.js deck.md --browser-timeout 90 --pptx --theme-set ./sf-editorial.css --allow-local-files --output /work/output/deck.pptx ;;
  pptx_editable_experimental)
    command -v libreoffice >/dev/null 2>&1 || { echo 'BLOCKED_MISSING_RUNTIME: LibreOffice Impress is required' >&2; exit 30; }
    node /home/marp/.cli/marp-cli.js deck.md --pptx --pptx-editable --theme-set ./sf-editorial.css --allow-local-files --output /work/output/deck-editable.pptx ;;
  *) echo 'invalid output mode' >&2; exit 2 ;;
esac
