"""Model download with progress reporting via a callback."""

from __future__ import annotations
from pathlib import Path
from typing import Callable
from tqdm import tqdm


def download_model(
    repo_id: str,
    cache_dir: Path | None,
    log: Callable[[str], None],
    hf_token: str | None = None,
    use_hf_default: bool = False,
) -> None:
    """
    Download a HuggingFace repo with progress.

    - use_hf_default=True  → downloads to ~/.cache/huggingface/hub (for MLX)
    - use_hf_default=False → downloads to cache_dir in HF hub format (for faster-whisper)
    """
    from huggingface_hub import snapshot_download

    class _LogTqdm(tqdm):
        def display(self, msg=None, pos=None):
            if self.total and self.n:
                mb_done  = self.n / 1_048_576
                mb_total = self.total / 1_048_576
                speed    = (self.format_dict.get("rate") or 0) / 1_048_576
                pct      = self.n / self.total * 100
                bar_fill = int(pct / 10)
                bar      = "█" * bar_fill + "░" * (10 - bar_fill)
                line     = (
                    f"  [{bar}] {mb_done:.0f} / {mb_total:.0f} MB"
                    f"  {speed:.1f} MB/s  ({pct:.0f}%)"
                )
                log(f"\r{line}")
            return True

    kwargs = dict(repo_id=repo_id, token=hf_token, tqdm_class=_LogTqdm)
    if not use_hf_default:
        kwargs["cache_dir"] = str(cache_dir)

    snapshot_download(**kwargs)
