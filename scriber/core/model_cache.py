from __future__ import annotations

from pathlib import Path


PYANNOTE_REPO = "pyannote/speaker-diarization-community-1"
PYANNOTE_LABEL = "speaker-diarization-community-1"

MLX_REPOS = {
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "tiny": "mlx-community/whisper-tiny-mlx",
}


def model_repo(model: str, backend: str) -> str:
    if backend == "mlx":
        return MLX_REPOS.get(model, f"mlx-community/whisper-{model}")
    return f"Systran/faster-whisper-{model}"


def scriber_cache() -> Path:
    from platformdirs import user_cache_dir

    return Path(user_cache_dir("scriber")) / "models"


def is_model_cached(model: str, backend: str) -> bool:
    repo = model_repo(model, backend)
    return (scriber_cache() / f"models--{repo.replace('/', '--')}").exists()


def is_pyannote_cached() -> bool:
    return (scriber_cache() / f"models--{PYANNOTE_REPO.replace('/', '--')}").exists()


def is_nllb_cached() -> bool:
    return (scriber_cache() / "models--facebook--nllb-200-distilled-600M").exists()
