# Publishing and image API

The publishing key authorizes state reads, updates, and MCP requests. The separate image key authorizes PNG/BMP reads. Keep keys in the client environment or private credentials file; no OpenAI API key or separate model call is required for the dot's publish-tool workflow.

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

Use a named `profile`, or supply `width` and `height` together. `levels` accepts 2 or 16; `frame` accepts 0–11. Omitting a frame uses the state-relative sequence. [Exact dimensions, authentication, and device refresh](platforms.md)
