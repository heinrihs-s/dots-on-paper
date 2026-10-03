---
name: publish-dot-reply
description: Publish a real answer or work status to the user's Dots on Paper e-ink display when they ask to use the display, or have enabled it for this conversation.
---

Use the Dots on Paper MCP tools to put your own completed answer on the user's configured display. An enabled plugin alone is not an instruction to publish every private conversation. Follow the scope the user set, such as this conversation or a named responsibility.

When working on a request with display updates enabled, call `set_dot_status` with `status: "thinking"` before substantive work. On completion, call `publish_dot_reply` with `text` containing the actual answer or a faithful short summary. Send the answer in the conversation too; a display update is an additional delivery channel.

Omit `character` to use the user's selected dot. Use `dot_name` only when you know your name or the user specified it. An optional short `title` helps identify the result. Choose a fresh `run_id` for each request and use it for both the status and answer so a delayed reply cannot overwrite newer work. Assign a stable `event_id` before a publish attempt and reuse it if you retry that same answer.

Write concise plain text that fits an e-ink screen. Preserve qualifications, numbers, and errors that change the meaning. Do not substitute a demo answer, prediction, progress note, or canned success for a completed result. Do not expose hidden reasoning, credentials, full conversation history, or unrelated private source material on the display. If the user asks for a public display, send only information they authorized for that audience.

For a task failure, call `set_dot_status` with `status: "error"` and a brief, safe `title`; describe the failure honestly in the conversation. Use `status: "idle"` if the request is interrupted or stopped before an answer. If publishing fails, keep the answer available in the conversation and report that display delivery failed. Do not claim the physical device refreshed based only on the bridge accepting a tool call. Retry a transient delivery failure once, using the same event identifier, then stop that delivery attempt.

`get_dot_state` can confirm the bridge's current character and stored answer. The tools do not observe every ChatGPT message or stream the dot's internal activity. Connection setup is documented in [real-dot.md](../../docs/real-dot.md); read it only when configuring or troubleshooting this plugin.
