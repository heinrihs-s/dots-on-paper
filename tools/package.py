"""Build versioned runtime/HA archives with an explicit file allowlist."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
EXCLUDE = {"data", ".env", ".venv", "__pycache__", "build", "dist", "release", ".impeccable", ".git", "node_modules"}
RUNTIME_FILES = ("README.md", "CONTRIBUTING.md", "LICENSE", "NOTICE.md", "SECURITY.md", "pyproject.toml", "requirements.txt", "run.ps1", "Dockerfile", ".dockerignore", "compose.yaml", ".env.example", "plugin.json", "mcp.json", ".agents/plugins/marketplace.json", "tools/setup.py", "tools/doctor.py", "tools/smoke.py", "tools/package.py", "tools/release_check.py", "tools/docker_smoke.py", "brand/header-paper-v2.png", "brand/header-paper-v2.provenance.json")


def included(path: Path) -> bool:
    if any(part in EXCLUDE or part.endswith(".egg-info") for part in path.relative_to(ROOT).parts):
        return False
    name = path.name.lower()
    if name.startswith(".env") and name != ".env.example" or name == "credentials.json" or name.endswith("-credentials.json"):
        return False
    return path.suffix.lower() not in {".pyc", ".key", ".pem", ".db", ".sqlite", ".sqlite3"} and ".sqlite3-" not in name


def archive(path: Path, files: list[Path]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for file in sorted(set(files)):
            if not file.is_file() or not included(file):
                continue
            info = zipfile.ZipInfo(file.relative_to(ROOT).as_posix(), date_time=(2026, 10, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            output.writestr(info, file.read_bytes())
    with zipfile.ZipFile(path) as result:
        assert result.testzip() is None
        assert not any(name.startswith("data/") or name.endswith("credentials.json") for name in result.namelist())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", action="store_true", help="Separately package large scripted media")
    args = parser.parse_args()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    RELEASE.mkdir(exist_ok=True)
    runtime = RELEASE / f"dots-on-paper-{version}.zip"
    files = [ROOT / name for name in RUNTIME_FILES]
    for directory in ("src", "docs", "examples", "skills"):
        files.extend((ROOT / directory).rglob("*"))
    archive(runtime, files)
    ha = RELEASE / f"dots-on-paper-home-assistant-{version}.zip"
    archive(ha, [*(ROOT / "custom_components").rglob("*"), *(ROOT / "examples/home-assistant").rglob("*"), ROOT / "LICENSE", ROOT / "src/dots_on_paper/assets/Figtree-LICENSE.txt"])
    downloads = [runtime, ha]
    for wheel in sorted((ROOT / "dist").glob(f"dots_on_paper-{version}-*.whl")):
        destination = RELEASE / wheel.name
        shutil.copy2(wheel, destination)
        downloads.append(destination)
    if args.campaign:
        campaign = RELEASE / f"dots-on-paper-media-{version}.zip"
        archive(campaign, [*(ROOT / "campaign").rglob("*"), *(ROOT / "brand").rglob("*"), ROOT / "LICENSE", ROOT / "NOTICE.md"])
        downloads.append(campaign)
    (RELEASE / "SHA256SUMS.txt").write_text("".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in downloads), encoding="utf-8", newline="\n")
    print("\n".join(f"Created {path.name}: {path.stat().st_size:,} bytes" for path in downloads))
    print("Created SHA256SUMS.txt. Runtime downloads exclude campaign films and local state.")


if __name__ == "__main__":
    main()
