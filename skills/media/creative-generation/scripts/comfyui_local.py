#!/usr/bin/env python3
"""Small, loopback-only ComfyUI API client for trusted user-supplied workflows.

This adapter never installs models or nodes, reads cloud credentials, or contacts
non-loopback hosts. A ComfyUI workflow/custom node is executable code; callers
must review and trust it before queueing it.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

DEFAULT_BASE_URL = "http://127.0.0.1:8188"
REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_JOB_TIMEOUT_SECONDS = 900
DEFAULT_MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024


class AdapterError(RuntimeError):
    """A bounded, user-actionable ComfyUI adapter error."""


class _LoopbackOnlyRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_base_url(base_url: str) -> str:
    """Accept only plain HTTP to an IP literal that is explicitly loopback."""
    try:
        parsed = urlsplit(base_url)
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port or 8188
    except (ValueError, TypeError) as exc:
        raise AdapterError("ComfyUI URL must use a loopback IP literal, e.g. http://127.0.0.1:8188") from exc

    if parsed.scheme != "http" or not address.is_loopback:
        raise AdapterError("Only plain HTTP to 127.0.0.0/8 or ::1 is allowed")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AdapterError("ComfyUI URL must not contain credentials, query parameters, or a fragment")
    if parsed.path not in ("", "/"):
        raise AdapterError("ComfyUI URL must be an origin without a path prefix")
    if not 1 <= port <= 65535:
        raise AdapterError("ComfyUI port must be between 1 and 65535")

    host = f"[{address.compressed}]" if address.version == 6 else address.compressed
    return f"http://{host}:{port}"


def _opener():
    # Ignore proxy environment variables and block redirects to non-loopback hosts.
    return build_opener(ProxyHandler({}), _LoopbackOnlyRedirectHandler())


def _json_request(base_url: str, path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> Any:
    url = f"{validate_base_url(base_url)}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with _opener().open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        exc.close()
        raise AdapterError(f"ComfyUI returned HTTP {exc.code} for {path}") from exc
    except URLError as exc:
        raise AdapterError(f"Cannot reach local ComfyUI at {validate_base_url(base_url)}: {exc.reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"ComfyUI returned invalid JSON for {path}") from exc


def load_workflow(path: Path) -> dict[str, Any]:
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Cannot read workflow JSON: {path}") from exc
    if not isinstance(workflow, dict) or not workflow:
        raise AdapterError("Workflow must be a non-empty ComfyUI API prompt object")
    return workflow


def _output_descriptors(value: Any):
    if isinstance(value, dict):
        filename = value.get("filename")
        if isinstance(filename, str) and filename:
            yield value
            return
        for child in value.values():
            yield from _output_descriptors(child)
    elif isinstance(value, list):
        for child in value:
            yield from _output_descriptors(child)


def _history_entry(history: Any, prompt_id: str) -> dict[str, Any] | None:
    if not isinstance(history, dict):
        raise AdapterError("ComfyUI history response was not an object")
    entry = history.get(prompt_id)
    if entry is None and len(history) == 1:
        entry = next(iter(history.values()))
    if entry is None:
        return None
    if not isinstance(entry, dict):
        raise AdapterError("ComfyUI history entry was not an object")
    return entry


def _safe_parts(descriptor: dict[str, Any]) -> tuple[str, str, str]:
    filename = descriptor.get("filename")
    subfolder = descriptor.get("subfolder", "")
    file_type = descriptor.get("type", "output")
    if not isinstance(filename, str) or not filename or filename in {".", ".."}:
        raise AdapterError("ComfyUI returned an invalid output filename")
    if "/" in filename or "\\" in filename or "\x00" in filename:
        raise AdapterError("ComfyUI output filename must not contain path separators")
    if not isinstance(subfolder, str) or "\\" in subfolder or "\x00" in subfolder:
        raise AdapterError("ComfyUI returned an invalid output subfolder")
    path = PurePosixPath(subfolder)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        if subfolder != "":
            raise AdapterError("ComfyUI output subfolder must remain relative")
    if not isinstance(file_type, str) or file_type not in {"output", "temp"}:
        raise AdapterError("ComfyUI returned an unsupported output file type")
    return filename, "" if subfolder == "." else subfolder, file_type


def _unique_target(output_root: Path, descriptor: dict[str, Any], node_id: str) -> Path:
    filename, subfolder, _ = _safe_parts(descriptor)
    safe_node = "".join(ch for ch in str(node_id) if ch.isalnum() or ch in "-_ ").strip() or "output"
    relative = Path(subfolder) / f"{safe_node}-{filename}"
    target = (output_root / relative).resolve()
    if not target.is_relative_to(output_root.resolve()):
        raise AdapterError("ComfyUI output path escapes the selected output directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target
    index = 1
    while candidate.exists():
        candidate = target.with_name(f"{target.stem}-{index}{target.suffix}")
        index += 1
    return candidate


def _download(base_url: str, descriptor: dict[str, Any], target: Path, max_bytes: int) -> Path:
    filename, subfolder, file_type = _safe_parts(descriptor)
    query = urlencode({"filename": filename, "subfolder": subfolder, "type": file_type})
    request = Request(f"{validate_base_url(base_url)}/view?{query}", headers={"Accept": "application/octet-stream"})
    try:
        with _opener().open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response, target.open("xb") as output:
            declared_length = response.headers.get("Content-Length")
            if declared_length and int(declared_length) > max_bytes:
                raise AdapterError(f"ComfyUI output exceeds the {max_bytes}-byte download limit")
            copied = 0
            while chunk := response.read(1024 * 1024):
                copied += len(chunk)
                if copied > max_bytes:
                    raise AdapterError(f"ComfyUI output exceeds the {max_bytes}-byte download limit")
                output.write(chunk)
    except HTTPError as exc:
        exc.close()
        target.unlink(missing_ok=True)
        raise AdapterError(f"ComfyUI could not return output {filename!r} (HTTP {exc.code})") from exc
    except (URLError, OSError, ValueError) as exc:
        target.unlink(missing_ok=True)
        if isinstance(exc, AdapterError):
            raise
        raise AdapterError(f"Could not download local ComfyUI output {filename!r}: {exc}") from exc
    except AdapterError:
        target.unlink(missing_ok=True)
        raise
    return target


def run_workflow(
    base_url: str,
    workflow: dict[str, Any],
    output_dir: Path,
    *,
    timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS,
    poll_interval_seconds: float = 2.0,
    max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
) -> list[Path]:
    base_url = validate_base_url(base_url)
    if timeout_seconds < 1 or poll_interval_seconds <= 0 or max_download_bytes < 1:
        raise AdapterError("Timeout, polling interval, and download limit must be positive")
    if not isinstance(workflow, dict) or not workflow:
        raise AdapterError("Workflow must be a non-empty ComfyUI API prompt object")

    output_root = output_dir.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    queued = _json_request(base_url, "/prompt", method="POST", body={"prompt": workflow})
    prompt_id = queued.get("prompt_id") if isinstance(queued, dict) else None
    if not isinstance(prompt_id, str) or not prompt_id or len(prompt_id) > 200:
        raise AdapterError("ComfyUI did not return a valid prompt_id")

    deadline = time.monotonic() + timeout_seconds
    entry: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        history = _json_request(base_url, f"/history/{quote(prompt_id, safe='')}")
        entry = _history_entry(history, prompt_id)
        if entry is not None:
            status = entry.get("status")
            if isinstance(status, dict) and status.get("status_str") == "error":
                raise AdapterError("ComfyUI workflow failed; inspect the local ComfyUI queue/logs")
            outputs = entry.get("outputs")
            if outputs:
                break
        time.sleep(min(poll_interval_seconds, max(0, deadline - time.monotonic())))
    else:
        raise AdapterError(f"ComfyUI job {prompt_id} did not finish within {timeout_seconds} seconds")

    descriptors = list(_output_descriptors(entry.get("outputs") if entry else None))
    if not descriptors:
        raise AdapterError("ComfyUI job completed without a downloadable image/video output")

    saved: list[Path] = []
    for index, descriptor in enumerate(descriptors):
        node_id = str(descriptor.get("node_id", index + 1))
        target = _unique_target(output_root, descriptor, node_id)
        saved.append(_download(base_url, descriptor, target, max_download_bytes))
    return saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path, help="trusted ComfyUI API workflow JSON")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output-dir", type=Path, default=Path("creative-output"))
    parser.add_argument("--timeout", type=int, default=DEFAULT_JOB_TIMEOUT_SECONDS)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--max-download-mb", type=int, default=2048)
    args = parser.parse_args(argv)

    try:
        outputs = run_workflow(
            args.base_url,
            load_workflow(args.workflow),
            args.output_dir,
            timeout_seconds=args.timeout,
            poll_interval_seconds=args.poll_interval,
            max_download_bytes=args.max_download_mb * 1024 * 1024,
        )
    except AdapterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
