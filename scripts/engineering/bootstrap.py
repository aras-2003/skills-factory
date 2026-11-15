"""One supported local Python environment; --check never installs packages."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"], check=True, capture_output=True)
    temporary = ROOT / ".tmp" / "python-tests"
    temporary.mkdir(parents=True, exist_ok=True)
    if args.check:
        missing = [n for n in ("yaml", "jsonschema") if importlib.util.find_spec(n) is None]
        if missing:
            print("Missing locked environment dependencies: " + ", ".join(missing))
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
