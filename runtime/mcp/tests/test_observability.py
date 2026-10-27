from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runtime" / "mcp"))

from observability import execute_tool  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402


class ObservabilityTests(unittest.TestCase):
    def test_span_is_hash_only_and_receipt_links_the_trace(self):
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        arguments = {"user_request": "private prompt text must not enter telemetry"}

        with patch("observability.trace.get_tracer_provider", return_value=provider):
            result = execute_tool(
                "route_investment_request",
                arguments,
                lambda: {"route": "portfolio", "version": "1.0.0"},
                lambda name, args, output, run_id: {
                    "result": output,
                    "tool_receipt": {"tool_name": name, "run_id": run_id},
                },
            )

        span = exporter.get_finished_spans()[0]
        attributes = dict(span.attributes)
        expected_input_digest = hashlib.sha256(
            json.dumps(arguments, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        self.assertEqual(span.name, "mcp.tool.route_investment_request")
        self.assertEqual(attributes["skills_factory.input_sha256"], expected_input_digest)
        self.assertEqual(attributes["skills_factory.external_read"], False)
        self.assertEqual(attributes["skills_factory.external_write"], False)
        self.assertEqual(attributes["skills_factory.capability.version"], "1.0.0")
        self.assertEqual(result["tool_receipt"]["run_id"], f"{span.context.trace_id:032x}")
        self.assertNotIn(arguments["user_request"], repr(attributes))
        self.assertNotIn("skills_factory.input", attributes)

    def test_failure_records_type_without_exception_message(self):
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("observability.trace.get_tracer_provider", return_value=provider):
            with self.assertRaisesRegex(RuntimeError, "sensitive exception detail"):
                execute_tool(
                    "load_skill",
                    {"skill_name": "example"},
                    lambda: (_ for _ in ()).throw(RuntimeError("sensitive exception detail")),
                    lambda name, args, output, run_id: output,
                )

        span = exporter.get_finished_spans()[0]
        attributes = dict(span.attributes)
        self.assertEqual(attributes["skills_factory.status"], "failure")
        self.assertEqual(attributes["skills_factory.error_type"], "RuntimeError")
        self.assertNotIn("sensitive exception detail", repr(attributes))
        self.assertNotIn("exception.message", attributes)
        self.assertEqual(span.events, ())


if __name__ == "__main__":
    unittest.main()
