"""Transcription backend — auto-selects MLX (Apple Silicon) or faster-whisper."""

from __future__ import annotations
import sys
import platform
import numpy as np
from dataclasses import dataclass


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None


def _is_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"


def _get_backend(device: str) -> str:
    if device == "auto":
        return "mlx" if _is_apple_silicon() else "faster-whisper"
    if device == "mlx":
        return "mlx"
    return "faster-whisper"


def transcribe(
    audio: np.ndarray,
    model: str = "large-v3-turbo",
    language: str | None = None,
    device: str = "auto",
    task: str = "transcribe",
) -> tuple[list[Segment], str]:
    """Returns (segments, detected_language)."""
    backend = _get_backend(device)
    if backend == "mlx":
        return _transcribe_mlx(audio, model, language, task)
    else:
        return _transcribe_faster_whisper(audio, model, language, device, task)


def _transcribe_mlx(
    audio: np.ndarray,
    model: str,
    language: str | None,
    task: str,
) -> tuple[list[Segment], str]:
    import mlx_whisper

    model_map = {
        "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
        "large-v3":       "mlx-community/whisper-large-v3-mlx",
        "large-v2":       "mlx-community/whisper-large-v2-mlx",
        "medium":         "mlx-community/whisper-medium-mlx",
        "small":          "mlx-community/whisper-small-mlx",
        "base":           "mlx-community/whisper-base-mlx",
        "tiny":           "mlx-community/whisper-tiny-mlx",
    }
    repo = model_map.get(model, f"mlx-community/whisper-{model}")

    kwargs: dict = {"path_or_hf_repo": repo, "task": task}
    if language:
        kwargs["language"] = language

    result = mlx_whisper.transcribe(audio, **kwargs)
    segments = [
        Segment(start=s["start"], end=s["end"], text=s["text"].strip())
        for s in result["segments"]
        if s["text"].strip() and s["end"] > s["start"]
    ]
    return segments, result.get("language", language or "en")


def _transcribe_faster_whisper(
    audio: np.ndarray,
    model: str,
    language: str | None,
    device: str,
    task: str,
) -> tuple[list[Segment], str]:
    from faster_whisper import WhisperModel

    compute_type = "float16" if device == "gpu" else "int8"
    fw_device = "cuda" if device == "gpu" else "cpu"

    fw_model = WhisperModel(model, device=fw_device, compute_type=compute_type)

    segments_gen, info = fw_model.transcribe(
        audio,
        language=language,
        task=task,
        vad_filter=True,
    )
    segments = [
        Segment(start=s.start, end=s.end, text=s.text.strip())
        for s in segments_gen
    ]
    return segments, info.language
