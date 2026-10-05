# Your first retained result

Start with a local browser. A display and cloud account are optional. Python 3.11+ runs the bridge; Node.js 22+ is needed when you connect the stdio MCP adapter.

1. Download and extract the [beta runtime](https://github.com/heinrihs-s/dots-on-paper/releases/tag/v0.2.0-beta.1), or clone this repository. Run `python tools/setup.py` in its root.
2. On Windows run `.\run.ps1`. On macOS/Linux run `.venv/bin/python -m dots_on_paper --data-dir ./data --open`. The launcher opens a paired browser. If a browser cannot be opened, use the manual credentials-file connection at http://127.0.0.1:9035.
3. Enter a short note and select **Send test card**. It uses the bridge's real renderer and persistent state. **Local note rendered** proves that path, independently of an assistant.
4. Open **Connect your assistant**, then **Generate MCP configuration**. The JSON contains the installed Node adapter's absolute path and a reference to the same private credentials file. Copy it into a JSON-compatible local MCP client. For Codex's configuration format and the existing portable plugin, follow [the local connection guide](real-dot.md#direct-local-mcp-connection).
5. Start a fresh client conversation. Ask it to call `get_dot_state`, then complete a small real task and call `publish_dot_reply` with a short, useful summary. The **MCP publication received** check records that an explicit tool update reached this bridge. It does not establish automatic observation of every reply.
6. Read the result in the preview. Expand **Read the full result** when a panel-sized summary omits text. Leave the browser running, or choose a [hardware route](platforms.md). Send a test card after configuring that route.

The generated configuration contains no publishing key. Keep its referenced private file on the same computer. A container's internal adapter/file paths cannot be used directly by a host client: use the existing checkout adapter and [Docker credentials procedure](setup.md#docker).

Source and display checks are separate. A stored tool result proves publishing. A fetched image or accepted upload proves a transport receipt. The named panel must still be observed. Record model, firmware, refresh settings and measured latency in the [hardware verification form](https://github.com/heinrihs-s/dots-on-paper/issues/new?template=hardware.yml).

After an interruption, **No recent update** appears after `DOTS_THINKING_TIMEOUT_SECONDS` (default 600). The last completed result remains stored and appears on the retained-result recovery card. **Restore last result** recovers it; begin a new task with a fresh run ID.

**Clear display** leaves retained information available for restoration. **Clear stored history** deliberately removes the current text, last completed result, supplied turns and pending content upload. A configured cloud route receives a clear card subject to its quota and refresh schedule; copies already stored by a cloud service follow that service's retention policy.

The ten-minute first-result and thirty-minute hardware goals are beta study targets. They have not yet been measured with ten independent users. [Study protocol](beta-study.md)
