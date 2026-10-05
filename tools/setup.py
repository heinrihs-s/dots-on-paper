"""Create an isolated checkout environment and private local bridge keys."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(arguments: list[str], environment: dict[str, str]) -> None:
    result = subprocess.run(arguments, cwd=ROOT, env=environment, capture_output=True, text=True)
    if result.returncode:
        # pip output may contain private package-index URLs; keep it out of logs.
        raise RuntimeError("Setup command failed. Check Python, network access, and directory permissions.")


def main() -> int:
    if sys.version_info < (3, 11):
        print("Python 3.11 or later is required.", file=sys.stderr)
        return 1
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    virtual_environment = ROOT / ".venv"
    python = virtual_environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    try:
        if not python.is_file():
            print("Creating a local Python environment...", flush=True)
            run([sys.executable, "-m", "venv", str(virtual_environment)], environment)
        print("Installing Dots on Paper and its renderer dependency...", flush=True)
        run([str(python), "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", str(ROOT)], environment)
        print("Initializing private bridge keys...", flush=True)
        run([str(python), "-m", "dots_on_paper", "--init", "--data-dir", str(ROOT / "data")], environment)
    except (RuntimeError, OSError):
        print("Setup could not finish. No credentials were printed or replaced. Run the installation steps in docs/setup.md to inspect the failing command.", file=sys.stderr)
        return 1
    print("Setup complete. Start with .\\run.ps1 on Windows or .venv/bin/python -m dots_on_paper --data-dir ./data --open on macOS/Linux.")
    print("Before starting, check installation with the environment's Python: tools/doctor.py --offline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
