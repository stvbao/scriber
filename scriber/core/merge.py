"""Merge transcript segments with speaker diarization labels."""

from __future__ import annotations
from scriber.core.transcribe import Segment
from scriber.core.diarize import SpeakerSegment


def merge(
    segments: list[Segment],
    speakers: list[SpeakerSegment],
) -> list[Segment]:
    """Assign speaker label to each transcript segment by overlap."""
    for seg in segments:
        seg.speaker = _find_speaker(seg.start, seg.end, speakers)
    return segments


def _find_speaker(
    start: float,
    end: float,
    speakers: list[SpeakerSegment],
) -> str | None:
    """Return the speaker with the most overlap with the given time range."""
    best_speaker = None
    best_overlap = 0.0

    for sp in speakers:
        overlap = min(end, sp.end) - max(start, sp.start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = sp.speaker

    return best_speaker
