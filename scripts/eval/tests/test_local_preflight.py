from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "local_preflight.py"
spec = importlib.util.spec_from_file_location("local_preflight", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OfflinePreflightTests(unittest.TestCase):
    def test_success_remains_static_only_not_runtime_pass(self):
        commands = []
        def success(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="OK\n", stderr="")
        report = mod.preflight(Path("."), runner=success)
        self.assertEqual("PASS", report["overall_status"])
        self.assertEqual("NOT_RUN", report["runtime_case_execution"])
        self.assertEqual("NOT_VERIFIED", report["runtime_compatibility"])
        self.assertEqual(len(mod.CHECKS), len(commands))

    def test_failed_check_blocks_preflight(self):
        def fail(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, stdout="blocker", stderr="")
        report = mod.preflight(Path("."), runner=fail)
        self.assertEqual("FAIL", report["overall_status"])
        self.assertTrue(all(c["status"] == "FAIL" for c in report["checks"]))

    def test_unavailable_runner_is_blocked_not_pass(self):
        def blocked(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 180)
        report = mod.preflight(Path("."), runner=blocked)
        self.assertEqual("FAIL", report["overall_status"])
        self.assertTrue(all(c["status"] == "BLOCKED" for c in report["checks"]))

    def test_production_source_preflight(self):
        report = mod.preflight(PATH.parents[2])
        self.assertEqual("PASS", report["overall_status"], report["checks"])


if __name__ == "__main__":
    unittest.main()
