# Contributing

Dots on Paper accepts an assistant's deliberately published reply and serves it as an e-ink image. Improvements should keep that path simple: readable output, explicit publishing, and honest platform support. See [the README](README.md) for the implemented interfaces and [product facts](docs/product-facts.md) for the terminology used in demos.

## Local checks

Use Python 3.12 and Node.js 22. Install the Python package from this directory:

```sh
python -m pip install .
python tools/smoke.py
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_mcp.mjs
python -m compileall -q custom_components/dots_on_paper
```

The tests exercise the bridge, rendering, and MCP adapter. The configured CI matrix covers Python 3.11/3.12 on Linux and Windows with Node 22; hosted results become available after publication. It uses current official [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), and [setup-node](https://github.com/actions/setup-node) actions. Compiling the custom integration checks Python syntax; it does not test a running Home Assistant instance. A change to an HA entity or action should also include results from a real HA installation when available.

Run `tools/doctor.py --offline` with your installed Python environment for local runtime/assets/configuration checks. With the bridge running, omit `--offline` to check scoped authentication, image output, and MCP forwarding. See [setup.md](docs/setup.md) for the Windows launcher and configuration options. These diagnostics do not publish an answer.

`tools/smoke.py` uses temporary state to test the installed CLI from outside the checkout, with `PYTHONPATH` removed. It publishes a test answer through the real Node MCP adapter and checks image scope and restart persistence. It does not use production data. This detects missing installed assets that source-import tests can overlook.

For a renderer change, check a 296 × 128 monochrome frame, the 1872 × 1404 TRMNL X frame, and a portrait frame with a long answer. Keep the full reply in state even when the panel truncates it. For a new device example, name the actual driver, dimensions, refresh behavior, and whether you tried it on hardware.

## Rebuild the demo and artwork

Install optional pinned development dependencies with `npm ci`. They are not
needed for the runtime MCP adapter. Start `node demo/serve.mjs`, then run
`npm run media:gifs` or `npm run media:export`. The GIF exporter prefers the
checkout's Python environment; `DOTS_PYTHON` can select another Python with Pillow.
Use an H.264-capable browser for the MP4 exports. On Windows, installed Edge is
selected automatically; `DOTS_BROWSER` can override its executable.

The original logo and GitHub cover have their own [source and rebuild guide](brand/README.md).
Run `npm run media:verify` after regenerating campaign media to verify dimensions,
loops, source hashes, provenance, and caption lengths.

## Pull requests

Describe the problem, the resulting behavior, and the checks you ran. Include a screenshot for a visible change. Include the relevant primary platform documentation for an adapter change. Keep staged marketing dialogue out of live state, and do not make unsupported claims about ChatGPT channels or automatic dot events.

Use generated test credentials. Do not commit a credentials file, database, `.env`, real conversation, or private display URL. Report a security issue using [SECURITY.md](SECURITY.md).

Source code is under [MIT](LICENSE). Retain the separate Figtree license and the asset provenance in [NOTICE.md](NOTICE.md) when redistributing assets. This is an independent project; platform names identify the supported interfaces.
