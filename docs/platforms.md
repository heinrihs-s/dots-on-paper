# Displays and refresh behavior

The bridge serves an authenticated image URL. A supported client fetches that image and refreshes its own panel. The included adapters cover common e-ink workflows; each device still needs its correct firmware, driver, dimensions, and network access.

| Platform | Included connection | Profile / output | Validation |
| --- | --- | --- | --- |
| TRMNL X BYOS | `/api/display`, existing ID and Access-Token | `trmnl_x`, 1872 × 1404, 16 gray | HTTP and rendering checked; hardware untested |
| TRMNL BYOS | Same device-pull API | `trmnl`, 800 × 480, monochrome | HTTP and rendering checked; hardware untested |
| Home Assistant | Native custom integration and conversation-agent script | Any named profile | Source/event checks; live HA runtime untested |
| OpenEPaperLink | [HA automation](../examples/openepaperlink.yaml), `drawcustom` / `dlimg` | `oep_296` or `oep_400`, monochrome | Documentation-checked; tag untested |
| ESPHome e-paper | [Online image fragment](../examples/esphome.yaml) | Exact panel dimensions, monochrome | Board/display driver and pins required |
| Inkplate / generic PNG or BMP clients | Direct image fetch | `inkplate`, 800 × 600, or custom size | Renderer checked; device client required |
| Portrait viewers / Kindle | Direct image fetch using your viewer or firmware | `kindle`, 1072 × 1448 | Renderer checked; no Kindle firmware integration |
| TRMNL cloud private plugins | No cloud adapter in this release | Separate cloud rendering schedule | Use BYOS for this bridge |

## Image authentication

For clients that support headers:

```text
GET /image.png?profile=trmnl_x
Authorization: Bearer <image_token>
```

For hardware that cannot send a header, use `/image.png?profile=oep_296&key=<image_token>`. Only the **read-only image key** works in a URL. Keep it out of shared logs and screenshots. Use `/image.bmp` for BMP.

Set `width` and `height` together for custom dimensions, with `levels=2` or `levels=16`. Each side must be 64–2400 pixels and the image must fit within eight million pixels. Long answers visibly truncate on the panel; full text stays in bridge state.

## Animation and physical panels

Omitting `frame` selects the current state-relative frame. Thinking loops; an answer advances through twelve arrival frames and settles. `frame=0` through `frame=11` selects a deterministic still. `DOTS_FRAME_SECONDS` defaults to five seconds per step and controls image selection.

The bridge does not command every device to refresh at that interval. TRMNL defaults to a conservative 60-second poll, the ESPHome example uses 30 seconds, and the OpenEPaperLink example sends final-answer snapshots. A slow device may display only the settled pose. Faster or partial refresh needs a panel/driver that supports it. The smooth campaign films are illustrative animation, not recordings of physical e-ink refresh.

## Existing TRMNL BYOS device

Configure `DOTS_TRMNL_DEVICE_ID` and `DOTS_TRMNL_ACCESS_TOKEN` with your existing enrolled identity. `/api/display` validates both headers and returns the scoped image URL, filename, and refresh interval. `/api/setup` refuses automatic enrollment; firmware updates and resets are not requested.

Changing the device's BYOS server is a separate firmware/configuration step. Pointing it at a new bridge should be verified with that device's documented procedure. This source package does not modify an existing dashboard deployment. Cloud TRMNL private-plugin webhooks follow their own render schedule and do not provide this bridge's device-pull animation path.

## Home Assistant

Copy `custom_components/dots_on_paper` into `/config/custom_components/`, restart HA, and add **Dots on Paper** in Settings → Devices & services. Enter the bridge URL reachable from HA, its publishing key, and a display profile.

The integration provides an image entity, status and last-reply sensors, character select, `show_answer`/`set_state` actions, and a `dot_reply` event for a newly observed answer. Full reply text is an attribute. Startup snapshots and character switches do not replay that event.

HA polls the latest state; transitions shorter than the polling interval may be missed. Its image entity is a cached state snapshot. Direct device image fetches use the stepped frames. The [HA guide](../examples/home-assistant/README.md) includes a dashboard and a script that forwards an actual HA conversation-agent answer, a separate source from the ChatGPT dot.

HACS publication is pending. Manual installation works from the supplied custom-component folder; a running bridge is still required. [Repository release requirements](github-release.md)

## ESPHome and OpenEPaperLink

The ESPHome file is a merge fragment. Configure your actual board, Wi-Fi, display driver, model, pins, busy signal, and drawing lambda before compiling. It uses the bridge's scoped image key. Panel polarity and refresh cadence need verification on your hardware.

The OpenEPaperLink example calls `open_epaper_link.drawcustom` with a `dlimg` payload. Choose the actual HA device ID and tag dimensions, and keep its image URL in secrets. Successful image rendering by the bridge does not establish tag delivery.

Primary platform contracts were checked when preparing the examples: [TRMNL BYOS](https://docs.trmnl.com/go/diy/byos), [ESPHome online images](https://esphome.io/components/image/online_image/), [OpenEPaperLink HA integration](https://github.com/OpenEPaperLink/Home_Assistant_Integration). [Local verification](verification.md) records what was actually exercised.
