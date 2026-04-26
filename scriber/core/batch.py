"""Shared batch transcription pipeline for CLI and GUI workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any, Callable


Emit = Callable[..., None]
TRANSLATION_MODEL = "large-v3"


@dataclass
class BatchConfig:
    files: list[Path]
    output_folder: Path | None = None
    language: str | None = None
    device: str = "auto"
    export: str = "txt"
    model: str = "large-v3-turbo"
    hf_token: str | None = None
    annotate: bool = False
    num_speakers: int = 0
    pause_markers: bool = False
    pause_threshold: float = 2.0
    translate: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "BatchConfig":
        output_folder = data.get("output_folder")
        hf_token = data.get("hf_token") or None
        return cls(
            files=[Path(file) for file in data.get("files", [])],
            output_folder=Path(output_folder) if output_folder else None,
            language=data.get("language") or None,
            device=data.get("device", "auto"),
            export=data.get("export", "txt"),
            model=data.get("model", "large-v3-turbo"),
            hf_token=hf_token,
            annotate=bool(data.get("annotate", bool(hf_token))),
            num_speakers=int(data.get("num_speakers") or 0),
            pause_markers=bool(data.get("pause_markers", False)),
            pause_threshold=float(data.get("pause_threshold", 2.0)),
            translate=bool(data.get("translate", False)),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "files": [str(file) for file in self.files],
            "output_folder": str(self.output_folder) if self.output_folder else None,
            "language": self.language or "",
            "device": self.device,
            "export": self.export,
            "model": self.model,
            "hf_token": self.hf_token,
            "annotate": self.annotate,
            "num_speakers": self.num_speakers,
            "pause_markers": self.pause_markers,
            "pause_threshold": self.pause_threshold,
            "translate": self.translate,
        }


@dataclass
class BatchResult:
    total_files: int
    failed: list[str] = field(default_factory=list)

    @property
    def completed(self) -> int:
        return self.total_files - len(self.failed)


def run_batch(config: BatchConfig | dict[str, Any], emit: Emit) -> BatchResult:
    if isinstance(config, dict):
        config = BatchConfig.from_mapping(config)

    files = config.files
    if not files:
        emit("log", "No files selected.")
        return BatchResult(total_files=0)

    emit("log", "─" * 40)
    emit("log", "Scriber")
    emit("log", f"Found {len(files)} file(s)")

    from scriber.core.audio import load_audio
    from scriber.core.transcribe import transcribe, _get_backend
    from scriber.core.diarize import diarize
    from scriber.core.merge import merge
    from scriber.core.export import export as do_export
    from scriber.core.download import download_model
    from scriber.core.model_cache import (
        PYANNOTE_LABEL,
        PYANNOTE_REPO,
        is_model_cached,
        is_pyannote_cached,
        model_repo,
    )

    failed: list[str] = []
    batch_start = perf_counter()

    for i, file in enumerate(files, 1):
        emit("file_start", file.name, index=i, total=len(files))
        emit("suspend_pulse")
        emit("log", f"\n[{i}/{len(files)}] {file.name}")
        emit("reset_timer")
        file_start = perf_counter()

        try:
            output_base = config.output_folder if config.output_folder else file.parent
            file_output = output_base / file.stem
            file_output.mkdir(parents=True, exist_ok=True)

            backend = _get_backend(config.device)
            backend_label = "MLX" if backend == "mlx" else "faster-whisper"

            emit("log", "  Loading audio...")
            emit("suspend_pulse")
            audio = load_audio(file)
            emit("log", f"  Audio length: {format_duration(len(audio) / 16000)}")

            if config.translate:
                eff_model = TRANSLATION_MODEL
                task = "translate"
                if eff_model != config.model:
                    emit("log", "  ⚠ Using large-v3 model (turbo doesn't support translation)")
            else:
                eff_model = config.model
                task = "transcribe"

            emit("log", "")
            emit("log", f"  Transcription model: {eff_model} ({backend_label})")
            if not is_model_cached(eff_model, backend):
                emit("log", "  Downloading, first time only...")
                emit("suspend_pulse")
                download_model(
                    model_repo(eff_model, backend),
                    log=_download_logger(emit),
                    hf_token=config.hf_token,
                )
                emit("finish_replace")

            if config.annotate:
                emit("log", f"  Annotation model: {PYANNOTE_LABEL}")
                if not is_pyannote_cached():
                    emit("log", "  Downloading, first time only...")
                    emit("suspend_pulse")
                    download_model(
                        PYANNOTE_REPO,
                        log=_download_logger(emit),
                        hf_token=config.hf_token,
                    )
                    emit("finish_replace")

            _disable_hf_progress_bars()

            action = "Transcribing and translating" if task == "translate" else "Transcribing"
            emit("log", "")
            emit("log", f"  {action}...")
            step_start = perf_counter()
            emit("resume_pulse", action)
            segments, _ = transcribe(
                audio,
                model=eff_model,
                language=config.language,
                device=config.device,
                task=task,
            )
            emit("suspend_pulse")
            emit("log", f"  {action} complete in {format_duration(perf_counter() - step_start)}.")

            if config.annotate:
                emit("log", "")
                emit("reset_timer")
                emit("log", "  Annotating speakers...")
                step_start = perf_counter()
                emit("resume_pulse", "Annotating speakers")
                diarize_kwargs = {}
                if config.num_speakers > 0:
                    diarize_kwargs["num_speakers"] = config.num_speakers
                speakers = diarize(audio, hf_token=config.hf_token, **diarize_kwargs)
                emit("suspend_pulse")
                emit("log", f"  Annotating complete in {format_duration(perf_counter() - step_start)}.")
                segments = merge(segments, speakers)
                unique = len({s.speaker for s in speakers})
                emit("log", f"  Speakers identified: {unique}")

            emit("log", "")
            out_stem = file_output / file.stem
            emit("log", f"  Exporting: {format_export(config.export)}")
            do_export(
                segments,
                out_stem,
                formats=config.export,
                pause_markers=config.pause_markers,
                pause_threshold=config.pause_threshold,
            )
            elapsed = format_duration(perf_counter() - file_start)
            emit("log", f"  Saved to: {file_output}")
            emit("log", "")
            emit("log", f"  Done in {elapsed}")

        except Exception as e:
            emit("suspend_pulse")
            emit("finish_replace")
            elapsed = format_duration(perf_counter() - file_start)
            failed.append(file.name)
            emit("log", f"✗ Failed: {file.name} ({elapsed})")
            emit("log", f"  Error: {e}")

    total = format_duration(perf_counter() - batch_start)
    emit("log", f"\n{'─' * 40}")
    if failed:
        emit("log", f"⚠ {len(files) - len(failed)}/{len(files)} file(s) completed in {total}.")
        emit("log", f"  Failed: {', '.join(failed)}")
    else:
        emit("log", f"Completed {len(files)}/{len(files)} file(s) in {total}.")
        if config.output_folder:
            emit("log", f"Output folder: {config.output_folder}")

    return BatchResult(total_files=len(files), failed=failed)


def _download_logger(emit: Emit):
    def log(msg: str):
        if msg.startswith("\r"):
            emit("log_replace", msg[1:])
        else:
            emit("log", msg)

    return log


def format_duration(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:
        return f"{h}h {m}m {s:.1f}s"
    if m:
        return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"


def format_export(formats: str) -> str:
    if formats == "all":
        return "txt, srt, vtt, json, md, html"
    return formats


def _disable_hf_progress_bars() -> None:
    try:
        from huggingface_hub.utils import disable_progress_bars
    except Exception:
        return
    disable_progress_bars()
