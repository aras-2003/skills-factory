# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp==2.3.0",
#   "matplotlib==3.11.2",
# ]
# ///

from __future__ import annotations

import math
from hashlib import sha256
from io import BytesIO
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mcp.server import MCPServer
from mcp.server.mcpserver import Image
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer(
    "Arek deterministic chart renderer",
    instructions=(
        "Render factual quantitative charts from explicit numeric inputs. "
        "Never infer missing values. Preserve labels, order and units."
    ),
)


def _validate_text(value: str, field: str, maximum: int, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str) or (not allow_empty and not value.strip()) or len(value) > maximum:
        raise ToolError(f"{field} must be a string of at most {maximum} characters")


def _validate_parallel(labels: Sequence[str], values: Sequence[float], expected_points: int, title: str, unit: str) -> None:
    if not labels or not values:
        raise ToolError("labels and values must be non-empty")
    if len(labels) != len(values):
        raise ToolError("labels and values must have equal length")
    if len(labels) > 60:
        raise ToolError("maximum 60 data points per chart")
    if expected_points != len(labels) or expected_points != len(values):
        raise ToolError("received chart data length does not match expected_points; refusing partial render")
    for label in labels:
        _validate_text(label, "labels", 80)
    _validate_text(title, "title", 160)
    _validate_text(unit, "unit", 30, allow_empty=True)
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or abs(value) > 1e12
        for value in values
    ):
        raise ToolError("values must contain only finite numbers between -1e12 and 1e12")


def _png(fig) -> list[str | Image]:
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=160,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="white",
    )
    width_px, height_px = fig.canvas.get_width_height()
    plt.close(fig)

    payload = buffer.getvalue()
    digest = sha256(payload).hexdigest()
    receipt = (
        "CHART_PAYLOAD_OK "
        f"mime=image/png bytes={len(payload)} sha256={digest} "
        f"canvas_px={width_px}x{height_px}"
    )
    return [receipt, Image(data=payload, format="png")]


@mcp.tool()
def render_bar_chart(
    labels: list[str],
    values: list[float],
    expected_points: int,
    title: str,
    unit: str,
    horizontal: bool,
) -> list[str | Image]:
    """Render a deterministic factual bar chart from explicit labels and numeric values."""
    _validate_parallel(labels, values, expected_points, title, unit)

    width = 8.0
    height = max(3.2, min(10.0, 0.42 * len(labels) + 1.8))
    fig, ax = plt.subplots(figsize=(width, height))

    if horizontal:
        positions = list(range(len(labels)))
        ax.barh(positions, values)
        ax.set_yticks(positions, labels=labels)
        ax.invert_yaxis()
        ax.set_xlabel(unit)
        for idx, value in enumerate(values):
            ax.text(value, idx, f" {value:g}{(' ' + unit) if unit else ''}", va="center")
    else:
        positions = list(range(len(labels)))
        ax.bar(positions, values)
        ax.set_xticks(positions, labels=labels, rotation=35, ha="right")
        ax.set_ylabel(unit)
        for idx, value in enumerate(values):
            ax.text(idx, value, f"{value:g}{(' ' + unit) if unit else ''}", ha="center", va="bottom")

    if title:
        ax.set_title(title)
    ax.grid(axis="x" if horizontal else "y", alpha=0.2)
    fig.tight_layout()
    return _png(fig)


@mcp.tool()
def render_line_chart(
    x_labels: list[str],
    series_names: list[str],
    series_values: list[list[float]],
    expected_x_labels: int,
    expected_series: int,
    expected_points_per_series: int,
    title: str,
    unit: str,
) -> list[str | Image]:
    """Render a deterministic factual line chart from explicit x labels and one or more numeric series."""
    if not x_labels:
        raise ToolError("x_labels must be non-empty")
    if len(x_labels) < 2:
        raise ToolError("x_labels must contain at least two points")
    if not series_names or not series_values:
        raise ToolError("series_names and series_values must be non-empty")
    if len(series_names) != len(series_values):
        raise ToolError("series_names and series_values must have equal length")
    if len(x_labels) > 100:
        raise ToolError("maximum 100 x-axis points per chart")
    if len(series_names) > 8:
        raise ToolError("maximum 8 series per chart")
    if len(x_labels) != expected_x_labels or len(series_names) != expected_series or len(series_values) != expected_series:
        raise ToolError("received chart data shape does not match expected counts; refusing partial render")
    for label in (*x_labels, *series_names):
        _validate_text(label, "chart labels", 80)
    _validate_text(title, "title", 160)
    _validate_text(unit, "unit", 30, allow_empty=True)
    for values in series_values:
        if len(values) < 2:
            raise ToolError("each series must contain at least two points")
        if len(values) != len(x_labels):
            raise ToolError("every series must match x_labels length")
        if len(values) != expected_points_per_series:
            raise ToolError("received chart data length does not match expected_points_per_series; refusing partial render")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > 1e12
            for value in values
        ):
            raise ToolError("series_values must contain only finite numbers between -1e12 and 1e12")

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = list(range(len(x_labels)))
    for name, values in zip(series_names, series_values):
        ax.plot(x, values, marker="o" if len(x_labels) <= 24 else None, label=name)

    step = max(1, len(x_labels) // 12)
    ticks = list(range(0, len(x_labels), step))
    if ticks[-1] != len(x_labels) - 1:
        ticks.append(len(x_labels) - 1)
    ax.set_xticks(ticks, labels=[x_labels[i] for i in ticks], rotation=35, ha="right")
    ax.set_ylabel(unit)
    if title:
        ax.set_title(title)
    if len(series_names) > 1:
        ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return _png(fig)


if __name__ == "__main__":
    mcp.run()
