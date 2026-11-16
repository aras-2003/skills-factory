"""Validate archived administrative inputs without rewriting historical campaigns.

Only this explicit support allowlist is historical. Runtime, fixtures, rubrics,
receipts and component sources remain bound to the live candidate by campaign.py.
The anchor is the last reviewed integration baseline before SDLC adoption.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess

ANCHOR = "ebb9a8d00780cc7116bf94a21a6f0c18ee8264e0"
SUPPORT_PATHS = frozenset({
    "release/production-readiness.yaml", "CATALOG.md", "docs/catalog.json",
    "scripts/eval/campaign.py",
})


def matches_support_pin(root: Path, path: str, expected: str, revision: str = ANCHOR) -> bool:
    """Verify an archived support pin against the immutable commit that recorded it."""
    if path not in SUPPORT_PATHS or not re.fullmatch(r"[0-9a-f]{40}", revision):
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{revision}:{path}"],
            capture_output=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected
