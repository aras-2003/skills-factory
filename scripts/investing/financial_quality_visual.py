"""Dependency-free SVG chart for verified multi-year financial quality trends.

The chart is descriptive, not a sector-normalized rating or forecast.
"""
from __future__ import annotations

from html import escape
from math import isfinite

SERIES = (
    ("gross_margin", "Gross margin", "#55b6a5"),
    ("operating_margin", "Operating margin", "#82a9f6"),
    ("net_margin", "Net margin", "#e2b66c"),
    ("fcf_margin", "FCF margin", "#d595b0"),
)


def render_quality_trends_svg(observations: list[dict], *, company: str = "Company") -> str:
    """Accept chronological dictionaries with period and metrics, render available margins."""
    if len(observations) < 3:
        raise ValueError("At least three periods required for a multi-year chart")
    periods = [str(item["period"]) for item in observations]
    if len(set(periods)) != len(periods):
        raise ValueError("Duplicate periods")
    width, height = 940, 420
    plot_x, plot_y, plot_w, plot_h = 80, 112, 780, 215
    valid: list[tuple[int, str, str, list[float | None]]] = []
    all_values = [0.]
    for key, label, color in SERIES:
        row = []
        for item in observations:
            value = (item.get("metrics") or {}).get(key)
            if value is not None and (not isinstance(value, (int, float)) or not isfinite(value)):
                raise ValueError("Nonfinite metric")
            row.append(float(value) * 100 if value is not None else None)
        if any(v is not None for v in row):
            valid.append((len(valid), label, color, row))
            all_values.extend(v for v in row if v is not None)
    minimum, maximum = min(all_values), max(all_values)
    if minimum == maximum:
        minimum -= 1
        maximum += 1
    spread = maximum - minimum
    minimum -= spread * 0.10
    maximum += spread * 0.10

    def pos_x(i: int) -> float:
        return plot_x + i * plot_w / (len(periods) - 1)

    def pos_y(v: float) -> float:
        return plot_y + (maximum - v) / (maximum - minimum) * plot_h

    name = escape(company[:80])
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<title id="t">Historical financial quality margins: {name}</title>',
        '<desc id="d">Gross, operating, net and free cash flow margins by reporting period. '
        'Missing metrics are not connected, and no arbitrary thresholds or score are applied.</desc>',
        '<rect width="940" height="420" fill="#111A29" rx="16"/>',
        f'<text x="32" y="39" fill="white" font-size="22" font-family="Arial">{name} · Financial quality trends</text>',
        '<text x="32" y="65" fill="#B8C9DB" font-size="13" font-family="Arial">Comparable verified annual/TTM observations · % of revenue · no universal thresholds</text>',
    ]
    for i in range(5):
        v = minimum + (maximum - minimum) * i / 4
        y = pos_y(v)
        out.append(f'<line x1="{plot_x}" x2="{plot_x+plot_w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#35465A"/>')
        out.append(f'<text x="14" y="{y+4:.1f}" fill="#CCD5E2" font-size="12">{v:.1f}%</text>')
    for i, period in enumerate(periods):
        out.append(f'<text x="{pos_x(i):.1f}" y="351" fill="#CCD5E2" font-size="12" text-anchor="middle">{escape(period)}</text>')
    for _, label, color, row in valid:
        points = []
        for i, value in enumerate(row):
            if value is None:
                if len(points) > 1:
                    out.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>')
                points = []
                continue
            x, y = pos_x(i), pos_y(value)
            points.append(f"{x:.1f},{y:.1f}")
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.8" fill="{color}"/>')
        if len(points) > 1:
            out.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>')
    for i, (key, label, color) in enumerate(SERIES):
        out.append(f'<rect x="{45 + (i%2)*445}" y="{372 + (i//2)*19}" width="12" height="9" fill="{color}"/>')
        out.append(f'<text x="{65+(i%2)*445}" y="{381+(i//2)*19}" fill="#CCD5E2" font-size="12">{escape(label)}{" (no data)" if key not in {x[0] for x in []} and not any((item.get("metrics") or {}).get(key) is not None for item in observations) else ""}</text>')
    out.append("</svg>")
    return "".join(out)
