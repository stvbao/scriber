"""Model download with progress reporting via a callback."""

from __future__ import annotations
from pathlib import Path
from typing import Callable
from tqdm import tqdm


def download_model(
    repo_id: str,
    cache_dir: Path,
    log: Callable[[str], None],
    hf_token: str | None = None,
) -> Path:
    """Download a HuggingFace repo to cache_dir, reporting progress via log()."""
    from huggingface_hub import snapshot_download

    class _LogTqdm(tqdm):
        def display(self, msg=None, pos=None):
            if self.total and self.n:
                mb_done  = self.n / 1_048_576
                mb_total = self.total / 1_048_576
                speed    = self.format_dict.get("rate") or 0
                speed_mb = (speed or 0) / 1_048_576
                pct      = self.n / self.total * 100
                bar_fill = int(pct / 10)
                bar      = "█" * bar_fill + "░" * (10 - bar_fill)
                line     = (
                    f"  [{bar}] {mb_done:.0f} / {mb_total:.0f} MB"
                    f"  {speed_mb:.1f} MB/s  ({pct:.0f}%)"
                )
                log(f"\r{line}")
            return True

    local_dir = cache_dir / repo_id.replace("/", "--")
    local_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        token=hf_token,
        tqdm_class=_LogTqdm,
    )
    return local_dir
