# Connect your real dot

Dots on Paper exposes three MCP tools: `set_dot_status`, `publish_dot_reply`, and `get_dot_state`. Once connected, your dot can call them to send an answer to the bridge. The bridge stores the update and serves it to your configured displays.

The local bridge and stdio MCP adapter have passed the checks listed in [verification.md](verification.md). A real dot account has not yet been connected, and the complete dot-to-device path remains unverified. The commands below describe the connection to test; they are not a record of a completed account setup.

This is a tool integration. It does not subscribe to an undocumented ChatGPT reply webhook, scrape your chats, capture account history, or replace your dot with a separate API model. An accepted tool result confirms the bridge stored the update; the display still refreshes according to its platform and configuration.

## Local plugin

The package uses the portable Agent Plugins layout: root `plugin.json`, `mcp.json`, and `skills/`. The bundled server is a dependency-free Node.js stdio adapter. It forwards newline-delimited MCP JSON-RPC requests to the bridge's authenticated HTTP `/mcp` endpoint. It supports the bridge's MCP protocol versions `2025-11-25`, `2025-06-18`, and `2025-03-26`; responses use JSON and do not require an HTTP session.

Install Node.js 22 or later on the computer running this adapter. Run the bridge and initialize its credentials using the main [README](../README.md). The adapter reads `api_token` from `data/credentials.json` relative to its own installed location. A copied plugin must have access to a credentials file for the same bridge; an installed cache copy does not automatically find a source checkout's data file.

You can override the adapter configuration with environment variables:

| Variable | Purpose |
| --- | --- |
| `DOTS_BRIDGE_URL` | Bridge base URL, default `http://127.0.0.1:9035`. A reverse-proxy path is preserved; a URL already ending in `/mcp` is accepted. |
| `DOTS_API_TOKEN` | API bearer token. A nonempty value overrides the credentials file. |
| `DOTS_CONFIG_FILE` | Credentials file containing `api_token`; use an absolute path when the plugin runs from an installed cache. |

Keep tokens in the execution environment or the bridge's credentials file. Do not paste them into a chat, commit them to `mcp.json`, or include them in a distributable archive. The adapter sends credentials only to the configured bridge, rejects URL credentials and redirects, and reports errors without upstream response bodies or token values. Use HTTPS for a bridge outside your trusted local network.

The repository includes a catalog at [`.agents/plugins/marketplace.json`](../.agents/plugins/marketplace.json). Its `source.path` is `./`, relative to the marketplace's repository root, so it points to this package. In a client with the documented plugin CLI, add the source:

```sh
codex plugin marketplace add heinrihs-s/dots-on-paper --ref main
```

For a local checkout, use `codex plugin marketplace add .` from the package root. Restart the desktop app, choose **Dots on Paper** in the Plugins Directory, install it, and start a new conversation with it enabled. These steps follow OpenAI's [local plugin packaging guide](https://developers.openai.com/plugins/build/plugins); no public directory listing or registered ChatGPT app ID is included here.

The installed copy still needs `DOTS_CONFIG_FILE` pointing to the running bridge's private credentials file in its execution environment. The MCP entry uses `cwd: "./"` to resolve `./src/mcp-stdio.mjs` from the installed plugin root, but credentials are not copied with the public package. If your local client cannot supply that environment, use the direct MCP configuration below.

### Direct local MCP connection

For a local Codex host, add this to its private `~/.codex/config.toml`, replacing both paths with your actual checkout paths. This config contains a file path, not the token itself:

```toml
[mcp_servers.dots-on-paper]
command = "node"
args = ["C:/path/to/dots-on-paper/src/mcp-stdio.mjs"]
env = { DOTS_CONFIG_FILE = "C:/path/to/dots-on-paper/data/credentials.json", DOTS_BRIDGE_URL = "http://127.0.0.1:9035" }
```

On macOS or Linux, use absolute paths such as `/path/to/dots-on-paper/...`. If the plugin's bundled server is also enabled, disable that copy to avoid exposing the same tools twice. Local MCP server configuration is documented in OpenAI's [MCP guide](https://learn.chatgpt.com/docs/extend/mcp).

Local MCP configuration provides tools to the local host; it does not by itself connect the cloud dot to this computer. The dot connection below supplies that path.

### Have the dot work on your connected computer

In the ChatGPT desktop app, open the dot's profile and select **Computers > Your computer > Allow access**. Ask the dot to work in a local Work or Codex task with Dots on Paper enabled. Keep the computer online and the app open. OpenAI documents this [connected-computer route](https://learn.chatgpt.com/docs/dots/computers-and-apps), including the separate permission required for dot access.

This route lets a local task publish its answer. It does not add the local server to every cloud conversation or provide a feed of the dot's messages.

## Connect the cloud dot through a private tunnel

Use [OpenAI's Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) to reach the local stdio adapter. The adapter supplies the bridge token locally, while the tunnel connects outward to OpenAI.

Before running it:

- Create a tunnel in [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels), associate the target ChatGPT workspace, and obtain its `tunnel_id` and runtime API key.
- Check Platform permissions: **Tunnels Read + Manage** to create it, **Read + Use** to run or select it. ChatGPT developer mode requires separate account or workspace access.
- Install the full `tunnel-client` from the [official latest release](https://github.com/openai/tunnel-client/releases/latest), add it to PATH, and keep the bridge running. Windows AMD64 and ARM64 builds are available. Choose the full client, not the `tunnel-client-runtime` variant, because this setup uses `init` and `doctor`. On macOS, the [supported installation](https://github.com/openai/tunnel-client#install-with-homebrew) is `brew install openai/tools/tunnel-client`. The host needs outbound HTTPS to OpenAI.

Use a private directory outside this repository for the tunnel profile. Do not package its configuration with the plugin. The tunnel runtime key is separate from the bridge's `api_token`.

### Windows PowerShell

Open a second terminal at the package root. The first terminal should still be running `./run.ps1`. Capture absolute bridge paths before switching to the private profile directory:

```powershell
$env:DOTS_CONFIG_FILE = (Resolve-Path ./data/credentials.json).Path
$env:DOTS_BRIDGE_URL = 'http://127.0.0.1:9035'
$dotsAdapterPath = (Resolve-Path ./src/mcp-stdio.mjs).Path.Replace('\', '/')
$dotsMcpCommand = 'node "' + $dotsAdapterPath + '"'
$dotsTunnelDir = Join-Path $env:LOCALAPPDATA 'DotsOnPaper/tunnel'
New-Item -ItemType Directory -Force -Path $dotsTunnelDir | Out-Null
$env:TUNNEL_CLIENT_PROFILE_DIR = $dotsTunnelDir
Set-Location $dotsTunnelDir

$dotsRuntimeKey = Read-Host 'Tunnel runtime API key' -AsSecureString
$env:CONTROL_PLANE_API_KEY = [System.Net.NetworkCredential]::new('', $dotsRuntimeKey).Password
Remove-Variable dotsRuntimeKey
$dotsTunnelId = Read-Host 'Tunnel ID'

tunnel-client init --sample sample_mcp_stdio_local --profile dots-on-paper --tunnel-id $dotsTunnelId --mcp-command $dotsMcpCommand
tunnel-client doctor --profile dots-on-paper --explain
tunnel-client run --profile dots-on-paper
```

### macOS or Linux shell

From the package root in a second terminal:

```sh
export DOTS_CONFIG_FILE="$PWD/data/credentials.json"
export DOTS_BRIDGE_URL="http://127.0.0.1:9035"
dots_adapter="$PWD/src/mcp-stdio.mjs"
mkdir -p "$HOME/.local/state/dots-on-paper/tunnel"
export TUNNEL_CLIENT_PROFILE_DIR="$HOME/.local/state/dots-on-paper/tunnel"
cd "$HOME/.local/state/dots-on-paper/tunnel"
```

Set `CONTROL_PLANE_API_KEY` in this terminal using your password manager or a hidden prompt; do not write the key into the commands below. Replace the example tunnel ID:

```sh
tunnel-client init --sample sample_mcp_stdio_local --profile dots-on-paper --tunnel-id tunnel_REPLACE_WITH_YOURS --mcp-command "node \"$dots_adapter\""
tunnel-client doctor --profile dots-on-paper --explain
tunnel-client run --profile dots-on-paper
```

The `init`, `doctor`, and `run` commands follow the official tunnel guide with this package's stdio command substituted. `TUNNEL_CLIENT_PROFILE_DIR` selects the private profile location, as documented in the [client configuration reference](https://github.com/openai/tunnel-client/blob/master/docs/configuration.md). No tunnel-client binary is bundled. A live tunnel profile has not yet been tested with this project.

Run one active client per tunnel ID for this stdio route. Stop it before starting a replacement. For a persistent deployment, use the client's documented runtime supervision or a host service, and supply the same bridge variables and runtime key each time it starts.

### Add it to ChatGPT

Enable **Settings > Security and login > Developer mode**. Open **Plugins**, select the plus button, choose **Connection > Tunnel**, and select your tunnel or enter its ID. Review the three discovered tools. Keep both the bridge and tunnel client running. See OpenAI's [connect and test guide](https://developers.openai.com/plugins/deploy/connect-chatgpt).

If discovery fails, run `tunnel-client doctor --profile dots-on-paper --explain` again. If the tunnel is missing, check its ChatGPT workspace association and your permissions. New permission assignments can take up to 30 minutes to propagate.

### Public HTTPS hosting is separate work

The bridge's HTTP `/mcp` endpoint requires a static bearer token. ChatGPT cannot present custom API keys, so exposing this endpoint through HTTPS alone does **not** make it a compatible authenticated ChatGPT plugin. A public deployment needs an OAuth 2.1 gateway with MCP discovery and token validation, or those features implemented in the server. They are not included. OpenAI describes the requirements in its [authentication guide](https://developers.openai.com/plugins/build/auth).

Secure MCP Tunnel is for a private developer-mode connection. Public directory submission additionally requires a stable public endpoint and OpenAI's publication requirements. Publishing this repository on GitHub does not publish a plugin in that directory.

## Verify an actual answer

After connecting, enable the plugin for your dot and say:

> Use Dots on Paper for answers in this conversation. Set it to thinking when you start work. When you finish, send a short version of your actual answer to my private e-ink display. Keep sensitive source details in our chat.

The bundled `publish-dot-reply` skill supplies this workflow in local tasks. For a developer-mode connection that exposes only MCP tools, give the instruction directly to your dot.

Check the complete path in order:

1. Run `./run.ps1 -Doctor` on Windows, or `.venv/bin/python tools/doctor.py` elsewhere. The live checks must pass before account testing.
2. Ask the connected dot to call `get_dot_state`. Confirm that it returns the bridge state, rather than describing the demo.
3. Ask a real question and tell the dot to publish its answer. Inspect the `set_dot_status` and `publish_dot_reply` calls and their arguments.
4. Confirm the stored text in the bridge preview, then verify that the physical display fetched and showed it. An accepted tool call proves storage, not device refresh.
5. Repeat after a follow-up, a character change, and a bridge restart. Stop the tunnel briefly and check that a failed delivery is reported while the answer remains available in chat.

Connection success does not guarantee tool use on every reply. Test the prompts or responsibilities you plan to use before treating the display as an automatic delivery channel.

## Tool inputs

`publish_dot_reply` requires `text`. `set_dot_status` requires `status`, one of `idle`, `thinking`, or `error`. Both accept optional `character`, `dot_name`, `title`, `run_id`, `event_id`, and `mode`; omitted `character` and `mode` use the current bridge selections. `get_dot_state` reads the stored display state. The bridge is the source of the tools' schemas and validation, so the stdio adapter forwards tool discovery rather than maintaining a second copy.

Select `last_reply` for the answer alone or `full_conversation` for the supplied user and assistant turns. For a conversation, include the user's explicit `user_text` in the thinking call, then send the answer normally using the same run ID. Omit `user_text` on completion if it was already supplied. A standalone answer can include a user turn, or `publish_dot_reply` can replace history using a `messages` snapshot ending with an assistant turn identical to `text`. Use `user_text` or `messages`, not both. Only share turns the user wants on the display. [Examples and bounded history](api.md#display-modes)

Choose a fresh `run_id` for each task and use it for the status and answer to prevent stale completion updates. A completion that supplies `run_id` must match the current active thinking run; mismatches are rejected. A standalone answer without `run_id` is accepted, so one-off publishing does not require a preceding thinking update. Keep a stable `event_id` when retrying the same update. The tools expose deliberate display updates, not a full dot activity log. There is no bundled Codex completion hook pretending to observe direct dot conversations.

Thinking is caller-reported state. The beta expires an interrupted task after `DOTS_THINKING_TIMEOUT_SECONDS` (default 600), reports “No recent update,” and retains the last completed result. Late completion of an expired run is rejected. Restore the result in the preview or start a new task with a fresh run ID. Polling clients can miss short transitions. Animation defaults off; when enabled, it represents stored status rather than live internal activity.

## Official sources

- [Dots and connected plugins](https://learn.chatgpt.com/docs/dots/computers-and-apps)
- [Package a portable plugin](https://developers.openai.com/plugins/build/plugins)
- [Connect and test an MCP plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Secure MCP Tunnel setup](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
- [MCP authentication](https://developers.openai.com/plugins/build/auth)
- [Local MCP configuration](https://learn.chatgpt.com/docs/extend/mcp)

OpenAI's [MCP Events](https://developers.openai.com/plugins/build/mcp-events) feature sends events from your service to ChatGPT; it does not supply an outbound feed of dot replies. [OpenAI API response webhooks](https://developers.openai.com/api/docs/guides/webhooks) apply to API project responses, not consumer dot conversations.
