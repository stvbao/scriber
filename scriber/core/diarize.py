"""Speaker diarization via pyannote v4."""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker: str


def diarize(audio_path: Path, hf_token: str) -> list[SpeakerSegment]:
    from pyannote.audio import Pipeline
    from platformdirs import user_cache_dir

    cache = Path(user_cache_dir("scriber")) / "models"

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        use_auth_token=hf_token,
        cache_dir=str(cache),
    )

    diarization = pipeline(str(audio_path))

    return [
        SpeakerSegment(start=turn.start, end=turn.end, speaker=speaker)
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]
