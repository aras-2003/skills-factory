"""Source-pinned load_skill contract tests over the real Python MCP stdio API."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from starlette.testclient import TestClient


RUNTIME_DIR = Path(__file__).resolve().parents[1]
ROOT = RUNTIME_DIR.parents[1]
SOURCE_REVISION = "a" * 40
STALE_REVISION = "b" * 40


def write_packaged_fixture(root: Path) -> Path:
    skill = root / "skills" / "meta" / "sample"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: sample\nmetadata:\n  version: 1.0.0\n  maturity: candidate\n---\nFixture instruction body.\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256()
    for item in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = item.relative_to(root).as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    manifest = {
        "channel": "lab", "version": "1.0.0", "release_id": "fixture-1",
        "source_revision": SOURCE_REVISION, "payload_content_sha256": digest.hexdigest(),
    }
    manifest_path = root / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


class LoadSkillSourceRevisionTests(unittest.TestCase):
    def test_tools_list_and_calls_enforce_optional_source_revision_contract(self):
        with tempfile.TemporaryDirectory(prefix="sf-load-skill-source-") as tmp:
            root = Path(tmp) / "package"
            manifest_path = write_packaged_fixture(root)
            params = StdioServerParameters(
                command=sys.executable,
                args=[str(RUNTIME_DIR / "server.py")],
                env={"PLUGIN_ROOT": str(root), "MPLCONFIGDIR": str(Path(tmp) / "mpl-cache")},
                cwd=ROOT,
            )

            async def run_calls():
                async with stdio_client(params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        listed = await session.list_tools()
                        load_tool = next(tool for tool in listed.tools if tool.name == "load_skill")
                        schema = load_tool.model_dump(by_alias=True)["inputSchema"]
                        self.assertEqual(schema["required"], ["skill_name"])
                        self.assertEqual(schema["additionalProperties"], False)
                        revision_schema = schema["properties"]["expected_source_revision"]
                        self.assertNotIn("type", revision_schema)
                        self.assertNotIn("default", revision_schema)
                        self.assertNotIn("minLength", revision_schema)
                        self.assertNotIn("maxLength", revision_schema)
                        self.assertNotIn("pattern", revision_schema)
                        self.assertNotIn("minLength", schema["properties"]["skill_name"])
                        self.assertNotIn("maxLength", schema["properties"]["skill_name"])

                        omitted = await session.call_tool("load_skill", {"skill_name": "sample"})
                        self.assertFalse(omitted.is_error)
                        self.assertIn("Fixture instruction body.", omitted.content[0].text)

                        matching = await session.call_tool("load_skill", {
                            "skill_name": "sample", "expected_source_revision": SOURCE_REVISION,
                        })
                        self.assertFalse(matching.is_error)
                        self.assertIn(SOURCE_REVISION, matching.content[0].text)

                        failures = [
                            ({"skill_name": "sample", "expected_source_revision": STALE_REVISION}, "SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision."),
                            ({"skill_name": "sample", "expected_source_revision": ""}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": "a" * 39}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": "a" * 41}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": SOURCE_REVISION + "\n"}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": "A" * 40}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": None}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "sample", "expected_source_revision": 42}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "", "expected_source_revision": "A" * 40}, "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID."),
                            ({"skill_name": "", "expected_source_revision": STALE_REVISION}, "SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision."),
                            ({"skill_name": "sample", "expected_source_revision": SOURCE_REVISION, "unexpected": "do-not-echo"}, "INVALID_TOOL_ARGUMENTS: Invalid tool arguments."),
                            ({"skill_name": "sample", "expected_source_revision": None, "unexpected": "do-not-echo"}, "INVALID_TOOL_ARGUMENTS: Invalid tool arguments."),
                        ]
                        for arguments, code in failures:
                            with self.subTest(arguments=arguments, expected_code=code):
                                result = await session.call_tool("load_skill", arguments)
                                self.assertTrue(result.is_error)
                                text = "\n".join(item.text for item in result.content if item.type == "text")
                                self.assertIn(text, (code, f"Error executing tool load_skill: {code}"))
                                self.assertNotIn("Fixture instruction body.", text)
                                self.assertNotIn(STALE_REVISION, text)
                                self.assertNotIn("do-not-echo", text)

                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        manifest["payload_content_sha256"] = "0" * 64
                        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                        for pin in (SOURCE_REVISION, STALE_REVISION):
                            with self.subTest(corrupt_payload_pin=pin):
                                unverifiable = await session.call_tool("load_skill", {
                                    "skill_name": "sample", "expected_source_revision": pin,
                                })
                                self.assertTrue(unverifiable.is_error)
                                error_text = "\n".join(item.text for item in unverifiable.content if item.type == "text")
                                self.assertEqual(error_text, "Error executing tool load_skill: SOURCE_REVISION_UNVERIFIABLE: Packaged source revision could not be verified.")
                                for secret in (SOURCE_REVISION, STALE_REVISION, str(root), "Fixture instruction body."):
                                    self.assertNotIn(secret, error_text)

            asyncio.run(run_calls())


class LoadSkillSourceRevisionHTTPTests(unittest.TestCase):
    def test_streamable_http_source_pin_contract(self):
        with tempfile.TemporaryDirectory(prefix="sf-load-skill-http-") as tmp:
            root = Path(tmp) / "package"
            manifest_path = write_packaged_fixture(root)
            with patch.dict(os.environ, {"PLUGIN_ROOT": str(root), "MPLCONFIGDIR": str(Path(tmp) / "mpl-cache")}):
                sys.path.insert(0, str(RUNTIME_DIR))
                try:
                    import server as runtime_server
                finally:
                    sys.path.remove(str(RUNTIME_DIR))
                self.assertEqual(Path(runtime_server.__file__).resolve(), RUNTIME_DIR / "server.py")

                with TestClient(runtime_server.app, base_url="http://127.0.0.1:8000") as client:
                    headers = {"Accept": "application/json, text/event-stream"}

                    def rpc(method, params, request_id=1):
                        response = client.post("/mcp", headers=headers, json={
                            "jsonrpc": "2.0", "id": request_id, "method": method, "params": params,
                        })
                        self.assertEqual(response.status_code, 200, response.text)
                        if response.headers.get("mcp-session-id"):
                            headers["mcp-session-id"] = response.headers["mcp-session-id"]
                        if response.headers.get("content-type", "").startswith("text/event-stream"):
                            payloads = [line[5:].strip() for line in response.text.splitlines() if line.startswith("data:")]
                            self.assertEqual(len(payloads), 1, response.text)
                            result = json.loads(payloads[0])
                        else:
                            result = response.json()
                        self.assertNotIn("error", result)
                        return result["result"]

                    initialize = rpc("initialize", {
                        "protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "source-pin-http-test", "version": "1"},
                    })
                    self.assertIn("protocolVersion", initialize)
                    self.assertIn("mcp-session-id", headers)
                    notification = client.post("/mcp", headers=headers, json={
                        "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
                    })
                    self.assertEqual(notification.status_code, 202)

                    tools = rpc("tools/list", {})["tools"]
                    schema = next(tool for tool in tools if tool["name"] == "load_skill")["inputSchema"]
                    self.assertEqual(schema["required"], ["skill_name"])
                    self.assertFalse(schema["additionalProperties"])
                    self.assertNotIn("type", schema["properties"]["expected_source_revision"])

                    def call(args):
                        return rpc("tools/call", {"name": "load_skill", "arguments": args})

                    with self.subTest(case_id="ARCH-PAR-HTTP-02-unpinned"):
                        unpinned = call({"skill_name": "sample"})
                        self.assertFalse(unpinned.get("isError", False))
                        self.assertIn("Fixture instruction body.", json.dumps(unpinned))

                    with self.subTest(case_id="ARCH-PAR-HTTP-03-matching"):
                        matching = call({"skill_name": "sample", "expected_source_revision": SOURCE_REVISION})
                        self.assertFalse(matching.get("isError", False))
                        self.assertIn("Fixture instruction body.", json.dumps(matching))
                        payloads = []
                        for item in matching["content"]:
                            if item["type"] != "text":
                                continue
                            try:
                                payload = json.loads(item["text"])
                            except ValueError:
                                continue
                            if isinstance(payload, dict) and "source_revision" in payload:
                                payloads.append(payload)
                        self.assertEqual(len(payloads), 1)
                        self.assertEqual(payloads[0]["source_revision"], SOURCE_REVISION)

                    def assert_failure(case_id, args, expected, *sensitive_values):
                        with self.subTest(case_id=case_id):
                            result = call(args)
                            self.assertTrue(result["isError"])
                            texts = [item["text"] for item in result["content"] if item["type"] == "text"]
                            self.assertEqual(len(texts), 1)
                            self.assertIn(texts[0], (expected, f"Error executing tool load_skill: {expected}"))
                            response_json = json.dumps(result)
                            for secret in ("Fixture instruction body.", SOURCE_REVISION, STALE_REVISION, str(root), *sensitive_values):
                                self.assertNotIn(secret, response_json)

                    assert_failure(
                        "ARCH-PAR-HTTP-04-stale", {"skill_name": "sample", "expected_source_revision": STALE_REVISION},
                        "SOURCE_REVISION_MISMATCH: The packaged skill source does not match the requested revision.",
                    )
                    assert_failure(
                        "ARCH-PAR-HTTP-05-null", {"skill_name": "sample", "expected_source_revision": None},
                        "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID.",
                    )
                    assert_failure(
                        "ARCH-PAR-HTTP-06-number", {"skill_name": "sample", "expected_source_revision": 42},
                        "INVALID_SOURCE_REVISION: expected_source_revision must be a lowercase 40-character Git commit ID.",
                    )
                    assert_failure(
                        "ARCH-PAR-HTTP-07-unknown-field",
                        {"skill_name": "sample", "expected_source_revision": SOURCE_REVISION, "unexpected": "do-not-echo"},
                        "INVALID_TOOL_ARGUMENTS: Invalid tool arguments.", "do-not-echo",
                    )

                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["payload_content_sha256"] = "0" * 64
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    assert_failure(
                        "ARCH-PAR-HTTP-08-corrupt-stale",
                        {"skill_name": "sample", "expected_source_revision": STALE_REVISION},
                        "SOURCE_REVISION_UNVERIFIABLE: Packaged source revision could not be verified.",
                    )


if __name__ == "__main__":
    unittest.main()
