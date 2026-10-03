"""Encode shared-palette README loops and verify the resulting playback.

Called by export-github.mjs. Requires Pillow only. No source pixels are edited:
the canvas frames are reduced to the GIF palette, with stationary pixels kept
identical across frames so the moving avatar does not shimmer the background.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

from PIL import Image

source, destination, metadata_path = map(Path, sys.argv[1:4])
provenance = json.loads(metadata_path.read_text(encoding="utf-8"))
paths = sorted(source.glob("frame-*.png"))
if len(paths) != 192:
    raise SystemExit(f"Expected 192 canvas frames, found {len(paths)}")
dimensions = (960, 720)
sample_indices = [0, 24, 48, 72, 96, 120, 144, 168]
sheet = Image.new("RGB", (dimensions[0], dimensions[1] * len(sample_indices)))
for row, index in enumerate(sample_indices):
    with Image.open(paths[index]) as frame:
        if frame.size != dimensions:
            raise SystemExit(f"Unexpected frame dimensions: {frame.size}")
        sheet.paste(frame.convert("RGB"), (0, dimensions[1] * row))
palette = sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
frames = []
for path in paths:
    with Image.open(path) as frame:
        if frame.size != dimensions:
            raise SystemExit(f"Unexpected frame dimensions in {path}: {frame.size}")
        frames.append(frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE))
durations = [80 if index % 3 != 2 else 90 for index in range(len(frames))]
frames[0].save(
    destination, save_all=True, append_images=frames[1:],
    duration=durations, loop=0, optimize=True, disposal=1,
    comment=json.dumps(provenance, ensure_ascii=False).encode("utf-8"),
)
with Image.open(destination) as encoded:
    total_duration = 0
    frame_hashes = set()
    loop = encoded.info.get("loop")
    if loop != 0:
        raise SystemExit("GIF must loop indefinitely")
    if encoded.size != dimensions:
        raise SystemExit(f"GIF has unexpected dimensions: {encoded.size}")
    comment = json.loads(encoded.info["comment"].decode("utf-8"))
    if not comment.get("fictional") or not comment.get("sourceFiles"):
        raise SystemExit("GIF is missing scripted-content/source provenance")
    for index in range(encoded.n_frames):
        encoded.seek(index)
        encoded.load()
        total_duration += encoded.info.get("duration", 0)
        frame_hashes.add(sha256(encoded.convert("RGB").tobytes()).hexdigest())
    if total_duration != 16000:
        raise SystemExit(f"GIF must last 16 seconds, got {total_duration} ms")
    if len(frame_hashes) < 8:
        raise SystemExit(f"GIF has too little motion: {len(frame_hashes)} distinct frames")
    print(json.dumps({
        "width": encoded.width, "height": encoded.height,
        "encodedFrames": encoded.n_frames, "distinctFrames": len(frame_hashes),
        "durationSeconds": total_duration / 1000, "loop": loop,
        "bytes": destination.stat().st_size,
    }))
