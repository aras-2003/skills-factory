"""Privacy-preserving OpenTelemetry spans for Skills Factory MCP calls.

Only hashes and runtime metadata are exported. Prompt text, skill instructions,
tool arguments, tool results, and model reasoning are never span attributes.
Export is opt-in through the standard OTEL_EXPORTER_OTLP_* environment.
"""

from __future__ import annotations

import atexit
import hashlib
import json
import os
import time
from collections.abc import Mapping
from contextlib import contextmanager
from threading import Lock
from typing import Any, Callable, Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

_PROVIDER_LOCK = Lock()


def _sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _exporter_endpoint() -> str | None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
    if endpoint:
        return endpoint
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    return f"{endpoint.rstrip('/')}/v1/traces" if endpoint else None


def _tracer() -> trace.Tracer:
    provider = trace.get_tracer_provider()
    if isinstance(provider, trace.ProxyTracerProvider):
        with _PROVIDER_LOCK:
            provider = trace.get_tracer_provider()
            if isinstance(provider, trace.ProxyTracerProvider):
                resource = Resource.create(
                    {
                        "service.name": os.environ.get("OTEL_SERVICE_NAME", "skills-factory-runtime"),
                        "service.version": os.environ.get("SKILLS_FACTORY_RELEASE_ID", "unknown"),
                        "deployment.environment.name": os.environ.get("SKILLS_FACTORY_ENVIRONMENT", "local"),
                        "skills_factory.source_revision": os.environ.get("SKILLS_FACTORY_SOURCE_REVISION", "unknown"),
                    }
                )
                provider = TracerProvider(resource=resource)
                endpoint = _exporter_endpoint()
                if endpoint:
                    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
                trace.set_tracer_provider(provider)
                atexit.register(provider.shutdown)
    return trace.get_tracer("skills_factory.runtime.mcp", "1.0.0")


@contextmanager
def tool_span(tool_name: str, arguments: Any) -> Iterator[tuple[Span, str]]:
    """Emit one bounded span and yield it with a trace-derived run identifier."""
    started = time.perf_counter_ns()
    with _tracer().start_as_current_span(
        f"mcp.tool.{tool_name}",
        kind=SpanKind.INTERNAL,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        context = span.get_span_context()
        run_id = f"{context.trace_id:032x}" if context.is_valid else "unavailable"
        capability = arguments.get("skill_name", tool_name) if isinstance(arguments, Mapping) else tool_name
        span.set_attribute("skills_factory.run_id", run_id)
        span.set_attribute("skills_factory.environment", os.environ.get("SKILLS_FACTORY_ENVIRONMENT", "local"))
        span.set_attribute("skills_factory.capability.name", str(capability))
        span.set_attribute("skills_factory.source_revision", os.environ.get("SKILLS_FACTORY_SOURCE_REVISION", "unknown"))
        span.set_attribute("skills_factory.input_sha256", _sha256(arguments))
        span.set_attribute("skills_factory.external_read", False)
        span.set_attribute("skills_factory.external_write", False)
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("tool.name", tool_name)
        try:
            yield span, run_id
        except Exception as exc:
            span.set_attribute("skills_factory.status", "failure")
            span.set_attribute("skills_factory.error_type", type(exc).__name__)
            span.set_status(Status(StatusCode.ERROR))
            raise
        else:
            span.set_attribute("skills_factory.status", "success")
        finally:
            span.set_attribute("skills_factory.latency_ms", (time.perf_counter_ns() - started) / 1_000_000)


def execute_tool(
    tool_name: str,
    arguments: Any,
    operation: Callable[[], Any],
    add_receipt: Callable[[str, Any, Any, str], Any],
) -> Any:
    """Run a tool, attach its existing receipt, and correlate receipt to span."""
    with tool_span(tool_name, arguments) as (span, run_id):
        result = operation()
        if isinstance(result, Mapping):
            version = result.get("version") or result.get("release_id")
            digest = result.get("content_sha256") or result.get("payload_content_sha256")
            if version:
                span.set_attribute("skills_factory.capability.version", str(version))
            if digest:
                span.set_attribute("skills_factory.capability.digest", str(digest))
        return add_receipt(tool_name, arguments, result, run_id)
