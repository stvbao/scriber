from __future__ import annotations
from pathlib import Path
from time import perf_counter

from PyQt6.QtCore import QThread, pyqtSignal


class Worker(QThread):
    log         = pyqtSignal(str)   # append new line
    log_replace = pyqtSignal(str)   # overwrite last line

    done = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._stop  = False

    def stop(self):
        self._stop = True

    def _emit(self, msg: str):
        if msg.startswith("\r"):
            self.log_replace.emit(msg[1:])
        else:
            self.log.emit(msg)

    def run(self):
        cfg           = self.config
        files         = cfg["files"]
        output_folder = Path(cfg["output_folder"])
        language      = cfg["language"] or None
        device        = cfg["device"]
        export        = cfg["export"]
        model         = cfg["model"]
        hf_token      = cfg["hf_token"] or None
        num_speakers  = cfg["num_speakers"]

        if not files:
            self.log.emit("No files selected.")
            self.done.emit()
            return

        self.log.emit("─" * 40)
        self.log.emit(f"Found {len(files)} file(s) to process...")

        from scriber.core.audio import load_audio
        from scriber.core.transcribe import transcribe, _get_backend
        from scriber.core.diarize import diarize
        from scriber.core.merge import merge
        from scriber.core.export import export as do_export
        from scriber.core.download import download_model
        from platformdirs import user_cache_dir

        backend       = _get_backend(device)
        backend_label = "MLX" if backend == "mlx" else "faster-whisper"
        cache         = Path(user_cache_dir("scriber")) / "models"

        failed      = []
        batch_start = perf_counter()

        for i, file in enumerate(files, 1):
            if self._stop:
                break

            self.log.emit(f"\n[{i}/{len(files)}] {file.name}")
            file_start = perf_counter()

            try:
                file_output = output_folder / file.stem
                file_output.mkdir(parents=True, exist_ok=True)

                # Load audio
                audio = load_audio(file)
                self.log.emit(f"  Audio length: {_fmt(len(audio) / 16000)}")

                # Download / load model
                self.log.emit("")
                if not _is_model_cached(model, backend, cache):
                    repo = _model_repo(model, backend)
                    self.log.emit(f"  Downloading {model} ({backend_label}) — first time only:")
                    download_model(
                        repo, cache, log=self._emit, hf_token=hf_token,
                        use_hf_default=(backend == "mlx"),
                    )
                    self.log.emit("  Download complete.")
                else:
                    self.log.emit(f"  Model: {model} ({backend_label}) — loaded from cache")

                # Transcribe
                self.log.emit("  Transcribing...")
                segments = transcribe(audio, model=model, language=language, device=device)
                self.log.emit("  Transcription complete.")

                # Diarize
                if hf_token:
                    self.log.emit("")
                    if not _is_pyannote_cached():
                        self.log.emit("  Downloading speaker annotation model — first time only:")
                        download_model(
                            "pyannote/speaker-diarization-community-1",
                            cache, log=self._emit, hf_token=hf_token,
                        )
                        self.log.emit("  Download complete.")
                    else:
                        self.log.emit("  Speaker annotation — loaded from cache")

                    speakers = diarize(
                        file,
                        hf_token=hf_token,
                        num_speakers=num_speakers if num_speakers > 0 else None,
                    )
                    segments = merge(segments, speakers)
                    unique = len({s.speaker for s in speakers})
                    self.log.emit(f"  Speakers identified: {unique}")
                    segments = [s for s in segments if s.speaker is not None]

                # Export
                self.log.emit("")
                out_stem = file_output / file.stem
                do_export(segments, out_stem, formats=export)
                elapsed = _fmt(perf_counter() - file_start)
                self.log.emit(f"✓  Done in {elapsed}")
                self.log.emit(f"   Saved to → {file_output}")

            except Exception as e:
                elapsed = _fmt(perf_counter() - file_start)
                failed.append(file.name)
                self.log.emit(f"✗  Failed: {file.name} ({elapsed})")
                self.log.emit(f"   Error: {e}")

        total = _fmt(perf_counter() - batch_start)
        self.log.emit(f"\n{'─' * 40}")
        if self._stop:
            self.log.emit(f"◼  Stopped after {total}.")
        elif failed:
            self.log.emit(f"⚠  {len(files) - len(failed)}/{len(files)} file(s) completed in {total}.")
            self.log.emit(f"   Failed: {', '.join(failed)}")
        else:
            self.log.emit(f"✓  {len(files)} file(s) transcribed in {total}.")
            self.log.emit(f"   Saved to → {output_folder}")
        self.done.emit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _model_repo(model: str, backend: str) -> str:
    if backend == "mlx":
        return f"mlx-community/whisper-{model}"
    return f"Systran/faster-whisper-{model}"


def _is_model_cached(model: str, backend: str, cache: Path) -> bool:
    if backend == "mlx":
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        return (hf_cache / f"models--mlx-community--whisper-{model}").exists()
    # faster-whisper uses HF hub format: models--Systran--faster-whisper-{model}
    return (cache / f"models--Systran--faster-whisper-{model}").exists()


def _is_pyannote_cached() -> bool:
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    return (hf_cache / "models--pyannote--speaker-diarization-community-1").exists()


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:  return f"{h}h {m}m {s:.1f}s"
    if m:  return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"
