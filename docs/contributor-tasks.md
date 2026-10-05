# Five bounded contributions

Use temporary state, the released beta and safe example text. Each task should include its exact version and reproduction steps. Avoid adding a broad adapter or speculative support claim as part of these tasks.

| Task | Reproduce / scope | Definition of done |
| --- | --- | --- |
| Verify one device | Follow first-result.md, configure one existing BYOS or Webhook Image route, publish a real task summary | Hardware form includes model, firmware, route, normal settings, latency, observed result, restart and failure recovery; safe photo only with permission |
| Translate setup text | Copy the four-step checklist wording from web.html and first-result.md into one proposed locale file | All actions and error/recovery wording covered; native speaker review; no translated credential/configuration identifiers |
| Improve one small-screen case | At 390 px, publish a 600-character paragraph and a short list using a temporary bridge | One reproducible readability/accessibility defect fixed; transcript stays readable; keyboard focus and layout checked at desktop and phone widths |
| Supply one tested recipe | Repeat a real source/scheduler → publish → retained result loop on three days | Names actual source and prerequisites, provides minimal configuration without secrets, records failures and reproducible outcome |
| Validate one client configuration | Generate local MCP config, load it in one named client, restart the client, call get_dot_state then publish_dot_reply | Exact client/Node/bridge versions, real useful result in browser, disconnected/reconnected failure handling, install instructions usable without maintainer help |

Propose the bounded task in Setup help or Recipes, or open an issue linking this document. A maintainer can label a reproducible, claimed task `good first issue`; those labels are not evidence of device verification.
