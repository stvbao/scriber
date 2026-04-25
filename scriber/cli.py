import argparse
import os
import sys
import threading
from time import perf_counter


def parse_args():
    parser = argparse.ArgumentParser(
        prog="scriber",
        description="Offline transcription for qualitative researchers",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # GUI subcommand
    subparsers.add_parser("app", help="Launch the GUI")

    # Cache subcommands
    cache = subparsers.add_parser("cache", help="Manage Scriber model cache")
    cache_subparsers = cache.add_subparsers(dest="cache_command", required=True)
    cache_subparsers.add_parser("path", help="Print Scriber model cache path")
    cache_subparsers.add_parser("clear", help="Clear Scriber model cache")

    # Transcribe subcommand
    transcribe = subparsers.add_parser("transcribe", help="Transcribe audio files")
    transcribe.add_argument("files", nargs="+", help="Audio files to transcribe")
    transcribe.add_argument(
        "--model", default="large-v3-turbo",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"],
        help="Whisper model to use (default: large-v3-turbo)",
    )
    transcribe.add_argument(
        "--language", default=None,
        help="Language code e.g. en, zh, fr (default: auto-detect)",
    )
    transcribe.add_argument(
        "--export", default="txt",
        choices=["txt", "srt", "vtt", "json", "md", "html", "all"],
        help="Export format (default: txt)",
    )
    transcribe.add_argument(
        "--output", default=None,
        help="Output directory (default: same as input file)",
    )
    transcribe.add_argument(
        "--annotate", action="store_true",
        help="Enable speaker annotation (requires --hf-token)",
    )
    transcribe.add_argument(
        "--hf-token", default=None,
        help="HuggingFace token for speaker annotation",
    )
    transcribe.add_argument(
        "--device", default="auto",
        choices=["auto", "cpu", "gpu", "mlx"],
        help="Device to use (default: auto)",
    )
    transcribe.add_argument(
        "--translate", action="store_true",
        help="Translate audio to English (instead of transcribing in source language)",
    )

    return parser.parse_args()


def run_cache(args):
    import shutil

    from scriber.core.model_cache import scriber_cache

    console = _Console()
    cache = scriber_cache()

    if args.cache_command == "path":
        console.line(str(cache))
        return

    if args.cache_command == "clear":
        freed = _path_size(cache)
        if cache.exists() or cache.is_symlink():
            if cache.is_dir() and not cache.is_symlink():
                shutil.rmtree(cache)
            else:
                cache.unlink()
        cache.mkdir(parents=True, exist_ok=True)

        console.line(console.style("Cleared Scriber model cache.", "green"))
        console.line(f"Path: {cache}")
        console.line(f"Freed: {_format_bytes(freed)}")
        return

    raise SystemExit(f"Unknown cache command: {args.cache_command}")


def run_cli(args):
    if args.annotate and not args.hf_token:
        raise SystemExit("--annotate requires --hf-token")

    from pathlib import Path
    from scriber.core.batch import BatchConfig, run_batch

    config = BatchConfig(
        files=[Path(file) for file in args.files],
        output_folder=Path(args.output) if args.output else None,
        language=args.language,
        device=args.device,
        export=args.export,
        model=args.model,
        hf_token=args.hf_token,
        annotate=args.annotate,
        translate=args.translate,
    )
    console = _Console()
    renderer = _BatchConsoleRenderer(console)

    try:
        result = run_batch(config, renderer.emit)
    except KeyboardInterrupt:
        renderer.abort()
        console.line("")
        console.line(console.style("Stopped by user.", "yellow"))
        console.line(f"Completed {renderer.completed_before_stop}/{len(args.files)} file(s) before stop.")
        sys.stdout.flush()
        sys.stderr.flush()
        raise SystemExit(130)

    renderer.finish()
    if result.failed:
        raise SystemExit(1)


class _BatchConsoleRenderer:
    def __init__(self, console):
        self.console = console
        self.activity = None
        self.progress_active = False
        self.last_progress = None
        self.current_index = 0
        self.pending_log = None

    @property
    def completed_before_stop(self) -> int:
        return max(0, self.current_index - 1)

    def emit(self, event_type: str, message: str = "", **payload) -> None:
        if event_type == "file_start":
            self._flush_pending_log()
            self.current_index = int(payload.get("index") or 0)
            return
        if event_type == "log":
            if self.console.progress and _is_activity_start_log(message):
                self._finish_replace_if_needed()
                self.pending_log = message
                return
            self._flush_pending_log()
            self._finish_replace_if_needed()
            self.console.line(self._style_log(message))
            return
        if event_type == "log_replace":
            self._flush_pending_log()
            self.last_progress = message
            if self.console.progress:
                self.console.replace(message)
                self.progress_active = True
            return
        if event_type == "finish_replace":
            self._flush_pending_log()
            self._finish_replace_if_needed()
            return
        if event_type == "resume_pulse":
            if not self._pending_log_matches_activity(message):
                self._flush_pending_log()
            else:
                self.pending_log = None
            if self.console.progress:
                self.activity = self.console.activity(message)
            return
        if event_type == "suspend_pulse":
            self._stop_activity()
            return

    def finish(self) -> None:
        self._flush_pending_log()
        self._stop_activity()
        self._finish_replace_if_needed()

    def abort(self) -> None:
        self._stop_activity()
        if self.progress_active:
            self.console.clear_replace()
        self.progress_active = False
        self.last_progress = None
        self.pending_log = None

    def _stop_activity(self) -> None:
        if self.activity:
            self.activity.fail()
            self.activity = None

    def _finish_replace_if_needed(self) -> None:
        if self.progress_active:
            self.console.finish_replace()
        elif self.last_progress and not self.console.progress:
            self.console.line(self.last_progress)
        self.progress_active = False
        self.last_progress = None

    def _flush_pending_log(self) -> None:
        if not self.pending_log:
            return
        self.console.line(self._style_log(self.pending_log))
        self.pending_log = None

    def _pending_log_matches_activity(self, label: str) -> bool:
        return bool(self.pending_log and self.pending_log.strip() == f"{label}...")

    def _style_log(self, message: str) -> str:
        stripped = message.strip()
        if not stripped:
            return message
        if stripped == "Scriber":
            return self.console.style(message, "cyan", "bold")
        if set(stripped) == {"─"} or stripped.startswith("["):
            return self.console.style(message, "cyan")
        if "model:" in stripped:
            return self.console.style(message, "cyan")
        if (
            stripped.startswith("✓")
            or stripped.startswith("Saved to:")
            or stripped.startswith("Output folder:")
            or stripped.startswith("Completed ")
            or "complete in" in stripped
            or stripped.startswith("Done in")
        ):
            return self.console.style(message, "green")
        if stripped.startswith("⚠") or "no speaker label" in stripped:
            return self.console.style(message, "yellow")
        if stripped.startswith("✗") or stripped.startswith("Error:"):
            return self.console.style(message, "red")
        if stripped.startswith("Audio length:"):
            return self.console.style(message, "dim")
        return message


def _is_activity_start_log(message: str) -> bool:
    return message.strip() in {
        "Transcribing...",
        "Translating to English...",
        "Annotating speakers...",
    }


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:
        return f"{h}h {m}m {s:.1f}s"
    if m:
        return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"


def _path_size(path) -> int:
    path = os.fspath(path)
    if not os.path.exists(path):
        return 0
    if os.path.isfile(path) and not os.path.islink(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for name in files:
            file_path = os.path.join(root, name)
            if os.path.islink(file_path):
                continue
            try:
                total += os.path.getsize(file_path)
            except OSError:
                pass
    return total


def _format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024


class _Console:
    _CODES = {
        "bold": "\033[1m",
        "dim": "\033[2m",
        "cyan": "\033[36m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
    }
    _RESET = "\033[0m"

    def __init__(self):
        self.color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
        self.progress = sys.stdout.isatty()
        self._lock = threading.Lock()

    def style(self, text: str, *styles: str) -> str:
        if not self.color:
            return text
        codes = "".join(self._CODES[s] for s in styles if s in self._CODES)
        return f"{codes}{text}{self._RESET}" if codes else text

    def line(self, text: str = "") -> None:
        with self._lock:
            print(text, flush=True)

    def replace(self, text: str) -> None:
        with self._lock:
            sys.stdout.write(f"\r{text}\033[K")
            sys.stdout.flush()

    def finish_replace(self) -> None:
        with self._lock:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def clear_replace(self) -> None:
        with self._lock:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

    def activity(self, label: str):
        return _Activity(self, label)


class _Activity:
    _FRAMES = ("[●○○○○]", "[○●○○○]", "[○○●○○]", "[○○○●○]", "[○○○○●]")

    def __init__(self, console: _Console, label: str):
        self.console = console
        self.label = label
        self.start = perf_counter()
        self.done = threading.Event()
        self.thread = None
        if console.progress:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        else:
            console.line(f"  {label}...")

    def _run(self) -> None:
        idx = 0
        while not self.done.is_set():
            elapsed = self.console.style(f"{_fmt(perf_counter() - self.start)} elapsed", "dim")
            frame = self.console.style(self._FRAMES[idx % len(self._FRAMES)], "cyan")
            self.console.replace(f"  {self.label}... {frame} {elapsed}")
            idx += 1
            self.done.wait(0.5)

    def complete(self, message: str) -> None:
        self._stop()
        self.console.line(self.console.style(f"  {message}", "green"))

    def fail(self) -> None:
        self._stop()

    def _stop(self) -> None:
        self.done.set()
        if self.thread:
            self.thread.join()
            self.console.clear_replace()
