"""Model download with progress reporting via a callback."""

from __future__ import annotations
import io
from typing import Callable
from tqdm import tqdm


def download_model(
    repo_id: str,
    log: Callable[[str], None],
    hf_token: str | None = None,
) -> None:
    """Download a HuggingFace repo with progress. Cache dir comes from HF_HUB_CACHE."""
    from huggingface_hub import snapshot_download

    class _LogTqdm(tqdm):
        def __init__(self, *args, **kwargs):
            kwargs["file"] = io.StringIO()  # suppress all default tqdm stream output
            super().__init__(*args, **kwargs)

        def display(self, msg=None, pos=None):
            if self.total and self.n:
                mb_total = self.total / 1_048_576
                if mb_total < 1:
                    return True  # skip file-count tqdm instances (not byte-based)
                speed = (self.format_dict.get("rate") or 0) / 1_048_576
                if not speed:
                    return True
                mb_done  = self.n / 1_048_576
                pct      = self.n / self.total * 100
                bar_fill = int(pct / 10)
                bar      = "=" * bar_fill + "-" * (10 - bar_fill)
                line     = (
                    f"  [{bar}] {pct:.0f}%"
                    f"  {mb_done:.0f}/{mb_total:.0f} MB"
                    f"  {speed:.1f} MB/s"
                )
                log(f"\r{line}")
            return True

    snapshot_download(repo_id=repo_id, token=hf_token, tqdm_class=_LogTqdm)
