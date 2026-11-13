from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(script: Path) -> int:
    print(f"\n==> {script.name}")
    return subprocess.run([sys.executable, str(script)], check=False).returncode


def main() -> int:
    here = Path(__file__).resolve().parent
    scripts = [
        here / "validate_skill.py",
        here / "validate_tests.py",
        here / "validate_catalog.py",
        here / "validate_provenance.py",
        here.parent / "catalog" / "validate_runtime_registry_parity.py",
        here / "validate_investing.py",
        here / "validate_runtime.py",
        here / "presentation_model.py",
    ]
    results = [run(script) for script in scripts]
    return 1 if any(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
