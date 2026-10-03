from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import Config, default_data_dir, init_credentials
from .server import BridgeServer
from .state import StateStore


def main():
    parser = argparse.ArgumentParser(description="Run the Dots on Paper display bridge")
    parser.add_argument("--init", action="store_true", help="Create private local keys, without displaying them")
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("DOTS_DATA_DIR", default_data_dir())))
    args = parser.parse_args()
    config_file = Path(os.environ.get("DOTS_CONFIG_FILE", args.data_dir / "credentials.json"))
    if args.init:
        init_credentials(config_file)
        print(f"Private keys are ready in {config_file}. No existing keys were replaced.")
        return
    if not config_file.exists() and not (os.environ.get("DOTS_API_TOKEN") and os.environ.get("DOTS_IMAGE_TOKEN")):
        parser.error("Run --init first, or configure both DOTS_API_TOKEN and DOTS_IMAGE_TOKEN")
    try:
        config = Config.from_environment(config_file)
        args.data_dir.mkdir(parents=True, exist_ok=True)
        store = StateStore(args.data_dir / "state.sqlite3")
        server = BridgeServer((config.host, config.port), config, store)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Dots on Paper is listening at {config.public_url}; bind {config.host}:{config.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()


if __name__ == "__main__":
    main()
