"""One supported local Python environment; --check never installs packages."""
from __future__ import annotations

import argparse
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[2]


def dependency_errors(lock: Path) -> list[str]:
    errors = []
    for name, expected in re.findall(r"(?m)^([A-Za-z0-9_.-]+)==([^\s;\\]+)", lock.read_text()):
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"{name}: missing")
            continue
        if actual != expected:
            errors.append(f"{name}: expected {expected}, installed {actual}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], check=True, capture_output=True)
    temporary = ROOT / ".tmp" / "python-tests"
    temporary.mkdir(parents=True, exist_ok=True)
    if args.check:
        errors = dependency_errors(ROOT / "requirements-dev.lock")
        if errors:
            print("Locked environment mismatch:\n" + "\n".join(errors))
            return 1
        print(f"Git and local dependencies: OK; run tests with TMPDIR={temporary.resolve()}")
        return 0
    env_dir = ROOT / ".venv"
    if not env_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(env_dir)], check=True)
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--require-hashes", "-r", str(ROOT / "requirements-dev.lock")], check=True)
    print(f"Use {python}; set TMPDIR to {temporary.resolve()} before local tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
