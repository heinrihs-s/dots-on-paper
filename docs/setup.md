# Run Dots on Paper

Run these commands from the repository root. Python 3.11 or later runs the bridge and renderer; Node.js 22 or later runs the MCP adapter and standalone demo. Use `python3` where your system does not provide the `python` command.

## First run

```sh
python tools/setup.py
```

Setup creates the repository's `.venv`, installs this Python package and Pillow, and initializes `data/credentials.json`. It leaves existing keys in place and does not print them. Installing dependencies requires access to the Python package index. Setup does not connect an account or configure display firmware.

Start the bridge on Windows:

```powershell
.\run.ps1
```

Start it on macOS/Linux:

```sh
.venv/bin/python -m dots_on_paper --data-dir ./data
```

Open **http://127.0.0.1:9035**. Select `data/credentials.json` in the browser connection panel to preview bridge state. The file is read in your browser; the publishing key stays in page memory. The initial state is **Waiting for your dot**. A staged animation is available separately using `node demo/serve.mjs` on port 9024.

The data directory holds private credentials and SQLite state. It is excluded from Git and distributable archives. The publishing key can read and update state; the separate image key can only fetch rendered images. Use the image key for hardware clients.

## Last reply or Full conversation

Use the bridge preview's display mode control, Home Assistant's Display mode select, or `PATCH /api/settings` with `{"mode":"full_conversation"}`. The default is `last_reply`; switching changes the rendered screen and preserves the stored messages.

Full conversation needs explicit turns from your assistant or automation. Supply `user_text` with a thinking update, then publish the assistant's answer, or send an answer with a `messages` snapshot. The bridge retains at most 20 turns and 24000 characters. It does not connect to a chat account to fetch history. [Request examples and limits](api.md#display-modes)

## Check the installation

On Windows:

```powershell
.\run.ps1 -Doctor
```

On macOS/Linux:

```sh
.venv/bin/python tools/doctor.py
```

The doctor checks the runtime, assets, bridge authentication, MCP tools, and rendered image. It reads state without publishing an answer. Before starting the bridge, use `--offline` to check installation files and private configuration. On Windows, the equivalent is `.\run.ps1 -Doctor -Offline`. Use `--url` for another bridge address and `--config` for that bridge's credentials file. The results distinguish a locally functioning bridge from a connected dot or refreshed hardware; those last two still need separate verification.

For an isolated installed-package check after setup, run `.\.venv\Scripts\python.exe tools\smoke.py` on Windows or `.venv/bin/python tools/smoke.py` on macOS/Linux. It starts the installed CLI outside the source checkout with temporary data, exercises real MCP publishing and image authentication, then verifies persistence after restart. It does not use production keys or replace your display's state.

## Installed package and credentials

To inspect a setup failure, create the environment manually with `python -m venv .venv`. On Windows, run `.\.venv\Scripts\python.exe -m pip install .`; on macOS/Linux use `.venv/bin/python -m pip install .`. Then use that same interpreter with `-m dots_on_paper --init --data-dir ./data` to initialize keys and `-m dots_on_paper --data-dir ./data` to start. Retain private index URLs or keys outside shared logs when asking for help.

For an existing managed Python environment, `python -m pip install .` and the same module commands work without creating another virtual environment. Use the same Python environment for installation and launch.

A source checkout keeps its state under `data/`. An installed wheel defaults to `%LOCALAPPDATA%\dots-on-paper` on Windows or `~/.local/share/dots-on-paper` elsewhere. `DOTS_DATA_DIR` and `DOTS_CONFIG_FILE` override these paths.

An MCP plugin installed into an app cache must use `DOTS_CONFIG_FILE` pointing to the **running bridge's** credentials file, or `DOTS_API_TOKEN` in its execution environment. Initializing unrelated keys in the cache will not authenticate against an existing bridge. The [real-dot guide](real-dot.md) covers the local adapter and cloud connection.

## Reach the bridge from HA or a display

`localhost` on Home Assistant or another device refers to that machine, not this bridge. Use the bridge computer's reachable LAN address, for example `http://192.168.1.20:9035`. Configure these environment variables before starting the Python server:

| Setting | Example | Purpose |
| --- | --- | --- |
| `DOTS_HOST` | `0.0.0.0` | Bind a listener reachable on the LAN. |
| `DOTS_PUBLIC_URL` | `http://192.168.1.20:9035` | Address returned to hardware clients. |
| `DOTS_ALLOWED_HOSTS` | `192.168.1.20,localhost,127.0.0.1` | Accepted request hostnames/IPs. |

Choose your actual address, and permit the port in the host firewall if needed. The Python launcher reads environment variables rather than `.env` files. `.env.example` supplies optional Compose settings. Use a trusted private network or an authenticated connection with HTTPS for remote access.

## Docker

```sh
docker compose run --rm bridge python -m dots_on_paper --init
docker compose up -d --build
```

Keys and state live in the `dots-data` volume. Compose defaults to a loopback host port. LAN clients require a reachable host port bind and matching `DOTS_PUBLIC_URL`/`DOTS_ALLOWED_HOSTS` values. Docker deployment still needs verification on your host.

If a local MCP client needs the Docker bridge's credentials, copy that same file into a private local path:

```sh
docker compose cp bridge:/data/credentials.json ./docker-credentials.json
```

Point `DOTS_CONFIG_FILE` at the copied file. HA uses its publishing key; devices use its image key.

## Common connection failures

| Symptom | Check |
| --- | --- |
| Python cannot import Pillow or the package | Run setup, then launch with the repository `.venv` interpreter or `run.ps1`. |
| Doctor cannot reach the bridge | Start the bridge first; confirm its URL and port. Use `--offline` for a file-only check. |
| 401 from API or MCP | Use credentials belonging to the running bridge, not a separately initialized copy. |
| Device can reach HA but not this image | Use a LAN-reachable bridge URL, allowed host, firewall rule, and read-only image key. |
| Dot cannot see localhost | Use Secure MCP Tunnel to the local stdio adapter, or a connected-computer task, as described in the real-dot guide. The bridge's static bearer key is not a direct ChatGPT HTTPS connection. |
| Display stays on thinking after work stops | Ask the connected assistant to call `set_dot_status` with `status: "idle"`. Thinking is reported by the caller and has no automatic expiry; starting the next request with a fresh `run_id` also replaces it. |
| Bridge has an answer; screen has not changed | Check the device's next fetch and refresh. A stored reply alone does not confirm physical delivery. |

For key rotation and private-data handling, see [SECURITY.md](../SECURITY.md).
