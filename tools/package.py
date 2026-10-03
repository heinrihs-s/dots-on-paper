"""Create install archives containing source and assets, never local keys or replies."""
from pathlib import Path
import hashlib
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
EXCLUDE = {"data", ".env", ".venv", "__pycache__", "build", "dist", "release", ".impeccable", ".git", "node_modules"}


def included(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDE or part.endswith(".egg-info") for part in relative.parts):
        return False
    name = path.name.lower()
    if name.startswith(".env") and name != ".env.example":
        return False
    if name == "credentials.json" or name.endswith("-credentials.json"):
        return False
    return path.suffix.lower() not in {".pyc", ".key", ".pem", ".db", ".sqlite", ".sqlite3"} and ".sqlite3-" not in name


def main():
    RELEASE.mkdir(exist_ok=True)
    plugin_path = RELEASE / "dots-on-paper-0.1.0.zip"
    with zipfile.ZipFile(plugin_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and included(path):
                archive.write(path, path.relative_to(ROOT))
        names = archive.namelist()
        assert "plugin.json" in names and "mcp.json" in names
        assert not any(name.startswith("data/") or name.endswith("credentials.json") for name in names)
    ha_path = RELEASE / "dots-on-paper-home-assistant-0.1.0.zip"
    with zipfile.ZipFile(ha_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "custom_components").rglob("*")):
            if path.is_file() and included(path):
                archive.write(path, path.relative_to(ROOT))
        for path in sorted((ROOT / "examples/home-assistant").iterdir()):
            if path.is_file() and included(path):
                archive.write(path, path.name)
        archive.write(ROOT / "LICENSE", "LICENSE")
        archive.write(ROOT / "demo/assets/Figtree-LICENSE.txt", "Figtree-LICENSE.txt")
    campaign_path = RELEASE / "dots-on-paper-x-package-0.1.0.zip"
    with zipfile.ZipFile(campaign_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "campaign").rglob("*")):
            if path.is_file() and included(path):
                archive.write(path, path.relative_to(ROOT))
        for name in ("LICENSE", "NOTICE.md", "docs/product-facts.md", "docs/real-dot.md", "docs/verification.md"):
            archive.write(ROOT / name, name)
        for path in sorted((ROOT / "brand").rglob("*")):
            if path.is_file() and included(path):
                archive.write(path, path.relative_to(ROOT))
        for name in ("Figtree.ttf", "Figtree-LICENSE.txt"):
            archive.write(ROOT / "demo/assets" / name, "demo/assets/" + name)
        archive.writestr("README.txt", "Open campaign/README.md for the four-post package and campaign/posts.md for captions.\nMedia is in campaign/media/. All scenes are scripted concepts; nothing was sent.\nThe separate source archive contains the actual MCP, Home Assistant and e-ink integrations.\n")
    for path in (plugin_path, ha_path, campaign_path):
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
        print(f"Created {path.name}: {path.stat().st_size:,} bytes")
    wheels = []
    for wheel in sorted((ROOT / "dist").glob("*.whl")):
        destination = RELEASE / wheel.name
        shutil.copy2(wheel, destination)
        wheels.append(destination)
    downloads = [plugin_path, ha_path, campaign_path, *wheels]
    sums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in downloads)
    (RELEASE / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    print("Created SHA256SUMS.txt for the source, HA, and available wheel downloads")


if __name__ == "__main__":
    main()
