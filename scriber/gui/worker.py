from __future__ import annotations
from pathlib import Path
from time import perf_counter

from PyQt6.QtCore import QThread, pyqtSignal


class Worker(QThread):
    log           = pyqtSignal(str)   # append new line
    log_replace   = pyqtSignal(str)   # overwrite last line
    reset_timer   = pyqtSignal()      # reset elapsed timer for new file
    suspend_pulse = pyqtSignal()      # pause the pulse while busy (no log_replace)

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
        hf_token        = cfg["hf_token"] or None
        num_speakers    = cfg["num_speakers"]
        pause_markers   = cfg["pause_markers"]
        pause_threshold = cfg["pause_threshold"]
        translate       = cfg.get("translate", False)

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

        backend       = _get_backend(device)
        backend_label = "MLX" if backend == "mlx" else "faster-whisper"

        # Translation: large-v3 required (turbo doesn't support it)
        TRANSLATION_MODEL = "large-v3"

        failed      = []
        batch_start = perf_counter()

        for i, file in enumerate(files, 1):
            if self._stop:
                break
            self.log.emit(f"\n[{i}/{len(files)}] {file.name}")
            self.reset_timer.emit()
            file_start = perf_counter()

            try:
                file_output = output_folder / file.stem
                file_output.mkdir(parents=True, exist_ok=True)

                # ── Audio ────────────────────────────────────────────────────
                self.log.emit("  Loading audio...")
                self.suspend_pulse.emit()
                audio = load_audio(file)
                self.log.emit(f"  Audio length: {_fmt(len(audio) / 16000)}")

                # Determine effective model and task
                if translate:
                    eff_model = TRANSLATION_MODEL
                    task      = "translate"
                else:
                    eff_model = model
                    task      = "transcribe"

                # ── Models ───────────────────────────────────────────────────
                self.log.emit("")
                self.log.emit(f"  Transcription model: {eff_model} ({backend_label})")
                if not _is_model_cached(eff_model, backend):
                    self.log.emit("  Downloading, first time only...")
                    self.suspend_pulse.emit()
                    download_model(_model_repo(eff_model, backend), log=self._emit, hf_token=hf_token)

                if hf_token:
                    self.log.emit("  Annotation model: speaker-diarization-community-1")
                    if not _is_pyannote_cached():
                        self.log.emit("  Downloading, first time only...")
                        self.suspend_pulse.emit()
                        download_model(
                            "pyannote/speaker-diarization-community-1",
                            log=self._emit, hf_token=hf_token,
                        )

                # ── Transcribe ───────────────────────────────────────────────
                action = "Translating to English" if task == "translate" else "Transcribing"
                self.log.emit("")
                self.log.emit(f"  {action}...")
                segments, _ = transcribe(audio, model=eff_model, language=language, device=device, task=task)
                self.log.emit(f"  {action} complete.")

                # ── Annotate ─────────────────────────────────────────────────
                if hf_token:
                    self.log.emit("")
                    self.reset_timer.emit()
                    self.log.emit("  Annotating speakers...")
                    speakers = diarize(
                        audio,
                        hf_token=hf_token,
                        num_speakers=num_speakers if num_speakers > 0 else None,
                    )
                    segments = merge(segments, speakers)
                    unique = len({s.speaker for s in speakers})
                    self.log.emit(f"  Speakers identified: {unique}")
                    segments = [s for s in segments if s.speaker is not None]

                # ── Export ───────────────────────────────────────────────────
                self.log.emit("")
                out_stem = file_output / file.stem
                do_export(segments, out_stem, formats=export,
                          pause_markers=pause_markers, pause_threshold=pause_threshold)
                elapsed = _fmt(perf_counter() - file_start)
                self.log.emit(f"✓ Done in {elapsed}")
                self.log.emit(f"  Saved to:{file_output}")

            except Exception as e:
                elapsed = _fmt(perf_counter() - file_start)
                failed.append(file.name)
                self.log.emit(f"✗ Failed: {file.name} ({elapsed})")
                self.log.emit(f"  Error: {e}")

        total = _fmt(perf_counter() - batch_start)
        self.log.emit(f"\n{'─' * 40}")
        if self._stop:
            self.log.emit(f"◼ Stopped after {total}.")
        elif failed:
            self.log.emit(f"⚠ {len(files) - len(failed)}/{len(files)} file(s) completed in {total}.")
            self.log.emit(f"  Failed: {', '.join(failed)}")
        else:
            self.log.emit(f"✓ {len(files)} file(s) transcribed in {total}.")
            self.log.emit(f"  Saved to:{output_folder}")
        self.done.emit()


# ── Helpers ───────────────────────────────────────────────────────────────────

_MLX_REPOS = {
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3":       "mlx-community/whisper-large-v3-mlx",
    "large-v2":       "mlx-community/whisper-large-v2-mlx",
    "medium":         "mlx-community/whisper-medium-mlx",
    "small":          "mlx-community/whisper-small-mlx",
    "base":           "mlx-community/whisper-base-mlx",
    "tiny":           "mlx-community/whisper-tiny-mlx",
}


def _model_repo(model: str, backend: str) -> str:
    if backend == "mlx":
        return _MLX_REPOS.get(model, f"mlx-community/whisper-{model}")
    return f"Systran/faster-whisper-{model}"


def _scriber_cache() -> Path:
    from platformdirs import user_cache_dir
    return Path(user_cache_dir("scriber")) / "models"


def _is_model_cached(model: str, backend: str) -> bool:
    cache = _scriber_cache()
    if backend == "mlx":
        repo = _MLX_REPOS.get(model, f"mlx-community/whisper-{model}")
        slug = repo.replace("/", "--")
        return (cache / f"models--{slug}").exists()
    return (cache / f"models--Systran--faster-whisper-{model}").exists()


def _is_pyannote_cached() -> bool:
    return (_scriber_cache() / "models--pyannote--speaker-diarization-community-1").exists()


def _is_nllb_cached() -> bool:
    return (_scriber_cache() / "models--facebook--nllb-200-distilled-600M").exists()


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:  return f"{h}h {m}m {s:.1f}s"
    if m:  return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"
