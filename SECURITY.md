# Security

## Report an issue

If this repository has private vulnerability reporting enabled, use its **Security → Report a vulnerability** entry. Otherwise, open an issue asking the maintainer for a private reporting route without including exploit details, credentials, or private content. No private reporting endpoint is bundled with this source package.

Include the package version, affected endpoint or adapter, a minimal reproduction using generated credentials, and the impact. Do not include an actual dot reply, production token, or device identity. The current engineering beta is 0.2.0b1; no response-time commitment is made.

## Boundaries

The publishing key can read the current reply and publish display updates. The separate image key can read rendered images. An image may contain the same private information as the reply. Query-string image keys are intended for hardware that cannot send a bearer header; request logs and shared screenshots can expose them.

The bridge defaults to loopback. Keep it on a trusted network or connect ChatGPT through Secure MCP Tunnel to the local stdio adapter, as described in [the real-dot guide](docs/real-dot.md). Other remote clients need HTTPS and compatible authentication. The bridge uses a static bearer key and does not implement the OAuth discovery needed for a direct authenticated ChatGPT HTTPS connection. It does not provision hosting or connect an account automatically.

The latest state and retry history are stored locally in SQLite. Changing the character does not erase the answer. Treat the data directory, backups, and credentials file as private. Do not put live data in a GitHub release or campaign asset.

The MCP tools publish text to the display bridge. They do not send texts, emails, or calendar invitations. Marketing scenes are scripted drafts, including the wife-texting joke. No depicted message is sent.

If a key is exposed, stop the bridge and generate a new credentials file using `python -m dots_on_paper --init --data-dir <fresh-private-directory>`. Set `DOTS_CONFIG_FILE` to a new path in that directory if you already use that override. Replace any configured key environment overrides, then configure the bridge and each client with the new credentials. Keep the old data directory private if you retain it. Do not rely on deleting a public commit to revoke a leaked key.
