"""Validate archived administrative inputs without rewriting historical campaigns.

Only this explicit support allowlist is historical. Runtime, fixtures, rubrics,
receipts and component sources remain bound to the live candidate by campaign.py.
The anchor is the last reviewed integration baseline before SDLC adoption.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

ANCHOR = "ebb9a8d00780cc7116bf94a21a6f0c18ee8264e0"
SUPPORT_PATHS = frozenset({
    "release/production-readiness.yaml", "CATALOG.md", "docs/catalog.json",
    "scripts/eval/campaign.py",
})


def matches_support_pin(root: Path, path: str, expected: str) -> bool:
    """Fail closed if the archived object is absent or the supplied pin is wrong."""
    if path not in SUPPORT_PATHS:
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{ANCHOR}:{path}"],
            capture_output=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected
