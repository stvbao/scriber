import os
import sys
import warnings


def _set_runtime_env() -> None:
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
    os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
    os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")

    resource_warning = "ignore:resource_tracker:UserWarning:multiprocessing.resource_tracker"
    existing = os.environ.get("PYTHONWARNINGS")
    if existing:
        if resource_warning not in existing:
            os.environ["PYTHONWARNINGS"] = f"{resource_warning},{existing}"
    else:
        os.environ["PYTHONWARNINGS"] = resource_warning
    warnings.filterwarnings(
        "ignore",
        message="resource_tracker:.*",
        category=UserWarning,
        module="multiprocessing.resource_tracker",
    )


def _clean_macos_dyld_env() -> None:
    if sys.platform != "darwin":
        return

    keys = ("DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH")
    needs_reexec = any(key in os.environ for key in keys)

    if getattr(sys, "frozen", False) or os.environ.get("SCRIBER_DYLD_ENV_CLEANED") == "1":
        for key in keys:
            os.environ.pop(key, None)
        return

    clean_env = os.environ.copy()
    for key in keys:
        clean_env.pop(key, None)

    if needs_reexec:
        clean_env["SCRIBER_DYLD_ENV_CLEANED"] = "1"
        os.execvpe(sys.executable, [sys.executable, "-m", "scriber", *sys.argv[1:]], clean_env)

    os.environ["SCRIBER_DYLD_ENV_CLEANED"] = "1"


_set_runtime_env()
_clean_macos_dyld_env()

from pathlib import Path
from platformdirs import user_cache_dir

# Set HF cache to scriber's own directory before any HF imports
_cache = Path(user_cache_dir("scriber")) / "models"
_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HUB_CACHE", str(_cache))

from scriber.cli import parse_args, run_cache, run_cli
from scriber.app import run_app


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "__gui_worker__":
        from scriber.gui.worker import run_worker_from_stdin

        raise SystemExit(run_worker_from_stdin())

    args = parse_args()

    if args.subcommand == "app" or len(sys.argv) == 1:
        run_app()
    elif args.subcommand == "cache":
        run_cache(args)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
