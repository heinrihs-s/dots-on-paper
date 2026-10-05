"""Forward actual answer text from another assistant to the bridge. Stdlib only."""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    parser = argparse.ArgumentParser(description="Publish an actual assistant answer from stdin or a UTF-8 file")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--dot-name", default="Your dot")
    parser.add_argument("--title", default="Your dot replied")
    parser.add_argument("--source", default="", help="Short source label frozen into the card")
    parser.add_argument("--character", choices=("artist", "curious", "bookish", "cool"))
    args = parser.parse_args()
    endpoint = os.environ.get("DOTS_BRIDGE_URL", "http://127.0.0.1:9035").rstrip("/")
    parts = urlsplit(endpoint)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        parser.error("DOTS_BRIDGE_URL must be an HTTP(S) bridge URL without credentials")
    token = os.environ.get("DOTS_API_TOKEN")
    if not token:
        config = Path(os.environ.get("DOTS_CONFIG_FILE", Path(__file__).resolve().parents[1] / "data" / "credentials.json"))
        try:
            token = json.loads(config.read_text(encoding="utf-8"))["api_token"]
        except (OSError, ValueError, KeyError):
            parser.error("Initialize the bridge keys or configure DOTS_CONFIG_FILE / DOTS_API_TOKEN")
    text = args.text_file.read_text(encoding="utf-8") if args.text_file else sys.stdin.read(12001)
    if not text.strip() or len(text) > 12000:
        parser.error("Answer text must contain 1–12000 characters")
    payload = dict(status="answer", text=text, dot_name=args.dot_name, title=args.title, source=args.source)
    if args.character:
        payload["character"] = args.character
    request = Request(endpoint + "/api/events", data=json.dumps(payload).encode("utf-8"), method="POST", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            state = json.load(response)
        print(f"Reply stored at revision {state['revision']}. Your display refreshes on its own schedule.")
    except Exception:
        parser.exit(1, "Publishing failed. Check the bridge URL, token and input; no private response was logged.\n")


if __name__ == "__main__":
    main()
