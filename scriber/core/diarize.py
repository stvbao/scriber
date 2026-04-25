"""Speaker diarization via pyannote v4."""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass

import numpy as np

_pipeline_cache: dict = {}


@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker: str


def diarize(
    audio: np.ndarray,
    hf_token: str,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> list[SpeakerSegment]:
    import torch
    from pyannote.audio import Pipeline

    cache_key = hf_token

    if cache_key not in _pipeline_cache:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-community-1",
            token=hf_token,
        )
        if torch.backends.mps.is_available():
            pipeline.to(torch.device("mps"))
        elif torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
        _pipeline_cache[cache_key] = pipeline

    pipeline = _pipeline_cache[cache_key]

    # Pass pre-loaded audio directly — avoids pyannote re-decoding the source file
    waveform = torch.from_numpy(audio).unsqueeze(0)  # [1, samples]
    input_audio = {"waveform": waveform, "sample_rate": 16000}

    kwargs = {}
    if num_speakers:
        kwargs["num_speakers"] = num_speakers
    elif min_speakers or max_speakers:
        if min_speakers:
            kwargs["min_speakers"] = min_speakers
        if max_speakers:
            kwargs["max_speakers"] = max_speakers

    output = pipeline(input_audio, **kwargs)

    return [
        SpeakerSegment(start=turn.start, end=turn.end, speaker=speaker)
        for turn, speaker in output.speaker_diarization
    ]
