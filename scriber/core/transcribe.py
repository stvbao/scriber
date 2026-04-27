"""Transcription backend — auto-selects MLX (Apple Silicon) or faster-whisper."""

from __future__ import annotations
import sys
import platform
from importlib import import_module
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


def _is_macos_14_or_newer() -> bool:
    version = platform.mac_ver()[0]
    if not version:
        return False
    try:
        return int(version.split(".", 1)[0]) >= 14
    except ValueError:
        return False


def _has_mlx_whisper() -> bool:
    return _mlx_import_error() is None


def _mlx_import_error() -> Exception | None:
    try:
        import_module("mlx_whisper")
    except Exception as e:
        return e
    return None


def _can_use_mlx() -> bool:
    return _is_apple_silicon() and _is_macos_14_or_newer() and _has_mlx_whisper()


def _require_mlx() -> None:
    if not _is_apple_silicon():
        raise RuntimeError("MLX backend requires Apple Silicon.")
    if not _is_macos_14_or_newer():
        raise RuntimeError("MLX backend requires macOS 14 or newer.")
    error = _mlx_import_error()
    if error:
        raise RuntimeError(f"MLX backend is unavailable: {error}") from error


def _get_backend(device: str) -> str:
    if device == "auto":
        return "mlx" if _can_use_mlx() else "faster-whisper"
    if device == "mlx":
        _require_mlx()
        return "mlx"
    if device == "gpu" and sys.platform == "darwin" and _can_use_mlx():
        return "mlx"
    return "faster-whisper"


def _faster_whisper_runtime(device: str) -> tuple[str, str]:
    if device == "cpu":
        return "cpu", "int8"
    if device == "gpu":
        # macOS GPUs are served by MLX; if we ended up here, fall back to
        # faster-whisper's native auto-detection instead of forcing CUDA.
        if sys.platform == "darwin":
            return "auto", "default"
        return "cuda", "float16"
    return "auto", "default"


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
        try:
            return _transcribe_mlx(audio, model, language, task)
        except (ImportError, OSError):
            if device != "auto":
                raise
            return _transcribe_faster_whisper(audio, model, language, device, task)
    else:
        return _transcribe_faster_whisper(audio, model, language, device, task)


def _transcribe_mlx(
    audio: np.ndarray,
    model: str,
    language: str | None,
    task: str,
) -> tuple[list[Segment], str]:
    _require_mlx()

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

    fw_device, compute_type = _faster_whisper_runtime(device)

    try:
        fw_model = WhisperModel(model, device=fw_device, compute_type=compute_type)
    except Exception as error:
        raise _friendly_faster_whisper_error(error, device) from error

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


def _friendly_faster_whisper_error(error: Exception, requested_device: str) -> Exception:
    if requested_device != "gpu":
        return error

    details = str(error).strip()
    message = "CUDA GPU mode is unavailable on this system. Use Device: auto or cpu instead."
    if details:
        message = f"{message} Details: {details}"
    return RuntimeError(message)


def prewarm_transcription_backend(device: str = "auto") -> None:
    backend = _get_backend(device)
    if backend == "mlx":
        _require_mlx()
        return
    import_module("faster_whisper")
