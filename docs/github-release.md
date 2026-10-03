# Publish Dots on Paper on GitHub

The source repository is [**heinrihs-s/dots-on-paper**](https://github.com/heinrihs-s/dots-on-paper), owned by `heinrihs-s`. Use this directory as the repository root. This guide covers subsequent tagged releases and HACS preparation.

## Repository identity

| Field | Prepared value |
| --- | --- |
| Name | `dots-on-paper` |
| Display name | Dots on Paper |
| Description | Your dot on e-ink. An MCP + Home Assistant bridge with four switchable companions and readable replies. |
| Personal dot | `heidot`; readers can use their own dot name. |
| Topics | `e-ink`, `e-paper`, `mcp`, `home-assistant`, `trmnl`, `esphome`, `openepaperlink`, `chatgpt`, `python`, `automation` |
| Social preview | `brand/social-preview.png`, 1280 × 640 |
| Source URL | `https://github.com/heinrihs-s/dots-on-paper` |

The current coloured paper-dot header is `brand/header-paper-v2.png`; its exact generation brief is adjacent. The monochrome Cool logo is `brand/logo-cool.svg`, with a dark variant and icon. The editable calendar social preview source is `brand/social-preview.html`. The README's GIF starts on a readable result; the MP4 links provide the full films.

After creating the repository, set its About description/topics and upload the preview through **Settings → Social preview → Edit → Upload an image**. The supplied PNG is under 1 MB and uses GitHub's recommended 1280 × 640 size. [GitHub social-preview guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)

## Publication steps

1. Push the release source to `main`. Retain `LICENSE`, `NOTICE.md`, the font license, and asset provenance. Exclude `data/`, credentials, databases, `.env`, caches, and local Python environments.
2. Confirm the README, GIFs, logo, documentation, and source resolve from that repository. The HA manifest already targets this owner/name; its documentation and issue URLs become usable after publication.
3. Let the configured GitHub CI run, and inspect its results. It is prepared for Python 3.11/3.12 on Linux/Windows, with Node 22. A local pass does not establish a GitHub-hosted CI pass.
4. Rebuild the release archives using `python tools/package.py`, inspect the included files, and attach the archives plus `release/SHA256SUMS.txt` to a `v0.1.0` release. List actual test results for the released commit.
5. Use the verified repository URL in the [release caption](../campaign/posts.md#3-integration-release). Publish that post only when its source/download links work.
6. Enable private vulnerability reporting if you want the private report route described in [SECURITY.md](../SECURITY.md) available.

Tagged release publication and X posting are separate account actions. The source push does not publish either one.

## Checks before release

```sh
python -m pip install .
python tools/smoke.py
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_mcp.mjs
python -m compileall -q custom_components/dots_on_paper
```

Use the installation doctor described in [setup.md](setup.md) to check runtime, assets, credentials, authenticated image output, and MCP connectivity. The doctor does not publish a reply. [Verification evidence](verification.md) records the local checks and remaining hardware/account limits.

`tools/package.py` builds the full source archive, manual HA archive, and separate X media archive, with checksums for those and the available wheel. The HA-only archive contains `custom_components/dots_on_paper`; it still needs a running bridge.

## Suggested release text

> Dots on Paper gives assistant replies a small face and a place on an e-ink screen. This first release includes an authenticated local bridge, three MCP publishing tools, four switchable characters, a Home Assistant integration, TRMNL BYOS endpoints, and ESPHome/OpenEPaperLink examples.
>
> Bridge, rendering, and MCP checks pass locally. Your private dot account, HA instance, and physical display need connection and verification after installation. The campaign clips are staged; the wife-texting scene ends with a cancelled draft and no message sent. Hardware refresh depends on the display and firmware.
>
> Start with README.md and docs/setup.md, then docs/real-dot.md for the dot connection. The manual HA archive installs the custom component; the full source archive contains the bridge and examples.

Use actual results for the released commit instead of copying an old test count.

## HACS and live integrations

The source has the HACS directory layout, owner/URL fields, and brand assets. HACS registration and installation validation are still pending. Verify current [HACS requirements](https://www.hacs.xyz/docs/publish/integration/) and its checks before advertising a HACS installation.

A GitHub release does not connect a private ChatGPT dot or provision a display. The actual dot needs the supported MCP connection and enabled tools; the display needs a reachable image URL and tested refresh configuration. Instinct remains an independent visual concept, with no implemented connector.

## Campaign handoff

Use the [campaign](../campaign/README.md) for the tiny dot's calm calendar judgment, the user's NOO reaction, and the code reveal. The captions and embedded source metadata identify the staged output. Preserve the Instinct still's own concept labels. A future live demonstration should name its actual answer source and tested hardware.

The source is published. A tagged release still needs its hosted CI results, verified download links, and release assets. The remaining live-integration steps are account access and physical HA/display verification.
