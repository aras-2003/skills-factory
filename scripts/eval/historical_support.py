"""Validate archived administrative inputs without rewriting historical campaigns.

Only this explicit support allowlist is historical. Runtime, fixtures, rubrics,
receipts and component sources remain bound to the live candidate by campaign.py.
Explicit revision calls retain the pre-adoption anchor as a compatibility default.
Campaign calls use the immutable commit recording the administrative manifest.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import yaml

ANCHOR = "ebb9a8d00780cc7116bf94a21a6f0c18ee8264e0"
SUPPORT_PATHS = frozenset({
    "release/production-readiness.yaml", "CATALOG.md", "docs/catalog.json",
    "scripts/eval/campaign.py",
})


def matches_support_pin(root: Path, path: str, expected: str, revision: str = ANCHOR,
                        manifest_path: str | None = None) -> bool:
    """Verify an archived support pin against the immutable commit that recorded it."""
    if path not in SUPPORT_PATHS or not re.fullmatch(r"[0-9a-f]{40}", revision):
        return False
    try:
        if manifest_path is not None:
            if manifest_path not in {
                "evals/campaigns/iteration-07-investing-quality-2026-11/campaign.yaml",
                "evals/campaigns/iteration-08-investing-monitoring-2026-11/campaign.yaml",
            }:
                return False
            # Administrative pins were reconciled after runtime execution. Their
            # provenance is the commit recording the manifest, not the runtime SHA.
            recorded = subprocess.run(
                ["git", "-C", str(root), "log", "-1", "--format=%H", "HEAD", "--", manifest_path],
                capture_output=True, check=False, timeout=15,
            )
            revision = recorded.stdout.decode().strip()
            if recorded.returncode or not re.fullmatch(r"[0-9a-f]{40}", revision):
                return False
            manifest = subprocess.run(
                ["git", "-C", str(root), "show", f"{revision}:{manifest_path}"],
                capture_output=True, check=False, timeout=15,
            )
            if manifest.returncode:
                return False
            data = yaml.safe_load(manifest.stdout) or {}
            if data.get("source_sha256", {}).get(path) != expected:
                return False
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{revision}:{path}"],
            capture_output=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError, yaml.YAMLError, AttributeError):
        return False
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected
