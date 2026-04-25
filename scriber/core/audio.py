"""Audio loading and resampling via PyAV — no ffmpeg install required."""

from pathlib import Path
import numpy as np

TARGET_SR = 16_000


def load_audio(path: Path) -> np.ndarray:
    """Load any audio file and return a 16kHz mono float32 numpy array."""
    import av

    container = av.open(str(path))
    stream = next(s for s in container.streams if s.type == "audio")

    resampler = av.AudioResampler(
        format="fltp",
        layout="mono",
        rate=TARGET_SR,
    )

    chunks = []
    for frame in container.decode(stream):
        for resampled in resampler.resample(frame):
            chunks.append(resampled.to_ndarray()[0])

    # Flush resampler
    for resampled in resampler.resample(None):
        chunks.append(resampled.to_ndarray()[0])

    container.close()
    return np.concatenate(chunks).astype(np.float32)
