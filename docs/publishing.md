# Distribute Dots on Paper

The GitHub repository includes an installable local plugin catalog. It has not been submitted to OpenAI's public directory.

## Install from the repository

Run this on the computer where you use Codex:

```sh
codex plugin marketplace add heinrihs-s/dots-on-paper --ref main
```

Restart the desktop app, open the Plugins Directory, select the **Dots on Paper** source, and install **Dots on Paper**. Start a new conversation with it enabled. Configure the running bridge and `DOTS_CONFIG_FILE` using the [connection guide](real-dot.md).

The command registers this repository as a catalog in that client's configuration. It does not submit the plugin to OpenAI or make it appear in everyone's directory. The catalog is [`.agents/plugins/marketplace.json`](../.agents/plugins/marketplace.json); its `./` path points to the repository root. The package contains root `plugin.json`, `mcp.json`, and `skills/`, following OpenAI's [packaging guide](https://developers.openai.com/plugins/build/plugins).

To fetch later repository updates:

```sh
codex plugin marketplace upgrade dots-on-paper
```

`main` follows development. Once a release tag exists, users can select that tag with `--ref` instead. See the [release guide](github-release.md).

## Publish in OpenAI's public directory

OpenAI's directory is shared by ChatGPT and Codex. The [submission guide](https://developers.openai.com/plugins/deploy/submission) describes this process:

1. Select the owning Platform organization and project. Use an organization owner account or a role with **Apps Management Write**, and verify the publishing identity.
2. Open [Platform Plugins](https://platform.openai.com/plugins), choose **Upload new or existing plugin**, and upload a package ZIP.
3. Resolve metadata and skill findings. For an MCP plugin, connect the server, verify its domain, and complete the tool scans and reviewer access.
4. Submit the draft for review. After approval, select **Publish plugin**.

The current package needs these changes before public MCP submission:

- A supported public HTTPS MCP connection. OpenAI's [packaging guide](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks) directs local MCP authors to deploy one or contact OpenAI for local MCP support.
- Listing icon files and `logo` / `composerIcon` paths, plus website, support, privacy-policy, and terms URLs. These are [submission fields](https://developers.openai.com/plugins/deploy/submission#manifest-fields).
- A real account-to-display test and a reviewer walkthrough of the working integration. The marketing films demonstrate scripted screens; they are not a recording of that connection. See [verification](verification.md) and [MCP review requirements](https://developers.openai.com/plugins/deploy/app-review).

The bridge currently authenticates HTTP requests with a private bearer token. ChatGPT cannot supply a custom API key. A public service needs supported user authentication, such as an OAuth gateway, and a way to route each user's updates to their own bridge. That service is not included. See OpenAI's [authentication guide](https://developers.openai.com/plugins/build/auth).

The source archive from `python tools/package.py` is for repository distribution; it is not a public submission package. Do not upload private bridge credentials or tunnel profiles. Keep the local plugin working while preparing any public version separately.
