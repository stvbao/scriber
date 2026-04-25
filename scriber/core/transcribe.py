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
) -> list[Segment]:
    backend = _get_backend(device)

    if backend == "mlx":
        return _transcribe_mlx(audio, model, language)
    else:
        return _transcribe_faster_whisper(audio, model, language, device)


def _transcribe_mlx(audio: np.ndarray, model: str, language: str | None) -> list[Segment]:
    import mlx_whisper

    # MLX community models on HuggingFace
    model_map = {
        "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
        "large-v3":       "mlx-community/whisper-large-v3",
        "large-v2":       "mlx-community/whisper-large-v2",
        "medium":         "mlx-community/whisper-medium",
        "small":          "mlx-community/whisper-small",
        "base":           "mlx-community/whisper-base",
        "tiny":           "mlx-community/whisper-tiny",
    }
    repo = model_map.get(model, f"mlx-community/whisper-{model}")

    kwargs = {"path_or_hf_repo": repo}
    if language:
        kwargs["language"] = language

    result = mlx_whisper.transcribe(audio, **kwargs)
    return [
        Segment(start=s["start"], end=s["end"], text=s["text"].strip())
        for s in result["segments"]
        if s["text"].strip() and s["end"] > s["start"]
    ]


def _transcribe_faster_whisper(
    audio: np.ndarray,
    model: str,
    language: str | None,
    device: str,
) -> list[Segment]:
    from faster_whisper import WhisperModel
    from platformdirs import user_cache_dir
    from pathlib import Path

    cache = Path(user_cache_dir("scriber")) / "models"
    cache.mkdir(parents=True, exist_ok=True)

    compute_type = "float16" if device == "gpu" else "int8"
    fw_device = "cuda" if device == "gpu" else "cpu"

    fw_model = WhisperModel(
        model,
        device=fw_device,
        compute_type=compute_type,
        download_root=str(cache),
    )

    segments, _ = fw_model.transcribe(
        audio,
        language=language,
        vad_filter=True,
    )

    return [
        Segment(start=s.start, end=s.end, text=s.text.strip())
        for s in segments
    ]
