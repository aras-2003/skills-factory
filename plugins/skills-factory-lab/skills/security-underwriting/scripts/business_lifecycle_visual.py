"""Standalone, accessible SVG lifecycle graphic from classifier output.

No plotting dependency; keeps the five phases visible even when classification fails.
"""
from __future__ import annotations

from html import escape
from math import isfinite

PHASES = (
    ("startup", "Startup"),
    ("hyper_growth", "Hyper Growth"),
    ("operating_leverage", "Operating Leverage"),
    ("capital_return", "Capital Return"),
    ("decline", "Decline"),
)
COLORS = ("#B8C4D4", "#CE9E54", "#3D8F7B", "#5685B4", "#C47777")


def render_lifecycle_svg(result: dict, *, company: str = "Company") -> str:
    """Return SVG string. Scores are affinities, never statistical probabilities."""
    name = escape(company[:90], quote=True)
    status = result.get("status")
    active = result.get("phase") if status == "CLASSIFIED" else None
    affinities = result.get("phase_affinity_pct", {}) if active else {}
    if active and (active not in dict(PHASES) or not isinstance(affinities, dict)):
        raise ValueError("Invalid classifier output")
    width, height = 960, 325
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-labelledby="title description">',
        f'<title id="title">Business lifecycle: {name}</title>',
        '<desc id="description">Five-stage lifecycle indicator with heuristic affinity bars. Scores are not calibrated probabilities. Missing data prevent phase selection.</desc>',
        '<rect width="960" height="325" rx="18" fill="#111A29"/>',
        f'<text x="30" y="43" fill="#F8FAFC" font-size="21" font-family="Arial,sans-serif">Business lifecycle · {name}</text>',
        '<text x="30" y="69" fill="#BAC6D7" font-size="13" font-family="Arial,sans-serif">Phase affinity · heuristic, NOT probability</text>',
    ]
    for i, ((key, label), color) in enumerate(zip(PHASES, COLORS)):
        x = 30 + 186 * i
        is_active = key == active
        parts.append(f'<rect x="{x}" y="91" width="178" height="69" rx="10" fill="{color if is_active else "#263348"}" stroke="{color}" stroke-width="{3 if is_active else 1}"/>')
        parts.append(f'<text x="{x+12}" y="119" fill="#FFFFFF" font-size="14" font-family="Arial,sans-serif">{i+1}. {escape(label)}</text>')
        parts.append(f'<text x="{x+12}" y="142" fill="#FFFFFF" font-size="12" font-family="Arial,sans-serif">{"CURRENT PHASE" if is_active else " "}</text>')
        raw = affinities.get(key, 0)
        if not isinstance(raw, (float, int)) or not isfinite(raw) or not 0 <= raw <= 100:
            raise ValueError("Invalid affinity value")
        value = float(raw) if active else 0
        parts.append(f'<rect x="{x}" y="186" width="178" height="11" rx="5" fill="#344358"/>')
        if value:
            parts.append(f'<rect x="{x}" y="186" width="{178*value/100:.2f}" height="11" rx="5" fill="{color}"/>')
        label_value = f"{value:.1f}% affinity" if active else "N/A"
        parts.append(f'<text x="{x}" y="219" fill="#D6E1ED" font-size="13" font-family="Arial,sans-serif">{label_value}</text>')
    if active:
        metrics = result.get("metrics") or {}
        growth = metrics.get("revenue_growth")
        margin = metrics.get("operating_margin")
        detail = (f"Revenue growth: {growth*100:.1f}%  |  Operating margin: {margin*100:.1f}%"
                  if isinstance(growth, (float, int)) and isinstance(margin, (float, int))
                  and isfinite(growth) and isfinite(margin) else "Metrics unavailable")
        detail = escape(detail)
        gaps = result.get("data_gaps", [])
        footer = "Missing data: " + ", ".join(escape(str(v)) for v in gaps) if gaps else "All optional KPI inputs present"
    else:
        detail = f"NOT CLASSIFIED · {escape(str(status or 'INVALID_DATA'))}"
        footer = "Insufficient or unverified financial information; no phase chosen."
    parts.append(f'<text x="30" y="262" fill="#F8FAFC" font-size="15" font-family="Arial,sans-serif">{detail}</text>')
    parts.append(f'<text x="30" y="288" fill="#BAC6D7" font-size="13" font-family="Arial,sans-serif">{footer}</text>')
    parts.append('</svg>')
    return "".join(parts)
