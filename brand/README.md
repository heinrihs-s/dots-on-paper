# Dots on Paper artwork

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
