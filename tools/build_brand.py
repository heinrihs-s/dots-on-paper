"""Build the original outlined wordmark. Optional design dependency: fonttools.

    python -m pip install fonttools
    python tools/build_brand.py

The application does not need fonttools. Committed SVGs contain paths, not fonts.
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
INK = "#1d2925"
PAPER = "#f2f3ed"


def mark(ink=INK, paper=PAPER):
    # A folded sheet holds four dots; the rightmost dot is the little star.
    return f'''<path d="M96 56H324L424 156V444Q424 456 412 456H96Q84 456 84 444V68Q84 56 96 56Z" fill="{paper}" stroke="{ink}" stroke-width="18" stroke-linejoin="round"/>
<path d="M324 56V144Q324 156 336 156H424" fill="none" stroke="{ink}" stroke-width="18" stroke-linejoin="round"/>
<g fill="{ink}"><circle cx="156" cy="258" r="34"/><circle cx="244" cy="198" r="34"/><circle cx="244" cy="318" r="34"/><circle cx="332" cy="258" r="34"/></g>
<g fill="{paper}"><rect x="319" y="250" width="7" height="16" rx="3.5"/><rect x="337" y="250" width="7" height="16" rx="3.5"/></g>'''


def svg(body, width, height, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{title}</title>{body}</svg>\n'''


def text_paths(text, weight, size, x, baseline, color=INK):
    font = instantiateVariableFont(TTFont(ROOT / "demo/assets/Figtree.ttf"), {"wght": weight})
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


def wordmark(color=INK, paper=PAPER):
    body = f'<g transform="translate(-16 4) scale(.33)">{mark(color, paper)}</g>'
    x = 165
    for phrase, weight in (("dots", 720), (" on paper", 430)):
        paths, x = text_paths(phrase, weight, 100, x, 121, color)
        body += paths
    return svg(body, round(x + 24), 176, "Dots on Paper")


def main():
    BRAND.mkdir(exist_ok=True)
    (BRAND / "icon.svg").write_text(svg(mark(), 512, 512, "Dots on Paper: four dots on a folded sheet"), encoding="utf-8")
    (BRAND / "icon-dark.svg").write_text(svg(mark(PAPER, INK), 512, 512, "Dots on Paper, dark background icon"), encoding="utf-8")
    (BRAND / "logo.svg").write_text(wordmark(), encoding="utf-8")
    (BRAND / "logo-dark.svg").write_text(wordmark(PAPER, INK), encoding="utf-8")
    (BRAND / "provenance.json").write_text(json.dumps({
        "creator": "Original vector artwork for Dots on Paper",
        "source": "tools/build_brand.py",
        "brief": "Four dots on a folded sheet. Mineral-green studio, charcoal ink, cool paper. One tiny dot has eyes. Crisp geometry that survives monochrome e-ink and small icons.",
        "font": "Figtree, SIL Open Font License, outlined from demo/assets/Figtree.ttf",
        "license": "MIT for original artwork; SIL OFL for the font",
        "affiliation": "Independent community project; not an OpenAI, Instinct, Home Assistant, or TRMNL logo",
    }, indent=2) + "\n", encoding="utf-8")
    print("Built four self-contained vector brand assets")


if __name__ == "__main__":
    main()
