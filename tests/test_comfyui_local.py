from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/media/creative-generation/scripts"))

from comfyui_local import AdapterError, _safe_parts, load_workflow, run_workflow, validate_base_url


class BaseUrlTests(unittest.TestCase):
    def test_accepts_ipv4_and_ipv6_loopback(self) -> None:
        self.assertEqual(validate_base_url("http://127.0.0.1:8188"), "http://127.0.0.1:8188")
        self.assertEqual(validate_base_url("http://[::1]:8190/"), "http://[::1]:8190")

    def test_rejects_non_loopback_and_named_hosts(self) -> None:
        for value in ("http://localhost:8188", "http://192.168.1.4:8188", "https://127.0.0.1:8188", "https://example.com"):
            with self.subTest(value=value), self.assertRaises(AdapterError):
                validate_base_url(value)

    def test_opener_blocks_redirects(self) -> None:
        from comfyui_local import _LoopbackOnlyRedirectHandler, _opener

        handler = next(handler for handler in _opener().handlers if isinstance(handler, _LoopbackOnlyRedirectHandler))
        self.assertIsNone(handler.redirect_request(None, None, 302, "Found", {}, "https://example.com"))

    def test_rejects_credentials_and_url_suffixes(self) -> None:
        for value in ("http://user:pass@127.0.0.1:8188", "http://127.0.0.1:8188/api", "http://127.0.0.1:8188/?q=x"):
            with self.subTest(value=value), self.assertRaises(AdapterError):
                validate_base_url(value)


class WorkflowTests(unittest.TestCase):
    def test_load_workflow_requires_a_non_empty_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text('{"1":{"class_type":"SaveImage"}}', encoding="utf-8")
            self.assertEqual(load_workflow(path)["1"]["class_type"], "SaveImage")
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(AdapterError):
                load_workflow(path)

    def test_rejects_traversal_in_output_metadata(self) -> None:
        with self.assertRaises(AdapterError):
            _safe_parts({"filename": "result.png", "subfolder": "../../outside"})
        with self.assertRaises(AdapterError):
            _safe_parts({"filename": "../result.png"})
        with self.assertRaises(AdapterError):
            _safe_parts({"filename": "result.png", "type": []})

    def test_download_limit_removes_partial_output(self) -> None:
        from comfyui_local import _download

        class Response:
            headers = {"Content-Length": "3"}

            def __init__(self) -> None:
                self.chunks = [b"123", b"45", b""]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _size: int) -> bytes:
                return self.chunks.pop(0)

        class Opener:
            def open(self, *_args, **_kwargs):
                return Response()

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "output.png"
            with patch("comfyui_local._opener", return_value=Opener()):
                with self.assertRaisesRegex(AdapterError, "download limit"):
                    _download("http://127.0.0.1:8188", {"filename": "image.png"}, target, 4)
            self.assertFalse(target.exists())

    @patch("comfyui_local._download")
    @patch("comfyui_local._json_request")
    def test_queues_polls_and_saves_only_reported_outputs(self, mock_json: object, mock_download: object) -> None:
        mock_json.side_effect = [
            {"prompt_id": "abc-123"},
            {"abc-123": {"outputs": {"7": {"images": [{"filename": "image.png", "subfolder": "", "type": "output"}]}}}},
        ]

        def save(_base_url: str, _descriptor: dict[str, object], target: Path, _max_bytes: int) -> Path:
            target.write_bytes(b"image")
            return target

        mock_download.side_effect = save
        with tempfile.TemporaryDirectory() as tmp:
            result = run_workflow("http://127.0.0.1:8188", {"1": {"class_type": "SaveImage"}}, Path(tmp))
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0].is_file())
            self.assertEqual(result[0].read_bytes(), b"image")
        self.assertEqual(mock_json.call_count, 2)
        self.assertEqual(mock_download.call_count, 1)

    @patch("comfyui_local._json_request")
    def test_reports_workflow_failure_without_claiming_success(self, mock_json: object) -> None:
        mock_json.side_effect = [
            {"prompt_id": "abc-123"},
            {"abc-123": {"status": {"status_str": "error"}, "outputs": {}}},
        ]
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(AdapterError, "workflow failed"):
            run_workflow("http://127.0.0.1:8188", {"1": {"class_type": "SaveImage"}}, Path(tmp), timeout_seconds=2)

    @patch("comfyui_local._json_request")
    def test_refuses_completed_job_without_output(self, mock_json: object) -> None:
        mock_json.side_effect = [
            {"prompt_id": "abc-123"},
            {"abc-123": {"status": {"status_str": "success"}, "outputs": {"7": {}}}},
        ]
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(AdapterError, "without a downloadable"):
            run_workflow("http://127.0.0.1:8188", {"1": {"class_type": "SaveImage"}}, Path(tmp), timeout_seconds=2)


if __name__ == "__main__":
    unittest.main()
