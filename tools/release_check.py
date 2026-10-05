"""Install and exercise the exact wheel and extracted runtime in temporary environments."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, cwd, env):
    result = subprocess.run([str(value) for value in arguments], cwd=cwd, env=env, capture_output=True, text=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"Artifact verification failed at {Path(str(arguments[-1])).name}; command output hidden")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--upgrade-from", type=Path, help="Optional previous wheel to seed retained state before upgrading")
    args = parser.parse_args()
    wheel, runtime = args.wheel.resolve(), args.runtime.resolve()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("DOTS_") and key != "PYTHONPATH"}
    sums = dict(line.split("  ", 1)[::-1] for line in (runtime.parent / "SHA256SUMS.txt").read_text().splitlines())
    for artifact in (wheel, runtime):
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != sums[artifact.name]:
            raise RuntimeError("Artifact checksum mismatch")
    with tempfile.TemporaryDirectory(prefix="dots-release-") as directory:
        temp = Path(directory)
        venv = temp / "wheel-environment"
        run([sys.executable, "-m", "venv", venv], temp, environment)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if args.upgrade_from:
            run([python, "-m", "pip", "install", "--disable-pip-version-check", args.upgrade_from.resolve()], temp, environment)
            script = "from pathlib import Path; from dots_on_paper.config import init_credentials; from dots_on_paper.state import StateStore; init_credentials(Path('credentials.json')); s=StateStore('upgrade.sqlite3'); s.apply({'status':'answer','text':'Retained across beta upgrade','event_id':'upgrade-proof'}); s.close()"
            run([python, "-c", script], temp, environment)
            original_keys = (temp / "credentials.json").read_bytes()
        run([python, "-m", "pip", "install", "--disable-pip-version-check", wheel], temp, environment)
        if args.upgrade_from:
            script = "from pathlib import Path; from dots_on_paper.config import init_credentials; from dots_on_paper.state import StateStore; init_credentials(Path('credentials.json')); s=StateStore('upgrade.sqlite3'); assert s.read()['last_result']['text']=='Retained across beta upgrade'; s.close()"
            run([python, "-c", script], temp, environment)
            assert (temp / "credentials.json").read_bytes() == original_keys
        run([python, ROOT / "tools/smoke.py"], temp, environment)
        checkout = temp / "runtime"
        with zipfile.ZipFile(runtime) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                candidate = (checkout / name).resolve()
                if not candidate.is_relative_to(checkout.resolve()):
                    raise RuntimeError("Unsafe archive path")
            archive.extractall(checkout)
        run([sys.executable, checkout / "tools/setup.py"], checkout, environment)
        installed = checkout / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([installed, checkout / "tools/doctor.py", "--offline", "--mcp"], checkout, environment)
        run([installed, checkout / "tools/smoke.py"], checkout, environment)
    print("Release artifacts verified: checksums, installed wheel, extracted runtime setup, build identity, MCP publication, native images and process restart." + (" Previous-wheel upgrade preserved keys and the last result." if args.upgrade_from else ""))


if __name__ == "__main__":
    main()
