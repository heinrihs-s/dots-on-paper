# Publishing and image API

The publishing key authorizes state reads, updates, and MCP requests. The separate image key authorizes PNG/BMP and display-metadata reads. Keep keys in the client environment or private credentials file. The bridge does not call a model API; the optional Secure MCP Tunnel connection requires its own Platform runtime key.

## Endpoints

| Endpoint | Authentication | Result |
| --- | --- | --- |
| `GET /api/health` | Public | Minimal health/version, without reply or credentials. |
| `GET /api/state` | Publishing bearer key | Current reply, display mode and supplied conversation turns. |
| `GET /api/profiles` | Publishing bearer key | Named render profiles. |
| `POST /api/events` | Publishing bearer key | Store a deliberate display update. |
| `PATCH /api/settings` | Publishing bearer key | Change `character` and/or `mode`, preserving the reply/event ID. |
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

The returned state includes `status`, `character`, `dot_name`, `title`, `text`, `mode`, `messages`, `revision`, `event_id`, `run_id`, and `updated_at`. The latest state and selected mode persist after restart. A successful response confirms storage; the display must still fetch and refresh.

For another assistant's actual output, use `examples/publish.py --text-file actual-answer.txt` or pipe the answer to that script's stdin. See its `--help` for bridge/configuration options. It publishes the supplied text rather than reading an account's conversations.

## Retry and task ordering

For a thinking → answer sequence, send `thinking` with a fresh `run_id`, then reuse that ID for the answer or error. An explicitly supplied completion ID must match the current active thinking run; a late answer cannot replace a newer task. A standalone answer omits `run_id` and does not need a preceding thinking update.

Use a stable `event_id` for retries of an identical event. Reusing it with changed content returns 409. Retry history retains the most recent 1000 revisions. Use a separate event ID for each new transition.

`PATCH /api/settings` accepts `character` and/or `mode`, such as `{ "mode": "full_conversation" }`. A settings change redraws the stored content without publishing a new answer.

## Display modes

**Last reply** (`last_reply`, the default) displays the latest assistant answer. **Full conversation** (`full_conversation`) displays the supplied user and assistant turns, with a dark user bubble. Small screens show the most recent turns that fit. Switching modes keeps the stored conversation.

Send an explicit user turn when starting work:

```json
{
  "status": "thinking",
  "mode": "full_conversation",
  "user_text": "Should I cancel?",
  "run_id": "task-42"
}
```

Then publish the answer with the same `run_id` and `text`. The bridge appends the assistant turn. You can supply `user_text` on a standalone answer too; omit it on completion when the thinking event already supplied that turn. The bridge stores up to 20 turns and 24000 content characters, discarding the oldest turns as new ones arrive. A mode selection alone does not retrieve messages from an account.

To replace the stored history deliberately, include a `messages` snapshot on an answer:

```json
{
  "status": "answer",
  "mode": "full_conversation",
  "text": "Cancelled. Nothing sent.",
  "messages": [
    {"role": "user", "content": "NOO"},
    {"role": "assistant", "content": "Cancelled. Nothing sent."}
  ]
}
```

A snapshot contains 1–20 objects with `role` (`user` or `assistant`), nonempty `content` up to 12000 characters per turn, and optional `meta` up to 120 characters. Combined content must fit within 24000 characters. Its last turn must be an assistant message whose content exactly matches `text`. Use `messages` or `user_text`, not both. Supply only messages intended for that display; the bridge never reads a chat account or captures hidden reasoning.

## MCP tools

| Tool | Input | Purpose |
| --- | --- | --- |
| `set_dot_status` | Required `status`: `idle`, `thinking`, or `error` | Publish a caller-reported state. |
| `publish_dot_reply` | Required `text` | Publish the caller's actual answer. |
| `get_dot_state` | No input | Read the current state. |

The publishing tools also accept optional `character`, `dot_name`, `title`, `run_id`, `event_id`, and `mode`. `set_dot_status` accepts `user_text` when thinking; `publish_dot_reply` accepts `user_text` or the answer's `messages` snapshot. The bridge supplies their schemas; the Node stdio adapter forwards discovery and tool calls. These tools do not read calendars, send messages, or observe an automatic ChatGPT reply feed. [Connection and protocol details](real-dot.md)

## Images

Use a named `profile`, or supply `width` and `height` together. `levels` accepts 2 or 16; `frame` accepts 0–11. During thinking, an omitted frame follows `DOTS_FRAME_SECONDS`; a client may choose explicit frames to advance at its own panel cadence. Answers always render the settled frame 11, including requests with an older explicit frame. The answer's PNG/BMP bytes and ETag remain unchanged until another event, character selection, or mode change.

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
