# Displays and refresh behavior

The bridge serves an authenticated image URL. A supported client fetches that image and refreshes its own panel. The included adapters cover common e-ink workflows; each device still needs its correct firmware, driver, dimensions, and network access.

| Platform | Included connection | Profile / output | Validation |
| --- | --- | --- | --- |
| TRMNL X BYOS | Thinking pose per wake, then cached result | `trmnl_x`, 1872 × 1404, 16 gray | Firmware contract, HTTP and rendering checked; hardware untested |
| TRMNL BYOS | Same device-pull API | `trmnl`, 800 × 480, monochrome | HTTP and rendering checked; hardware untested |
| Home Assistant | Thinking image timer and conversation-agent script | Any named profile | Source/event checks; live HA runtime untested |
| OpenEPaperLink | [HA automation](../examples/openepaperlink.yaml), `drawcustom` / `dlimg` | `oep_296` or `oep_400`, monochrome | Documentation-checked; tag untested |
| ESPHome e-paper | [State-aware image fragment](../examples/esphome.yaml) | Exact panel dimensions, monochrome | Board/display driver and pins required |
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

Thinking uses twelve successive PNG/BMP poses. An image client can select `frame=0` through `frame=11`, or omit it to use the state-relative five-second sequence configured by `DOTS_FRAME_SECONDS`. Once an answer arrives, every image request returns the settled result immediately. Its pixels and ETag stay fixed until another event or character change. This is successive-image animation; panels do not play the campaign's MP4 or GIF files.

For TRMNL BYOS, `/api/display` advances one pose per authenticated device poll. The pinned frame URL and changing filename avoid repeatedly choosing the same pose when the device's sleep happens to match the loop duration. During thinking, the bridge returns `DOTS_THINKING_REFRESH_SECONDS` (default 15). After completion it returns `DOTS_REFRESH_SECONDS` (default 60) and one stable result filename.

TRMNL interprets the interval as seconds to **sleep after** its wake/download/draw cycle, so boot, Wi-Fi, transfer, and panel refresh add latency. The current firmware skips the image download and panel redraw when the filename is unchanged. The result therefore remains on the screen during later polls. A sleeping device cannot receive an immediate push: a short task may finish before it wakes and only the result will appear. Wake the device before a demonstration, or choose a shorter normal interval for your desk setup. More frequent wakes consume more power. [BYOS protocol](https://docs.trmnl.com/go/diy/byos), [firmware cache and sleep loop](https://github.com/usetrmnl/trmnl-firmware/blob/2cd89c395cd23feb0aa170719ebe26432ce85844/src/bl.cpp)

Stock TRMNL X currently uses a full update for new images; its partial-update block is commented out. Expect slow steps and flashing, rather than the accelerated movie cadence. The ordinary TRMNL and some ESPHome panels have partial-refresh paths, with periodic full clears. Faster animation requires the exact panel and driver to support it. [TRMNL display implementation](https://github.com/usetrmnl/trmnl-firmware/blob/2cd89c395cd23feb0aa170719ebe26432ce85844/src/display.cpp), [ESPHome driver models](https://esphome.io/components/display/waveshare_epaper/)

The campaign films render the actual monochrome/grayscale screen frames at an accelerated cadence and finish on a held answer. They are previews, not footage of a physical panel.

### Configure a TRMNL desk demo

With the bridge stopped, set these variables before launching it on Windows:

```powershell
$env:DOTS_THINKING_REFRESH_SECONDS = '15'
$env:DOTS_REFRESH_SECONDS = '60'
.\run.ps1
```

The bridge accepts thinking intervals from 5 to 3600 seconds. A value of 5 is an opt-in shorter sleep, not a five-second display guarantee. For Docker, set the same values in its environment and recreate the service. Native clients must also have the existing BYOS identity, reachable image origin, and correct profile configured.

For a generic image client, use the read-only [`/api/display-state`](api.md#images) metadata. Poll for new work, advance an explicit local frame while `animated` is true, and draw a completed result only when its revision changes. Conditional image requests return 304 for unchanged pixels. Keep the panel's own refresh timer disabled if the application controls drawing.

## Existing TRMNL BYOS device

Configure `DOTS_TRMNL_DEVICE_ID` and `DOTS_TRMNL_ACCESS_TOKEN` with your existing enrolled identity. `/api/display` validates both headers and returns HTTP 200 with JSON `status: 0`, the scoped image URL, filename, and refresh interval. `/api/setup` refuses automatic enrollment; firmware updates and resets are not requested.

Changing the device's BYOS server is a separate firmware/configuration step. Pointing it at a new bridge should be verified with that device's documented procedure. This source package does not modify an existing dashboard deployment. Cloud TRMNL private-plugin webhooks follow their own render schedule and do not provide this bridge's device-pull animation path.

## Home Assistant

Copy `custom_components/dots_on_paper` into `/config/custom_components/`, restart HA, and add **Dots on Paper** in Settings → Devices & services. Enter the bridge URL reachable from HA, its publishing key, and a display profile.

The integration provides an image entity, status and last-reply sensors, character select, `show_answer`/`set_state` actions, and a `dot_reply` event for a newly observed answer. Full reply text is an attribute. Startup snapshots and character switches do not replay that event.

HA polls the latest state; transitions shorter than the polling interval may be missed. Its image entity runs a configurable frame timer only while thinking. The completed result cancels the timer and remains cached. Direct device image fetches have their own cadence. The [HA guide](../examples/home-assistant/README.md) includes a dashboard and a script that forwards an actual HA conversation-agent answer, a separate source from the ChatGPT dot.

HACS publication is pending. Manual installation works from the supplied custom-component folder; a running bridge is still required. [Repository release requirements](github-release.md)

## ESPHome and OpenEPaperLink

The ESPHome file is a merge fragment. Configure your actual board, Wi-Fi, display driver, model, pins, busy signal, and drawing lambda before compiling. It polls display metadata using the scoped image key, fetches thinking poses at a configurable panel cadence, then draws the final result once. Set the display's own `update_interval` to `never`. Panel polarity, partial-refresh support, busy timing, and refresh cadence need verification on your hardware.

The OpenEPaperLink example calls `open_epaper_link.drawcustom` with a final `dlimg` result. Choose the actual HA device ID and tag dimensions, and keep its image URL in secrets. Typical sleeping tags have radio check-in latency measured in tens of seconds. A tag's fast/partial refresh mode does not remove that latency, so the portable example sends the held result rather than a rapid loop. Successful image rendering by the bridge does not establish tag delivery. [Protocol timing](https://github.com/OpenEPaperLink/OpenEPaperLink/wiki/Tag-protocol-timing)

Primary platform contracts were checked when preparing the examples: [TRMNL BYOS](https://docs.trmnl.com/go/diy/byos), [ESPHome online images](https://esphome.io/components/image/online_image/), [OpenEPaperLink HA integration](https://github.com/OpenEPaperLink/Home_Assistant_Integration). [Local verification](verification.md) records what was actually exercised.
