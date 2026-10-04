# dots on paper

A standalone TRMNL X animation demo. Pick one of four plush dots: Artist in a beret, Curious with raised googly eyes, Bookish with round glasses, or Cool with a heart-shaped body and sunglasses. Your selected dot wakes up, thinks, and replies on paper. Playback stops on the result after 16 seconds. The demo accesses no assistant account or device; the surrounding package provides the MCP bridge.

## Open the demo

From this workspace:

```powershell
node demo/serve.mjs
```

Open <http://127.0.0.1:9024>. The server binds to loopback only. All fonts and imagery are stored locally. `index.html` also opens directly in a browser.

The preview includes a four-dot picker, play/pause, replay, a timeline, studio/screen views, smooth/stepped motion, and a multiline reply editor. Switching dots keeps the current reply, playback position, and view. Preset downloads follow the character. Edited replies save the actual studio or native-screen PNG. Reduced-motion preferences show the final reply with playback paused, including after editing.

## Shareable media

- `exports/dots-on-paper.mp4`: H.264, 1600×1200, about 16 seconds; thinks, then holds the reply.
- `exports/dots-on-paper.gif`: 960×720 preview that plays once and retains the final reply.
- `exports/poster.png`: 1600×1200 studio still.
- `exports/screen-1872x1404.png`: native-size screen still.

The other characters have MP4 films, GIFs, studio posters, and native screen stills with `-curious`, `-bookish`, or `-cool` before the file extension. All use native renderer snapshots and finish on the result.

The original films use the demonstration line “Good ideas deserve a little paper.” Edited text uses a reusable reply layout for paragraphs, bullet points, numbered lists, and headings. Long answers visibly truncate on the panel while the full text remains in the editor. Save a custom picture directly in the preview; export a new film with the capture harness.

### Calendar Chaos picture

Open <http://127.0.0.1:9024/?example=calendar-chaos> for the social-post example. Cool replies with an introduction, bullet points for the date with Paula tonight, breakfast with Amy tomorrow, and lunch with your wife, followed by “Your calendar needs a lawyer.” This is the same layout as any custom answer. The first frame shows the complete reply, paused; replay performs the animation. All four dots remain selectable.

`exports/calendar-chaos-poster-cool.png` is the 1600×1200 studio picture. `exports/calendar-chaos-screen-1872x1404-cool.png` is the native-size screen picture. Corresponding files with `artist`, `curious`, and `bookish` are included. The example's download controls follow the selected character and save these pictures.

The names, reminders, and punchline are fictional demo copy; they are not connected to a real calendar or dot. Prepared PNGs are bundled for all four characters. The campaign exporter below recreates the Cool reminder pictures and all four NOO variants.

### The NOO moment

Open <http://127.0.0.1:9024/?example=wife-noo>. A scripted assistant announces a wife-texting draft, the user interrupts with “NOO,” and the assistant confirms “Cancelled. Nothing sent.” Timed chat messages use a separate generic conversation renderer. The requested clean composition omits the extra footer labels; the draft status and cancellation stay in the conversation. There is no messaging tool or send action. All four characters have studio and native PNGs under `exports/wife-noo-*`.

The four-post X package, two H.264 films, and separate Instinct-inspired still are in `campaign/`. The two current dot films use actual snapshots from `src/dots_on_paper/render.py`, advanced every half second while thinking, then held on a settled result. Their GIFs play once and stop on the result. Recreate those media with `node demo/tools/export-campaign.mjs`, then `node demo/tools/export-github.mjs`. Verify the generic reply, conversation timeline, mobile editor, and reduced-motion behavior with `node demo/tools/verify-replies.mjs`. The package's [product facts](../docs/product-facts.md) distinguish supported dot behavior from scripted media and the unimplemented Instinct connector.

The TRMNL X proportions follow the local technology document and [official product specifications](https://shop.trmnl.com/products/trmnl-x). The interactive demo's smooth/stepped motion and the films' accelerated snapshot cadence are illustrative timing choices; a real display controls its own refresh speed.

## Recreate the media

With the local preview server running:

```powershell
node demo/tools/export-campaign.mjs
```

Install Playwright normally or set `DOTS_NODE_MODULES` to its node_modules directory. `DOTS_BROWSER` selects an H.264-capable browser; Microsoft Edge is preferred on Windows. The exporter also recognizes the desktop bundled runtime. It installs nothing automatically. `--skip-video` and `--only=reminders|noo|instinct|cast|characters` are available. Campaign files are written to `campaign/media/`; the four single-line character films and their stills go to `demo/exports/`. The GIF exporter rebuilds all six animations.

## Asset credits

- `assets/beret-dot.png`, `curious-dot.png`, `bookish-dot.png`, and `cool-dot.png`: generated with the built-in imagegen tool for this demo, inspired by the supplied plush-dot reference. Each exact generation prompt is saved beside its asset in a `.prompt.md` file. Facial expressions and eyewear are rendered separately by canvas; Curious's raised white eye globes are part of its plush asset.
- `assets/Figtree.ttf`: Figtree by Erik Kennedy, from the official Google Fonts repository. Its SIL Open Font License is included in `assets/Figtree-LICENSE.txt`.
- Hardware mockup, e-paper fibers, motion, typography, and compositing are authored in `demo.js`.
