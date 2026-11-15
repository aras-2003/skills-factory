import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("sdlc_bootstrap", Path(__file__).resolve().parents[1] / "bootstrap.py")
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def test_importable_but_wrong_version_is_not_a_valid_environment(self):
        with tempfile.TemporaryDirectory() as td:
            lock = Path(td) / "lock"
            lock.write_text("mcp==2.3.0 \\\n    --hash=sha256:example\n")
            with patch.object(bootstrap.importlib.metadata, "version", return_value="1.0.0"):
                self.assertEqual(["mcp: expected 2.3.0, installed 1.0.0"], bootstrap.dependency_errors(lock))
            with patch.object(bootstrap.importlib.metadata, "version", return_value="2.3.0"):
                self.assertEqual([], bootstrap.dependency_errors(lock))
