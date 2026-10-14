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


def _validate_text(value: object, field: str, limit: int = 160) -> None:
    if not isinstance(value, str) or len(value) > limit or any(
        ord(c) < 32 and c != "\t" for c in value
    ):
        raise ToolError(f"{field} must be a bounded string without control characters")


def _validate_labels(labels: Sequence[str], name: str, limit: int = 80) -> None:
    if isinstance(labels, (str, bytes)) or not isinstance(labels, (list, tuple)):
        raise ToolError(f"{name} must be a sequence of labels")
    if any(not isinstance(x, str) or not x.strip() for x in labels):
        raise ToolError(f"{name} must have nonempty string labels")
    for label in labels:
        _validate_text(label, name, limit)


def _validate_parallel(labels: Sequence[str], values: Sequence[float]) -> None:
    _validate_labels(labels, "labels")
    if not labels or not isinstance(values, (list, tuple)) or not values:
        raise ToolError("labels and values must be non-empty sequences")
    if len(labels) != len(values):
        raise ToolError("labels and values must have equal length")
    if len(labels) > 60:
        raise ToolError("maximum 60 data points per chart")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or abs(value) > 1_000_000_000_000
        for value in values
    ):
        raise ToolError("values must contain only finite numbers")


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
    title: str = "",
    unit: str = "",
    horizontal: bool = True,
) -> list[str | Image]:
    """Render a deterministic factual bar chart from explicit labels and numeric values."""
    _validate_parallel(labels, values)
    _validate_text(title, "title")
    _validate_text(unit, "unit", 30)

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
    title: str = "",
    unit: str = "",
) -> list[str | Image]:
    """Render a deterministic factual line chart from explicit x labels and one or more numeric series."""
    _validate_labels(x_labels, "x_labels")
    _validate_labels(series_names, "series_names")
    _validate_text(title, "title")
    _validate_text(unit, "unit", 30)
    if len(x_labels) < 2:
        raise ToolError("line charts require at least two x-axis points")
    if not series_names or not isinstance(series_values, (list, tuple)) or not series_values:
        raise ToolError("series_names and series_values must be non-empty")
    if len(series_names) != len(series_values):
        raise ToolError("series_names and series_values must have equal length")
    if len(x_labels) > 100:
        raise ToolError("maximum 100 x-axis points per chart")
    if len(series_names) > 8:
        raise ToolError("maximum 8 series per chart")
    for values in series_values:
        if not isinstance(values, (list, tuple)):
            raise ToolError("series_values must be sequences of numbers")
        if len(values) != len(x_labels):
            raise ToolError("every series must match x_labels length")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > 1_000_000_000_000
            for value in values
        ):
            raise ToolError("series_values must contain only finite numbers")

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
