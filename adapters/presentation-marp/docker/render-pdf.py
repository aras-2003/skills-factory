#!/usr/bin/env python3
"""Render pinned Marp HTML to searchable, 16:9 PDF without Chromium printToPDF."""
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from weasyprint import CSS, HTML, default_url_fetcher


def main():
    if len(sys.argv) != 4:
        raise SystemExit(2)
    source = Path(sys.argv[1]).resolve()
    destination = Path(sys.argv[2]).resolve()
    asset_root = Path(sys.argv[3]).resolve()
    if not source.is_file() or not asset_root.is_dir():
        raise SystemExit(2)

    def fetch_local(url):
        parsed = urlparse(url)
        if parsed.scheme == "data":
            return default_url_fetcher(url)
        if parsed.scheme != "file":
            raise ValueError("non-local resource blocked")
        candidate = Path(unquote(parsed.path)).resolve()
        if not candidate.is_relative_to(asset_root):
            raise ValueError("resource outside staged input blocked")
        return default_url_fetcher(url)

    layout = CSS(string="""
        @page { size: 1280px 720px; margin: 0; }
        html, body { margin: 0 !important; padding: 0 !important; }
        section {
          box-sizing: border-box !important;
          width: 1280px !important;
          height: 720px !important;
          margin: 0 !important;
          break-after: page !important;
          page-break-after: always !important;
        }
        section:last-of-type {
          break-after: auto !important;
          page-break-after: auto !important;
        }
    """)
    try:
        HTML(filename=str(source), base_url=asset_root.as_uri() + "/", url_fetcher=fetch_local).write_pdf(
            target=str(destination), stylesheets=[layout]
        )
    except Exception:
        print("SF_PDF_RENDER_FAILED:weasyprint", file=sys.stderr)
        raise SystemExit(1)
    if not destination.is_file() or destination.stat().st_size == 0:
        print("SF_PDF_RENDER_FAILED:empty_output", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
