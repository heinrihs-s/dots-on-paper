# Publish an engineering beta

The source repository is [heinrihs-s/dots-on-paper](https://github.com/heinrihs-s/dots-on-paper), with the [public browser trial](https://heinrihs.org/dotsonpaper/try/). The About description is “A tiny e-ink companion for useful AI replies. Local bridge, MCP, and Home Assistant.” Discussions provide Show your desk, Setup help and Recipes. Hardware-led promotion waits for the [roadmap evidence gates](roadmap.md).

## Build and verify downloads

Use the maintained Python environment from [setup.md](setup.md). Build after the final source changes:

```sh
python -m pip install --upgrade .
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_mcp.mjs
python tools/smoke.py
python tools/doctor.py --offline --mcp
python -m pip wheel . --no-deps --wheel-dir dist
python tools/package.py
python tools/release_check.py --wheel release/dots_on_paper-0.2.0b1-py3-none-any.whl --runtime release/dots-on-paper-0.2.0b1.zip
```

When a previous wheel is available, add `--upgrade-from dist/dots_on_paper-0.1.0-py3-none-any.whl` to check migration with retained state and unchanged keys. Checks run outside the source directory, with temporary credentials and databases. Never package `data/`, `.env`, private keys, caches or local environments.

The runtime ZIP contains the Python bridge, packaged stdio adapter, launch/setup/doctor tools, docs, examples, licenses and one header image. Large films and development dependencies stay in the source repository; `python tools/package.py --campaign` creates an optional separate media archive. The wheel is the installable Python package. The manual HA ZIP contains the integration and still requires a running bridge; its own manifest remains 0.1.0 and has not been verified in a live HA runtime.

## Publish the matching source and images

1. Push the reviewed source and inspect Source checks. It exercises Python 3.11/3.12 on Linux/Windows, exact wheel/runtime installation, and native amd64/arm64 container startup, restart and replacement with a disposable persistent volume.
2. Create the `v0.2.0-beta.1` tag at that verified commit. Publish a GitHub prerelease with the wheel, runtime ZIP, HA ZIP and `SHA256SUMS.txt`, using [the release notes](release-notes-0.2.0-beta.1.md). A prerelease uses its direct tag URL; GitHub’s `/releases/latest` excludes prereleases.
3. The tag starts Beta release. Each native runner builds and tests its image before publishing an architecture tag. Only after both pass does the workflow publish `ghcr.io/heinrihs-s/dots-on-paper:0.2.0-beta.1`. Check anonymous pulls before advertising it as a public download.
4. Compare the deployed browser trial with the generated site manifest. Record actual CI links, deployment and release results in [verification.md](verification.md) and [the deployment record](../site/DEPLOYMENT.md).

Docker’s native runner checks establish the listed architecture behavior; they do not establish support for every Raspberry Pi model, a panel or firmware. Release artifacts and compatibility claims must describe the same source revision.

## Account, hardware and promotion gates

The [compatibility matrix](compatibility.md) distinguishes software verification, experimental routes and example configurations. A webhook acceptance or image fetch is a receipt; an observed physical panel is separate evidence. Record exact model, firmware, refresh settings, latency, restart and failure recovery using the hardware issue form.

HACS registration and live installation validation remain pending. Verify [current HACS requirements](https://www.hacs.xyz/docs/publish/integration/) before advertising that route. HACS installs the integration, not the bridge. A private ChatGPT dot needs a supported MCP connection and account permissions. Instinct remains a visual concept without an implemented connector.

Use the [beta study](beta-study.md) to observe first use and seven-day usefulness. Publish real-device footage and community launch posts after the gates pass, with permission for user photos. Existing campaign films are staged. Outreach, messaging and posting remain separate future actions.
