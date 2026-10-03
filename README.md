![Dots on Paper — blue, green, yellow and pink matte paper dots, with the sunglasses heart in front](brand/header-paper-v2.png)

# Dots on Paper

**Give your assistant a tiny face and a place on your desk.**

An MCP and Home Assistant bridge that turns real assistant replies into readable e-ink screens. Four switchable characters, a calm reply view, and a little personality when an answer arrives.

[![heidot’s staged reminder reply ending with “Your calendar needs a lawyer”](campaign/media/dot-reminders.gif)](campaign/media/dot-reminders.mp4)

*heidot, imagined on e-ink. The calendar is fictional; the bridge is real.* [Watch the MP4](campaign/media/dot-reminders.mp4) · [The “NOO” film](campaign/media/dot-noo.mp4) · [X launch package](campaign/README.md)

**Working locally:** authenticated publishing, rendering, browser preview, and MCP forwarding. **Still to connect:** your actual dot account, HA installation, and physical display. [Verification and limits](docs/verification.md)

## What you get

- A local bridge with persistent replies and separate publishing/image keys.
- Three MCP tools: `set_dot_status`, `publish_dot_reply`, and `get_dot_state`.
- A Home Assistant image entity, reply/status sensors, character picker, actions, and new-reply events.
- TRMNL BYOS endpoints, ESPHome/OpenEPaperLink examples, and custom PNG/BMP sizes.
- Artist, Curious, Bookish, and Cool — switch the face without losing the answer.
- A standalone demo and ready-to-edit campaign assets.

```text
Your dot or HA assistant → authenticated bridge → PNG / BMP → e-ink display
```

The dot deliberately publishes its answer through a tool. The bridge does not automatically watch every ChatGPT reply. Display refresh is controlled by the device; the film's smooth animation is an illustrative concept.

## Run the bridge

From this repository's root, with **Python 3.11+** and **Node.js 22+** installed:

```sh
python tools/setup.py
```

Then start it:

| Windows PowerShell | macOS / Linux |
| --- | --- |
| `.\run.ps1` | `.venv/bin/python -m dots_on_paper --data-dir ./data` |

Open **http://127.0.0.1:9035** and select `data/credentials.json` in the connection panel. Setup creates a local virtual environment, installs the package, and initializes private keys without replacing or displaying them. The first state is “Waiting for your dot.”

With the bridge running, check it using `.\run.ps1 -Doctor` on Windows or `.venv/bin/python tools/doctor.py` on macOS/Linux. [Setup, LAN access, Docker, and troubleshooting](docs/setup.md)

## Connect your real dot

Install the portable plugin or connect its MCP tools to your client. A cloud ChatGPT dot needs a reachable connection — a supported Secure MCP Tunnel or authenticated HTTPS endpoint. A localhost bridge alone is not reachable from the cloud.

After connecting, tell your dot:

> Use Dots on Paper for answers in this conversation. Set it to thinking when you start. Publish a short version of your actual answer when you finish.

The local tools are implemented; private account access and device delivery need verification after installation. [Real-dot connection guide](docs/real-dot.md) · [REST/API inputs](docs/api.md)

**heidot** is the personal dot behind this project's idea. **Dots on Paper** is the bridge name; configure your own dot's display name when publishing.

## Displays and Home Assistant

| Platform | Included path | Current validation |
| --- | --- | --- |
| TRMNL / TRMNL X BYOS | Authenticated device-pull endpoint; native screen profiles | HTTP and renderer checked; hardware untested |
| Home Assistant | Native custom integration + actual conversation-agent forwarding example | Source checks; live HA runtime untested |
| ESPHome e-paper | Online-image configuration fragment | Driver, pins, and panel refresh need your setup |
| OpenEPaperLink | HA `drawcustom` image automation | Documentation-checked; tag untested |
| Generic PNG/BMP clients, Inkplate, portrait viewers | Scoped image URL with named or custom dimensions | Renderer checked; device client required |

Copy `custom_components/dots_on_paper` into HA's `/config/custom_components/`, restart HA, and add **Dots on Paper** in Devices & services. Use a bridge address reachable from HA. [HA setup](examples/home-assistant/README.md) · [Profiles, authentication, and refresh behavior](docs/platforms.md)

TRMNL cloud private-plugin rendering follows a different schedule and is not connected by this release. HACS publication is also pending.

## Try the animation

```sh
node demo/serve.mjs
```

Open **http://127.0.0.1:9024/?example=calendar-chaos**. Switch all four dots, try the “NOO” conversation, or write a multiline reply. The layout handles paragraphs and lists; the examples do not change its rules.

The [campaign](campaign/README.md) includes GIFs, MP4s, native screen stills, and four short posts. The wife-texting exchange is a cancelled scripted draft; no message is sent. The **Instinct-inspired** image is an independent concept with no Instinct connector. [Product facts](docs/product-facts.md)

## Publish and contribute

The source is on [GitHub](https://github.com/heinrihs-s/dots-on-paper). HACS registration and a tagged release remain separate steps. [GitHub release guide](docs/github-release.md)

[Contributing and checks](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE) · [Asset provenance](NOTICE.md)
