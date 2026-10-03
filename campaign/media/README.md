# Campaign media

These images and films are scripted, fictional demos. The “NOO” scene uses a draft, an interruption, and “Cancelled. Nothing sent.” No calendar was accessed and no message was sent. The Instinct image is an **Instinct-inspired concept with scripted output and no connector**; those labels are also visible inside the picture.

To regenerate from the local canvas renderer:

```powershell
node demo/serve.mjs
# In another terminal, from the repository root:
node demo/tools/export-campaign.mjs
```

The exporter loads a normal Playwright installation first, then the desktop bundled Node runtime. Set `DOTS_NODE_MODULES` to another `node_modules` directory if necessary. `DOTS_BROWSER` selects the browser executable; installed Microsoft Edge is the Windows default because its MediaRecorder produces usable H.264 MP4s. Set `DOTS_DEMO_URL` if the demo server uses another port.

Use `--skip-video` to regenerate just the pictures. Use `--only=reminders`, `--only=noo`, `--only=instinct`, or `--only=cast` to select one group. The cast group rebuilds all four “NOO” poster/native pairs under `demo/exports`. In the original TRMNL development workspace, the same commands use `dots-demo/` instead of `demo/`.

Films are 1600 × 1200, approximately 16 seconds, H.264 MP4, recorded at a requested 24 fps. Native images are 1872 × 1404. The exporter checks nonempty H.264 output and browser-decoded dimensions/duration. Each PNG contains an uncompressed `dots:provenance` iTXt record with fictional-content provenance and its mascot source/prompt. MP4 provenance is stored alongside each film in `.provenance.json`.
