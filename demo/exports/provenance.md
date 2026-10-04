# Export provenance

These media files are staged renders for the Dots on Paper demo. The character films, posters, and native screen images were rebuilt on 4 October 2026 using the bridge's native Python renderer.

`src/dots_on_paper/render.py` supplies the actual 1872 × 1404, 16-tone screen snapshots, including character expressions and reply typography. `demo.js` composes the studio/device mockup around those snapshots. The four plush bodies were generated with imagegen; each exact generation prompt is saved beside its sprite as `.prompt.md`. The typeface is self-hosted Figtree under its included SIL OFL license.

- `poster.png`: settled result in a 1600 × 1200 studio frame.
- `screen-1872x1404.png`: settled native result at 1872 × 1404.
- `dots-on-paper.mp4`: H.264 MP4 in a 24 fps container, about 16 seconds. Native thinking snapshots change every half second for six seconds; the reply is retained for the remaining ten seconds.
- `dots-on-paper.gif`: 960 × 720, 16 seconds, shared-palette GIF. It has no loop extension and leaves its final result visible.

Files with `-curious`, `-bookish`, or `-cool` before the extension use the same timeline with the corresponding character. Each MP4 and GIF has a `.provenance.json` file containing the renderer checksum, staged states, pose numbers, snapshot hashes, and final hold duration. MP4 exports are decoded in the browser to check their last frame against the rendered result.

The displayed reply is illustrative: “Good ideas deserve a little paper.” The half-second snapshot cadence is an accelerated preview, not a hardware refresh claim. No external message feed or physical device event is connected. `dot-reminders.mp4` and `dot-noo.mp4` are byte-identical copies of their campaign masters.
