"""Offline safety and input-contract tests for the local ComfyUI adapter.

These tests do not connect to ComfyUI, queue a workflow, or generate media.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from comfyui_local import (  # noqa: E402
    AdapterError,
    _LoopbackOnlyRedirectHandler,
    _safe_parts,
    _unique_target,
    load_workflow,
    validate_base_url,
)


class LocalAdapterSafetyTests(unittest.TestCase):
    def test_accepts_only_loopback_ip_literal_origins(self) -> None:
        self.assertEqual("http://127.0.0.1:8188", validate_base_url("http://127.0.0.1:8188"))
        self.assertEqual("http://[::1]:8188", validate_base_url("http://[::1]"))

        for base_url in (
            "https://127.0.0.1:8188",
            "http://localhost:8188",
            "http://192.168.1.10:8188",
            "http://127.0.0.1:8188/path",
            "http://user:password@127.0.0.1:8188",
            "http://127.0.0.1:8188?admin=true",
            "http://127.0.0.1:8188#fragment",
        ):
            with self.subTest(base_url=base_url), self.assertRaises(AdapterError):
                validate_base_url(base_url)

    def test_redirect_handler_refuses_redirects(self) -> None:
        handler = _LoopbackOnlyRedirectHandler()
        request = Request("http://127.0.0.1:8188/view")
        self.assertIsNone(
            handler.redirect_request(request, None, 302, "Found", {}, "http://example.com/secret")
        )

    def test_workflow_must_be_a_non_empty_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "workflow.json"
            path.write_text('{"1": {"class_type": "CheckpointLoaderSimple"}}', encoding="utf-8")
            self.assertEqual(
                {"1": {"class_type": "CheckpointLoaderSimple"}},
                load_workflow(path),
            )

            for content in ("[]", "null", "{}", "not json"):
                path.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(AdapterError):
                    load_workflow(path)

    def test_output_descriptors_reject_path_traversal_and_unexpected_types(self) -> None:
        invalid_descriptors = (
            {"filename": "../escape.png"},
            {"filename": ".."},
            {"filename": "folder\\escape.png"},
            {"filename": "image.png", "subfolder": "../outside"},
            {"filename": "image.png", "subfolder": "/absolute"},
            {"filename": "image.png", "type": "input"},
        )
        for descriptor in invalid_descriptors:
            with self.subTest(descriptor=descriptor), self.assertRaises(AdapterError):
                _safe_parts(descriptor)

        self.assertEqual(
            ("image.png", "renders/day-1", "output"),
            _safe_parts({"filename": "image.png", "subfolder": "renders/day-1"}),
        )

    def test_output_path_stays_inside_root_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "outputs"
            first = _unique_target(root, {"filename": "image.png", "subfolder": "renders"}, "7")
            first.write_bytes(b"first")
            second = _unique_target(root, {"filename": "image.png", "subfolder": "renders"}, "7")

            self.assertTrue(first.is_relative_to(root.resolve()))
            self.assertTrue(second.is_relative_to(root.resolve()))
            self.assertNotEqual(first, second)
            self.assertEqual(b"first", first.read_bytes())

    def test_output_path_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "outputs"
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            root.mkdir()
            (root / "linked").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(AdapterError):
                _unique_target(root, {"filename": "image.png", "subfolder": "linked"}, "7")


if __name__ == "__main__":
    unittest.main()
