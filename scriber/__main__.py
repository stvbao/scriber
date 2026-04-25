import sys
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
