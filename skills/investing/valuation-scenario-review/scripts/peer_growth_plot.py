"""Static PEG reference scatter rendered only from a peer comparison snapshot."""
from __future__ import annotations

from pathlib import Path


def render_peer_growth_plot(comparison: dict, output_path: str | Path) -> dict:
    """Render compatible peer/target points without fetching or transforming source data."""
    plot = comparison.get("plot", {})
    points = plot.get("points", [])
    if comparison.get("status") != "COMPARABLE" or not points or plot.get("same_input_as_table") is not True:
        return {"status": "BLOCKED_NO_COMPATIBLE_POINTS", "snapshot_id": plot.get("snapshot_id")}
    if not plot.get("snapshot_id") or not plot.get("as_of") or not plot.get("filter"):
        return {"status": "BLOCKED_INCOMPLETE_PROVENANCE", "snapshot_id": plot.get("snapshot_id")}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"status": "BLOCKED_RENDERER_UNAVAILABLE", "snapshot_id": plot.get("snapshot_id")}

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    growths = [float(point["eps_growth_pct"]) for point in points]
    max_growth = max(growths)
    for point in points:
        x = float(point["eps_growth_pct"])
        y = float(point["forward_pe"])
        color = "#b42318" if point.get("role") == "TARGET" else "#175cd3"
        ax.scatter(x, y, color=color, s=70, zorder=3)
        ax.annotate(point["ticker"], (x, y), xytext=(5, 5), textcoords="offset points")
    # PEG = 1 is P/E = EPS growth percentage points; keep its range within the plot.
    upper = max(max_growth, max(float(point["forward_pe"]) for point in points))
    ax.plot([0, upper], [0, upper], linestyle="--", color="#667085", label="PEG = 1 reference")
    ax.set(xlabel="Forecast EPS CAGR (%)", ylabel="Forward P/E (x)",
           title=f"Peer snapshot {plot['as_of']} · {plot['filter']['industry']}")
    ax.grid(alpha=0.2)
    ax.legend(loc="best")
    fig.savefig(destination, dpi=150)
    plt.close(fig)
    return {"status": "RENDERED_STATIC", "path": str(destination), "snapshot_id": plot["snapshot_id"],
            "as_of": plot["as_of"], "filter": plot["filter"],
            "source_count": len(points), "source_urls": sorted({
                point[key] for point in points for key in ("eps_growth_source_url", "forward_pe_source_url")
            })}
