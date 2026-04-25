import os
import sys
from pathlib import Path
from platformdirs import user_cache_dir

# Set HF cache to scriber's own directory before any HF imports
_cache = Path(user_cache_dir("scriber")) / "models"
_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HUB_CACHE", str(_cache))

from scriber.cli import parse_args, run_cli
from scriber.app import run_app


def main():
    args = parse_args()

    if args.subcommand == "app" or len(sys.argv) == 1:
        run_app()
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
