# Dots on Paper artwork

The current header is `header-paper-v2.png`: four colourful, matte paper-pulp
companions in blue, green, yellow and pink, led by Cool. Fine cellulose fibers
and dry pigment give the scene its e-ink paper character. It is generated with
the built-in image tool; the exact brief is in `header-paper-v2.prompt.md` and
output provenance is adjacent. The previous silver-white studio version remains
available as `header-cool-v1.png`.

The matching independent vector family is `logo-cool.svg`,
`logo-cool-dark.svg`, `icon-cool.svg`, and `icon-cool-dark.svg`. It uses a
softened heart and sunglasses as clear negative space, with outlined Figtree
lettering. Source and licensing are in `cool-logo.source.md`; rebuild with
`tools/build_cool_logo.py`. These are the premium companion assets used with
the GitHub header. The folded-sheet family below remains available.

Four dots on a folded sheet. The rightmost dot has eyes: one little protagonist,
three companions, all on paper. The mark remains legible without color.

- `logo.svg` / `logo-dark.svg`: original outlined Figtree wordmark; no font download needed.
- `icon.svg` / `icon-dark.svg`: square vector mark with a transparent outer background.
- `icon.png`: 512-pixel transparent icon.
- `social-preview.png`: 1280 × 640 GitHub preview, with the calendar scene and punchline.
- `social-preview.html`: editable source composition, using the project's local font and real rendered demo.

Original vector art is MIT licensed. Figtree uses its included SIL Open Font
License. This is an independent project's identity, with no official endorsement.
`provenance.json` records the source and brief; rendered PNGs include their source
and sidecar provenance.

To rebuild vector paths, install the optional `fonttools` design dependency and
run `python tools/build_brand.py`. Install the pinned development tools with
`npm ci`, then render the PNGs with `node tools/build-brand.mjs`. These packages
are needed only to rebuild marketing art; the bridge needs Python and Pillow.
On macOS/Linux, first install the development browser with
`npx playwright install chromium`. On Windows, the renderer uses installed
Microsoft Edge. `DOTS_BROWSER` can specify another installed browser executable.
