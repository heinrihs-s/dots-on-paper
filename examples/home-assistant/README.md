# Home Assistant

Copy `custom_components/dots_on_paper` into Home Assistant's `/config/custom_components/` directory, restart Home Assistant, and add **Dots on Paper** in Settings → Devices & services. The source is on [GitHub](https://github.com/heinrihs-s/dots-on-paper) and includes the HACS directory layout, `hacs.json`, brand icons, and maintainer metadata. HACS registration is pending. Manual installation is the locally checked path; verify current [HACS requirements](https://www.hacs.xyz/docs/publish/integration/) and your HA installation before using a HACS custom **Integration** repository.

Use the bridge URL reachable from the HA host, its `DOTS_API_TOKEN`, and an image profile. The default interval is five seconds, with a two-second minimum. `localhost` refers to Home Assistant's own host/container, so a bridge on another computer needs that computer's LAN address. Configure the bridge's `DOTS_HOST`, `DOTS_PUBLIC_URL`, and `DOTS_ALLOWED_HOSTS` for that address before connecting from HA or a device. This integration does not open a network listener or modify your hardware.

It adds a screen image, status sensor, last reply sensor, and character picker. Reply text is an attribute, keeping the sensor's state within HA's 255-character limit. The last reply survives thinking/idle transitions and is restored after HA restarts. Native image fetching sends the API token in the Authorization header; entity attributes and image URLs do not contain the bridge token.

Use Developer tools → Actions to call `dots_on_paper.set_state` or `dots_on_paper.show_answer`. Select the bridge in the action editor; the resulting `entry_id` is a Home Assistant config entry ID, not a display device ID. A new answer produces a `dot_reply` event with `entry_id`, `text`, `dot_name`, `character`, `event_id`, `run_id`, and revision. Startup snapshots, repeated polling, and character changes do not replay that event. Very brief transitions between state polls can be missed; this integration reads the current bridge state rather than a durable event history.

For a thinking → answer sequence, begin with a fresh `run_id` and reuse it for completion; this lets the bridge reject delayed answers from an older run. Do not use a conversation ID as the display run ID. For a standalone `show_answer`, omit `run_id`. Use a different `event_id` for each transition, and reuse that event ID only when retrying the exact same event.

`conversation.yaml` is an optional script that obtains an actual answer from a configured HA conversation agent and forwards it to the display. Edit its placeholders in your own HA instance. It uses the HA conversation agent, separate from the ChatGPT Work dot source. `dashboard.yaml` is a small card example; adjust entity IDs to those assigned by your installation.

Hardware examples require a separate **read-only** `DOTS_IMAGE_TOKEN`. Do not reuse a HA long-lived access token or the bridge write token in display URLs. Devices must reach the bridge address. Keep tokens in HA/ESPHome secrets; no live credentials are included here.

This component has source/syntax checks; it has not been loaded into a live HA runtime or tested on e-ink hardware.

Official contracts: [config flows](https://developers.home-assistant.io/docs/core/integration/config_flow/), [service actions](https://developers.home-assistant.io/docs/dev_101_services/), [image entities](https://developers.home-assistant.io/docs/core/entity/image/), [conversation responses](https://developers.home-assistant.io/docs/intent_conversation_api/).
