"""Build the original Cool-dot vector logo without runtime font dependencies.

Optional design dependency: fonttools. Committed SVGs contain outlined Figtree.
    python tools/build_cool_logo.py --font-tools-path /path/to/fonttools
"""
from pathlib import Path
import json
import sys

if "--font-tools-path" in sys.argv:
    sys.path.insert(0, sys.argv[sys.argv.index("--font-tools-path") + 1])

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand"
INK = "#171719"
LIGHT = "#f5f5f7"
FONT = ROOT / "demo/assets/Figtree.ttf"
HEART = "M256 154C218 101 181 76 142 76C79 76 61 116 61 192C61 257 104 295 145 338C183 378 227 412 256 434C285 412 329 378 367 338C408 295 451 257 451 192C451 116 433 76 370 76C331 76 294 101 256 154Z"
LENS = "M118 184H223Q235 184 237 197L242 232Q243 260 221 260H153Q135 260 129 242L114 207Q106 184 118 184Z"


def mark(color=INK):
    # A compound clipping path removes both lenses and their bridge from the
    # silhouette. Negative space stays transparent on every background.
    return f'''<defs><mask id="cool-lenses" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512"><path d="{HEART}" fill="#fff"/><path d="{LENS}" fill="#000"/><path d="{LENS}" transform="translate(512 0) scale(-1 1)" fill="#000"/><path d="M236 197Q256 181 276 197" fill="none" stroke="#000" stroke-width="16" stroke-linecap="round"/></mask></defs><path d="{HEART}" fill="{color}" mask="url(#cool-lenses)"/>'''


def svg(body, width, height, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{title}</title>{body}</svg>\n'''


def text_paths(text, weight, size, x, baseline, color):
    font = instantiateVariableFont(TTFont(FONT), {"wght": weight})
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    paths = []
    for letter in text:
        name = cmap[ord(letter)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        if pen.getCommands():
            paths.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {baseline}) scale({scale:.6f} {-scale:.6f})"/>')
        x += glyphs[name].width * scale
    return f'<g fill="{color}">' + "".join(paths) + "</g>", x


def wordmark(color):
    body = f'<g transform="translate(-10 -4) scale(.31)">{mark(color)}</g>'
    x = 174
    for phrase, weight in (("dots", 640), (" on paper", 430)):
        paths, x = text_paths(phrase, weight, 92, x, 112, color)
        body += paths
    return svg(body, round(x + 24), 156, "Dots on Paper — Cool dot logo")


def main():
    BRAND.mkdir(exist_ok=True)
    files = {
        "icon-cool.svg": svg(mark(), 512, 512, "Cool dot — a heart with sunglasses"),
        "icon-cool-dark.svg": svg(mark(LIGHT), 512, 512, "Cool dot — light mark for dark backgrounds"),
        "logo-cool.svg": wordmark(INK),
        "logo-cool-dark.svg": wordmark(LIGHT),
    }
    for name, contents in files.items():
        (BRAND / name).write_text(contents, encoding="utf-8")
    brief = "Original minimal premium product logo for Dots on Paper. A softened heart-shaped Cool dot with sunglasses cut through the silhouette as clear negative space. Precise monochrome geometry, outlined lowercase Figtree wordmark, transparent background. Product-studio restraint; no Apple logo, no OpenAI trademark, no imitation knot. Preserve clear recognition at 32 pixels."
    (BRAND / "cool-logo.source.md").write_text(
        "# Cool-dot vector identity\n\n" + brief + "\n\n"
        "Source: `tools/build_cool_logo.py`. All shapes are original native vector geometry. "
        "The Figtree wordmark is outlined from `demo/assets/Figtree.ttf`, licensed under the SIL OFL. "
        "Original artwork is MIT-licensed. This is an independent community project.\n\n"
        "The light and dark variants use the same geometry. The SVG mask contains no external links, "
        "embedded image, script, or font dependency. Sunglasses remain transparent; use the appropriate "
        "foreground variant for the background.\n",
        encoding="utf-8",
    )
    (BRAND / "cool-logo.provenance.json").write_text(json.dumps({
        "creator": "Original vector artwork for Dots on Paper",
        "source": "tools/build_cool_logo.py",
        "brief": brief,
        "assets": list(files),
        "font": "Figtree, SIL Open Font License, outlined from demo/assets/Figtree.ttf",
        "license": "MIT for original artwork; SIL OFL for font",
        "affiliation": "Independent community project; no Apple or OpenAI trademark artwork",
    }, indent=2) + "\n", encoding="utf-8")
    print("Built four original Cool-dot vector logo assets and source provenance")


if __name__ == "__main__":
    main()
