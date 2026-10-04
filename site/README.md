# Public website

Source for [heinrihs.org/dotsonpaper](https://heinrihs.org/dotsonpaper/). This is a static showcase and setup guide. It never connects to a bridge, receives credentials, or calls an assistant.

Build after the repository’s normal Python setup:

```sh
python tools/build_site.py
```

Preview the built route:

```sh
python -m http.server 9027 --directory site/dist
```

Open http://127.0.0.1:9027/dotsonpaper/. The output lives in `site/dist/dotsonpaper/`. The build copies approved artwork and films, compresses the hero to WebP, and renders fictional thinking/result images with the same Python renderer as the bridge. The adjacent `build.json` records source and file hashes. Generated files are excluded from Git in this repository.

Production is served by the existing `heinrihs-s/heinrihs.org` static-site application in Coolify. Copy the complete output directory into that repository as `dotsonpaper/`; its Dockerfile copies the directory into the nginx document root. The existing site keeps its hostname and the new page occupies `/dotsonpaper/`. A slashless request redirects to the canonical directory URL. Rebuild and copy again when the page or its source assets change.

All links to full connection guides point to the public source repository. The animation is an accelerated preview and the physical/account verification limits are visible in the setup guides and questions.

Full conversation has three selectable turns: the draft, the user’s reply, and the dot’s response. Replay shows thinking and then the exchange; the last screen remains visible. The native renderer accepts optional `messages` entries with `role`, `content`, and `meta` for this showcase. The bridge’s public publishing tools still accept a single answer, so the conversation control is a website preview, not a live chat-history integration.

Watch the film opens the selected clip inline and begins playback. The retired `/dotsonpaper/assets/dot-noo.mp4` route is removed from the build and returns HTTP 410 in production. The new conversation clip uses `dot-conversation.mp4`. See [deployment](DEPLOYMENT.md) and [plugin distribution](../docs/publishing.md).
