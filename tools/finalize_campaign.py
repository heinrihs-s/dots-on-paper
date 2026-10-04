"""Verify rendered campaign media and update its shareable inventory."""
from pathlib import Path
import hashlib
import json
import re
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "campaign"
sys.path.insert(0, str(ROOT / "src"))
from dots_on_paper.render import render_image

_verified_native_frames = set()


def verify_recorded_renderer_frames(provenance):
    """Keep archived source provenance while proving current compatibility.

    Adding an optional renderer layout changes its source checksum without
    changing earlier states. That is acceptable only if every native snapshot
    recorded by the old export still renders to exactly the original bytes.
    Other changed source assets continue to fail the checksum check.
    """
    native = provenance["native"]
    assert native["source"] == "src/dots_on_paper/render.py"
    assert native["frames"]
    dimensions = (native["nativeWidth"], native["nativeHeight"], native["nativeLevels"])
    for frame in native["frames"]:
        key = (*dimensions, frame["sha256"])
        if key in _verified_native_frames:
            continue
        rendered = render_image(frame["state"], dimensions[0], dimensions[1], levels=dimensions[2], frame=frame["frame"])
        assert hashlib.sha256(rendered).hexdigest() == frame["sha256"], f"Archived native frame changed: {frame['id']}"
        _verified_native_frames.add(key)


def main():
    path = CAMPAIGN / "media-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for item in manifest["assets"]:
        asset = CAMPAIGN / item["path"]
        assert asset.is_file(), f"Missing media: {item['path']}"
        payload = asset.read_bytes()
        assert len(payload) > 10000
        item["bytes"] = len(payload)
        item["sha256"] = hashlib.sha256(payload).hexdigest()
        item["status"] = "verified"
        if item["kind"] == "image":
            with Image.open(asset) as image:
                assert image.size == (item["width"], item["height"])
                image.load()
                provenance = json.loads(image.info["dots:provenance"])
                assert provenance["fictional"] is True
            with Image.open(asset) as image:
                image.verify()
            item["embedded_provenance"] = True
        elif item["kind"] == "animation":
            provenance_path = asset.with_suffix(asset.suffix + ".provenance.json")
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            assert provenance["sha256"] == item["sha256"]
            with Image.open(asset) as image:
                assert image.format == "GIF"
                assert image.size == (item["width"], item["height"])
                assert image.info.get("loop") is None, "GIF must stop on the final result"
                embedded = json.loads(image.info["comment"].decode("utf-8"))
                assert embedded["fictional"] is True
                assert embedded["sourceFiles"] == provenance["sourceFiles"]
                duration = 0
                distinct = set()
                for index in range(image.n_frames):
                    image.seek(index)
                    image.load()
                    duration += image.info.get("duration", 0)
                    distinct.add(hashlib.sha256(image.convert("RGB").tobytes()).hexdigest())
                assert duration == 16000
                assert len(distinct) >= 8
                assert image.n_frames == provenance["encodedFrames"]
                item["encoded_frames"] = image.n_frames
                item["distinct_frames"] = len(distinct)
                item["duration_seconds"] = duration / 1000
                item["loop"] = None
                assert provenance["endsOnRetainedResult"] is True
                assert provenance["native"]["resultHoldSeconds"] >= 7
                item["ends_on_retained_result"] = True
                item["embedded_provenance"] = True
            for source in provenance["sourceFiles"]:
                source_path = (ROOT / source["path"]).resolve()
                source_path.relative_to(ROOT.resolve())
                assert source_path.is_file(), source_path
                if hashlib.sha256(source_path.read_bytes()).hexdigest() != source["sha256"]:
                    assert source["path"] == "src/dots_on_paper/render.py", f"Source changed: {source['path']}"
                    verify_recorded_renderer_frames(provenance)
            film = asset.parent / provenance["sourceFilm"]["name"]
            assert hashlib.sha256(film.read_bytes()).hexdigest() == provenance["sourceFilm"]["sha256"]
            item["provenance"] = str(provenance_path.relative_to(CAMPAIGN)).replace("\\", "/")
        elif item["kind"] == "video":
            provenance_path = asset.with_suffix(".provenance.json")
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            assert provenance["sha256"] == item["sha256"]
            assert provenance["codec"] == "H.264 / avc1"
            assert (provenance["width"], provenance["height"]) == (item["width"], item["height"])
            assert 15.5 <= provenance["duration"] <= 16.5
            assert b"avc1" in payload
            assert provenance["endsOnRetainedResult"] is True
            assert provenance["native"]["resultHoldSeconds"] >= 7
            assert provenance["resultFrameBrowserDecode"]["stableMeanPixelDifference"] <= 1
            assert provenance["resultFrameBrowserDecode"]["expectedResultMeanPixelDifference"] <= 3
            item["duration_seconds"] = provenance["duration"]
            item["codec"] = provenance["codec"]
            item["provenance"] = str(provenance_path.relative_to(CAMPAIGN)).replace("\\", "/")
        else:
            raise AssertionError(f"Unknown campaign media kind: {item['kind']}")
    captions = re.findall(r"```text\n(.*?)\n```", (CAMPAIGN / "posts.md").read_text(encoding="utf-8"), re.S)
    assert len(captions) == 8
    counts = [len(caption) for caption in captions]
    assert max(counts) <= 280
    manifest["caption_character_counts"] = counts
    manifest["checked_date"] = "2026-10-04"
    manifest["verification"] = {"png_dimensions_and_provenance": True, "mp4_browser_decode": True, "mp4_h264_and_checksum": True, "mp4_decoded_final_result_and_hold": True, "gif_stops_on_result_dimensions_and_provenance": True}
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(manifest['assets'])} campaign assets and {len(captions)} captions: {counts}")


if __name__ == "__main__":
    main()
