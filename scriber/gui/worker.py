from __future__ import annotations
from pathlib import Path
from time import perf_counter

from PyQt6.QtCore import QThread, pyqtSignal


class Worker(QThread):
    log   = pyqtSignal(str)
    done  = pyqtSignal()

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._stop  = False

    def stop(self):
        self._stop = True

    def run(self):
        cfg           = self.config
        files         = cfg["files"]
        output_folder = Path(cfg["output_folder"])
        language      = cfg["language"] or None
        device        = cfg["device"]
        export        = cfg["export"]
        model         = cfg["model"]
        hf_token      = cfg["hf_token"] or None
        num_speakers  = cfg["num_speakers"]

        if not files:
            self.log.emit("No files selected.")
            self.done.emit()
            return

        self.log.emit("─" * 40)
        self.log.emit(f"Found {len(files)} file(s) to process...")
        self.log.emit(f"Model: {model}  |  Device: {device}")

        from scriber.core.audio import load_audio
        from scriber.core.transcribe import transcribe
        from scriber.core.diarize import diarize
        from scriber.core.merge import merge
        from scriber.core.export import export as do_export

        failed      = []
        batch_start = perf_counter()

        for i, file in enumerate(files, 1):
            if self._stop:
                break

            self.log.emit(f"\nProcessing {i}/{len(files)}: {file.name}")
            file_start = perf_counter()

            try:
                output_folder.mkdir(parents=True, exist_ok=True)

                self.log.emit("  Loading audio...")
                audio = load_audio(file)

                self.log.emit(f"  Transcribing ({device})...")
                segments = transcribe(audio, model=model, language=language, device=device)
                self.log.emit(f"  {len(segments)} segments transcribed")

                if hf_token:
                    self.log.emit("  Running speaker annotation...")
                    speakers = diarize(
                        file,
                        hf_token=hf_token,
                        num_speakers=num_speakers if num_speakers > 0 else None,
                    )
                    segments = merge(segments, speakers)
                    unique = len({s.speaker for s in speakers})
                    self.log.emit(f"  {unique} speaker(s) identified")

                # Filter hallucination segments (no speaker assigned when annotation on)
                if hf_token:
                    segments = [s for s in segments if s.speaker is not None]

                self.log.emit("  Exporting...")
                out_stem = output_folder / file.stem
                do_export(segments, out_stem, formats=export)

                elapsed = _fmt(perf_counter() - file_start)
                self.log.emit(f"✓  Done: {file.name} ({elapsed})")

            except Exception as e:
                elapsed = _fmt(perf_counter() - file_start)
                failed.append(file.name)
                self.log.emit(f"✗  Failed: {file.name} ({elapsed})")
                self.log.emit(f"   Error: {e}")

        total = _fmt(perf_counter() - batch_start)
        self.log.emit(f"\n{'─' * 40}")
        if self._stop:
            self.log.emit(f"◼  Stopped after {total}.")
        elif failed:
            self.log.emit(f"⚠  Finished with errors — {len(files) - len(failed)}/{len(files)} file(s) in {total}.")
            self.log.emit(f"   Failed: {', '.join(failed)}")
        else:
            self.log.emit(f"✓  All done — {len(files)} file(s) transcribed in {total}.")
        self.done.emit()


def _fmt(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    if h:  return f"{h}h {m}m {s:.1f}s"
    if m:  return f"{m}m {s:.1f}s"
    return f"{seconds:.1f}s"
