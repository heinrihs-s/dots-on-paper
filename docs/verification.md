# Release verification

## Engineering beta, 5 October 2026

Version `0.2.0b1` was installed in the existing Windows environment: Python 3.12.14, Pillow 12.3.0 and Node 24.11.0. The final source passed **86 Python tests and 15 Node MCP tests**. The installed runtime fingerprint is `35e4fa914fc9` (prefix). The doctor also correctly rejected a stale installed build during development even though its version matched.

New reliability checks cover absolute thinking deadlines, restart/timeout recovery, late and superseded runs, duplicate/reconnected events, retained timestamps, restore, deliberate display/history clearing, and single-use same-origin pairing. Delivery checks exercise persisted pending uploads, coalescing, failure/restart recovery, hourly quotas, Retry-After, permanent failures, raw PNG HTTP transport, refused redirects and the 1 MB limit. Requests use disposable local services, not a stock account or panel.

The final desktop (1440 px) and phone (390 px) browser pass checked guided test/source separation, generated installed-adapter configuration with an actual stdio publication, readable transcripts, restore and clearing. The public build's editable simulation checked all characters, a real 1872×1404 PNG download, safe sample replacement, no personal text in requests/storage/URLs, a visible simulation label on phones, reduced motion and contained horizontal scrolling. There were no browser script errors. Two bounded visual rounds covered the initial implementation and the final fixes.

The exact wheel and runtime archive are exercised by `tools/release_check.py`, including a previous 0.1.0 wheel upgrade that preserves keys and retained state. Source checks additionally run Linux/Windows × Python 3.11/3.12, exact-artifact setup on both OSes and native amd64/arm64 container persistence checks. Hosted run and publication results are recorded separately after they complete; a workflow definition alone is not verification.

The compatibility matrix, first-result guide, three recipes, hardware issue form, five contributor tasks and study form are in the beta. GitHub About points to the public website; Discussions has Show your desk, Setup help and Recipes. The [roadmap](roadmap.md) keeps interactive assistant reproduction, a physical model/firmware run, stock account access, live HA/HACS, ten observed users, seven-day retention and promotion open. These gates are not established by the software tests.

## Historical checks

Local checks on **3 October 2026** for version 0.1.0:

| Check | Evidence |
| --- | --- |
| Python bridge and renderer | 37 tests passed against the real HTTP server, SQLite, Pillow output, and Node MCP adapter. |
| Node MCP adapter | 14 tests passed, including handshake, actual forwarding, scoped credentials, and error redaction. |
| Fresh installation | `tools/setup.py` completed online from an empty repository `.venv`; package and Pillow installed, existing checkout keys were neither replaced nor printed. The 37 Python and 14 Node tests passed in that installed environment. |
| Installed-package cold start | `tools/smoke.py` passed from an external temporary working directory with `PYTHONPATH` removed: fresh/idempotent keys, actual Node MCP thinking → answer, 1872 × 1404 / 16-gray and 296 × 128 / 2-gray PNGs, image-key scope, and equal state after SQLite/process restart. Production data was not used. |
| Installation doctor | Offline doctor passed using the repository `.venv`. Live doctor passed all 10 checks, including authenticated HTTP state/image, HTTP MCP tools, and Node stdio adapter discovery. Its Windows JSON output was fixed for the local console encoding. |
| Generic browser reply | Paragraphs, five bullets, numbered items including 10/11, Unicode, long words, and a 4000-character answer checked. Long output visibly ellipsizes; full text stays in the editor. |
| Browser controls | All four characters, actual custom PNG downloads, mobile editor at 390 px, no horizontal overflow, and reduced-motion editing checked. |
| Conversation | Thinking, draft, NOO, and cancellation frames checked. Extra footer labels were removed at the user's request; the draft status and cancellation remain in the conversation. |
| Independent finish review | A numeric-marker spacing issue was fixed with a measured shared gutter. Confirmation found no remaining blocking UI/UX issue. |
| Live bridge preview | Authenticated browser connected to the local bridge, all four selectors and image profile dimensions checked. No private key remained in the visible token field. |
| Media | Both MP4s decoded as H.264/avc1, 1600 × 1200, approximately 16 seconds. Both GIFs are 960 × 720, 16-second infinite loops with readable first frames; every frame, dimensions, timing, and embedded provenance checked. PNG dimensions and provenance checked. See the campaign manifest and adjacent MP4 provenance JSON. |
| Docker configuration | Compose configuration validation passed. The local Docker daemon was unavailable, so no image build or container runtime was verified. |
| Distribution | Python wheel rebuilt without downloading dependencies. Source and manual HA archives are generated by `tools/package.py` with ZIP integrity checks and exclusions for local data, credentials, environment files, caches, and Git metadata. |

The [GitHub-hosted source checks](https://github.com/heinrihs-s/dots-on-paper/actions/runs/37153148253) passed for commit `cc8cadeb3281788930732b044d41a57c29d773cf` on 3 October 2026. That run uses the Linux/Windows × Python 3.11/3.12 matrix, with Node 22, and includes the installed-package smoke test.

Follow-up checks on **4 October 2026**: the rebuilt and reinstalled wheel passed 38 Python tests, 14 Node tests, and the installed-package smoke check. The added regression executes the served preview's refresh script against a temporary real HTTP/SQLite/renderer bridge at both 5- and 37-second intervals. It checks timing boundaries, thinking loops, answer settling, and image reuse, confirming the preview now follows `DOTS_FRAME_SECONDS`.

The connection audit checked the current official dot, plugin, authentication, and Secure MCP Tunnel documentation. Both plugin JSON files passed their published schemas; the new marketplace catalog resolves to the root package. The installed Codex CLI supports the documented marketplace command. The private MCP TOML and PowerShell setup blocks passed syntax checks, and the Windows command uses forward slashes to match the tunnel client's parser. These are setup checks, not a live tunnel or account connection.

The **thinking → held result update on 4 October 2026** passed 50 Python tests and 14 Node tests against the rebuilt, reinstalled package. The installed-package smoke check also passed. New checks exercise successive authenticated TRMNL polls, the required JSON `status: 0`, thinking/idle sleep intervals, the read-only display metadata, and unchanged answer pixels and ETags across later requests. The browser preview selects the settled answer immediately and follows reduced-motion preferences.

Nine of the Python tests exercise the Home Assistant image entity's timer, cache, slow and concurrent downloads, completion during a fetch, unavailable state, and unload lifecycle. These use isolated HA interfaces rather than a running Home Assistant installation. The exact ESPHome fragment passed configuration/schema validation with ESPHome 2026.9.1 in a temporary full board configuration with fake secrets. This checks its actions and configuration; no firmware was compiled or flashed.

All six published MP4s and their six GIF counterparts now use the bridge's native renderer for the screen. The reminder and character films hold their completed result for ten seconds; the NOO film holds its cancellation for seven seconds. The GIFs play once and retain their last frame. Export checks decode the start and end of the result hold, compare them with the renderer output, and record timing and checksums in the adjacent provenance files. The accelerated film cadence does not establish a physical panel's refresh performance.

These checks do not verify a physical TRMNL/e-paper panel, live Home Assistant runtime, private ChatGPT dot connection, Instinct integration, or Docker deployment. Those remain installation checks. No live account, external messaging, or calendar is used in the campaign. The bridge's three MCP tools publish/read display state; they contain no messaging sender.

Reproduce source checks from the repository root:

```sh
python -m pip install .
python tools/smoke.py
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_mcp.mjs
python -m compileall -q custom_components/dots_on_paper
```

With the standalone preview running, `node demo/tools/verify-replies.mjs` performs the browser reply checks. `node demo/tools/export-campaign.mjs` recreates campaign media with Playwright and an H.264-capable browser. `DOTS_BROWSER` selects the export browser; `DOTS_BROWSER_PATH` selects the verification browser. Renderer and source checks require no live account credentials.

The manifest records per-file checksums; locally built release packages have `release/SHA256SUMS.txt`. The source repository is [heinrihs-s/dots-on-paper](https://github.com/heinrihs-s/dots-on-paper). GitHub-hosted CI reports separately from these local checks. Tagged release downloads and HACS registration are not included in the source push; account and hardware verification remain as described above.
