# Campaign media

These images and films are scripted, fictional demos. The “NOO” scene uses a draft, an interruption, and “Cancelled. Nothing sent.” No calendar was accessed and no message was sent. The Instinct image is an **Instinct-inspired concept with scripted output and no connector**; those labels are also visible inside the picture.

The two dot films use the bridge's native 16-tone PNG renderer. The device frame and studio background are composed by the demo canvas. Each film advances explicit thinking snapshots at an accelerated half-second interval, then holds a settled result. The reminder result holds for ten seconds; the NOO cancellation holds for seven seconds. These are renderer previews, not recordings of a physical panel's refresh behavior.

To regenerate:

```powershell
node demo/serve.mjs
# In another terminal, from the repository root:
node demo/tools/export-campaign.mjs
node demo/tools/export-github.mjs
.venv/Scripts/python.exe tools/finalize_campaign.py
```

The exporter needs Python with Pillow; it uses the checkout's `.venv` or `DOTS_PYTHON`. It loads a normal Playwright installation first, then the desktop bundled Node runtime. Set `DOTS_NODE_MODULES` to another `node_modules` directory if necessary. `DOTS_BROWSER` selects the browser executable; installed Microsoft Edge is the Windows default because its MediaRecorder produces usable H.264 MP4s. Set `DOTS_DEMO_PORT` before starting the server and `DOTS_DEMO_URL` for the exporters if another port is needed. On macOS/Linux, use `.venv/bin/python` for the verification command.

Use `--skip-video` to regenerate just the pictures. Use `--only=reminders`, `--only=noo`, `--only=instinct`, `--only=cast`, or `--only=characters` to select one group. The cast group rebuilds all four “NOO” poster/native pairs under `demo/exports`. The characters group rebuilds each character's single-line film and final still. In the original TRMNL development workspace, the same commands use `dots-demo/` instead of `demo/`.

Films are 1600 × 1200, approximately 16 seconds, in a 24 fps H.264 MP4 container. Native screen images are 1872 × 1404. The exporter decodes frames near the start and end of each result hold and checks that they match the rendered result. GIFs are 960 × 720 and play once, leaving their final frame visible. Each PNG contains an uncompressed `dots:provenance` iTXt record. MP4 and GIF provenance includes the native renderer checksum, staged states, pose numbers, snapshot hashes, timeline, and result hold duration. No live account or device is used.
