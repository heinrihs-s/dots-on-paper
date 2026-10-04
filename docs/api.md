# Publishing and image API

The publishing key authorizes state reads, updates, and MCP requests. The separate image key authorizes PNG/BMP and display-metadata reads. Keep keys in the client environment or private credentials file. The bridge does not call a model API; the optional Secure MCP Tunnel connection requires its own Platform runtime key.

## Endpoints

| Endpoint | Authentication | Result |
| --- | --- | --- |
| `GET /api/health` | Public | Minimal health/version, without reply or credentials. |
| `GET /api/state` | Publishing bearer key | Latest flat state. |
| `GET /api/profiles` | Publishing bearer key | Named render profiles. |
| `POST /api/events` | Publishing bearer key | Store a deliberate display update. |
| `PATCH /api/settings` | Publishing bearer key | Change `character`, preserving the reply/event ID. |
| `POST /mcp` | Publishing bearer key | MCP JSON-RPC tools. |
| `GET /image.png`, `GET /image.bmp` | Image or publishing bearer key; URL `key` accepts image key only | Rendered screen. |
| `GET /api/display-state` | Image or publishing bearer key; URL `key` accepts image key only | Status, revision, animation frame and polling hints, without reply text or credentials. |
| `GET /api/display` | Enrolled TRMNL `ID` and `Access-Token` headers | Pinned frame URL, filename cache key and next sleep interval; JSON `status: 0`. |

## Publish an answer

```json
{
  "status": "answer",
  "dot_name": "heidot",
  "title": "heidot replied",
  "text": "The actual answer from your assistant.",
  "event_id": "stable-delivery-id"
}
```

Send the JSON to `/api/events` with `Authorization: Bearer <publishing_key>`. Valid statuses are `idle`, `thinking`, `answer`, and `error`. Characters are `artist`, `curious`, `bookish`, and `cool`; omitting `character` retains the current selection.

The returned flat state includes `status`, `character`, `dot_name`, `title`, `text`, `revision`, `event_id`, `run_id`, and `updated_at`. The latest state persists after restart. A successful response confirms storage; the display must still fetch and refresh.

For another assistant's actual output, use `examples/publish.py --text-file actual-answer.txt` or pipe the answer to that script's stdin. See its `--help` for bridge/configuration options. It publishes the supplied text rather than reading an account's conversations.

## Retry and task ordering

For a thinking → answer sequence, send `thinking` with a fresh `run_id`, then reuse that ID for the answer or error. An explicitly supplied completion ID must match the current active thinking run; a late answer cannot replace a newer task. A standalone answer omits `run_id` and does not need a preceding thinking update.

Use a stable `event_id` for retries of an identical event. Reusing it with changed content returns 409. Retry history retains the most recent 1000 revisions. Use a separate event ID for each new transition.

`PATCH /api/settings` accepts only a character change, such as `{ "character": "cool" }`. It does not publish a new answer.

## MCP tools

| Tool | Input | Purpose |
| --- | --- | --- |
| `set_dot_status` | Required `status`: `idle`, `thinking`, or `error` | Publish a caller-reported state. |
| `publish_dot_reply` | Required `text` | Publish the caller's actual answer. |
| `get_dot_state` | No input | Read the current state. |

The publishing tools also accept optional `character`, `dot_name`, `title`, `run_id`, and `event_id`. The bridge supplies their schemas; the Node stdio adapter forwards discovery and tool calls. These tools do not read calendars, send messages, or observe an automatic ChatGPT reply feed. [Connection and protocol details](real-dot.md)

## Images

Use a named `profile`, or supply `width` and `height` together. `levels` accepts 2 or 16; `frame` accepts 0–11. During thinking, an omitted frame follows `DOTS_FRAME_SECONDS`; a client may choose explicit frames to advance at its own panel cadence. Answers always render the settled frame 11, including requests with an older explicit frame. The answer's PNG/BMP bytes and ETag remain unchanged until another event or character selection.

For a state-aware image client, fetch `/api/display-state` using the read-only image key:

```json
{
  "status": "thinking",
  "revision": 1,
  "animated": true,
  "frame": 0,
  "frame_count": 12,
  "frame_seconds": 5,
  "next_poll_seconds": 5
}
```

This metadata is illustrative. A client can poll it for new work, advance its own frame counter only after a successful image download, and draw the result once when `animated` becomes false. Image clients can use `If-None-Match` to skip unchanged pixels; 304 responses still require authentication. An answer returns `frame: 11`, `animated: false`, and the normal polling hint. The hint does not select a driver or guarantee the panel can refresh that quickly.

The TRMNL endpoint uses a separate counter for the enrolled device, advancing once per authenticated GET while thinking. Its pinned frame URL and changed filename prevent a long sleep from repeatedly landing on the same loop phase. Completed replies have one stable filename. [Exact dimensions, authentication, and device refresh](platforms.md)
