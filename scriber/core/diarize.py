"""Speaker diarization via pyannote v4."""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker: str


def diarize(
    audio_path: Path,
    hf_token: str,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> list[SpeakerSegment]:
    from pyannote.audio import Pipeline
    from platformdirs import user_cache_dir

    cache = Path(user_cache_dir("scriber")) / "models"

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        token=hf_token,
        cache_dir=str(cache),
    )

    kwargs = {}
    if num_speakers:
        kwargs["num_speakers"] = num_speakers
    elif min_speakers or max_speakers:
        if min_speakers:
            kwargs["min_speakers"] = min_speakers
        if max_speakers:
            kwargs["max_speakers"] = max_speakers

    output = pipeline(str(audio_path), **kwargs)

    return [
        SpeakerSegment(start=turn.start, end=turn.end, speaker=speaker)
        for turn, speaker in output.speaker_diarization
    ]
