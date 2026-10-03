# Connect your real dot

Dots on Paper publishes real replies through three MCP tools: `set_dot_status`, `publish_dot_reply`, and `get_dot_state`. Your dot calls the tools after you enable display updates for a conversation or responsibility. The bridge stores the latest state and exposes it to your configured displays.

This is a tool integration. It does not subscribe to an undocumented ChatGPT reply webhook, scrape your chats, stream the full conversation, or replace your dot with a separate API model. An accepted tool result confirms the bridge stored the update; the display still refreshes according to its platform and configuration.

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

Install the package through a local or repository plugin marketplace supported by your desktop client. The MCP entry uses `cwd: "./"` so `./src/mcp-stdio.mjs` resolves from the plugin root. No registered ChatGPT app ID is fabricated in this package. For a direct local Codex connection, add a stdio MCP server that launches `node` with the absolute path to `src/mcp-stdio.mjs`, and forward the applicable environment variables. Start a new conversation after enabling the plugin.

Local MCP configuration provides tools to the local host; it does not by itself connect the cloud dot to this computer. The dot connection below supplies that path.

## Connect the cloud dot

Official OpenAI documentation says dots can use installed, enabled plugins with the connected account's permissions. A private display bridge needs a reachable MCP connection. Use one of these documented routes:

1. **Private developer-mode connection:** run OpenAI's Secure MCP Tunnel client on a host that can reach the bridge. Point it at the Node stdio adapter, which supplies bridge authentication. Create a tunnel in Platform settings and configure the tunnel client with its identity and runtime API key. In ChatGPT, enable developer mode, go to Plugins, add a connection, and select **Tunnel**. Tunnel and developer-mode access depend on the account and workspace. Keep the client running while the dot uses the display.
2. **Remote HTTPS connection:** operate a stable HTTPS MCP endpoint or an authenticated HTTPS proxy to the bridge, then add its `/mcp` URL in ChatGPT developer mode. The bridge requires a bearer token for all `/mcp` POST requests. A public multiuser plugin additionally needs the authentication, authorization, domain verification, and review setup required by OpenAI; this local package does not implement OAuth or provision public hosting.

The local adapter is useful behind a Secure MCP Tunnel because it reads the bridge token locally. Secure MCP Tunnel is a private testing/connection route, not a substitute for the public endpoint required for public plugin submission. Follow the official setup guide for your account rather than treating localhost as reachable from ChatGPT.

After connecting, enable the plugin for your dot and say:

> Use Dots on Paper for answers in this conversation. Set it to thinking when you start work. When you finish, send a short version of your actual answer to my private e-ink display. Keep sensitive source details in our chat.

The bundled `publish-dot-reply` skill supplies this publishing workflow. For a developer-mode MCP connection where only the tools are connected, give the workflow instruction directly to your dot. Ask the dot to call `get_dot_state`, then answer a real question and verify its `publish_dot_reply` call. Confirm the rendered output separately on the device. Authentication or connection success does not prove that the model will invoke the publishing tool on every future reply.

## Tool inputs

`publish_dot_reply` requires `text`. `set_dot_status` requires `status`, one of `idle`, `thinking`, or `error`. Both accept optional `character`, `dot_name`, `title`, `run_id`, and `event_id`; omitted `character` uses the current bridge selection. `get_dot_state` reads the stored display state. The bridge is the source of the tools' schemas and validation, so the stdio adapter forwards tool discovery rather than maintaining a second copy.

Choose a fresh `run_id` for each task and use it for the status and answer to prevent stale completion updates. A completion that supplies `run_id` must match the current active thinking run; mismatches are rejected. A standalone answer without `run_id` is accepted, so one-off publishing does not require a preceding thinking update. Keep a stable `event_id` when retrying the same update. The tools expose deliberate display updates, not a full dot activity log. There is no bundled Codex completion hook pretending to observe direct dot conversations.

## Official sources

- [Dots and connected plugins](https://learn.chatgpt.com/docs/dots/computers-and-apps)
- [Package a portable plugin](https://developers.openai.com/plugins/build/plugins)
- [Connect and test an MCP plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- [Secure MCP Tunnel setup](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

OpenAI's [MCP Events](https://developers.openai.com/plugins/build/mcp-events) feature sends events from your service to ChatGPT; it does not supply an outbound feed of dot replies. [OpenAI API response webhooks](https://developers.openai.com/api/docs/guides/webhooks) apply to API project responses, not consumer dot conversations.
