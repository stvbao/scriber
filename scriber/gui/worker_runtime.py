from __future__ import annotations

import json
import sys

from scriber.core.batch import BatchConfig, run_batch


def run_worker_from_stdin() -> int:
    _prewarm_runtime()
    _emit_process_event("ready")

    try:
        config = BatchConfig.from_mapping(json.loads(sys.stdin.read()))
    except Exception as e:
        _emit_process_event("log", "✗ Worker process could not read its configuration.")
        _emit_process_event("log", f"  Error: {e}")
        return 2

    try:
        run_batch(config, _emit_process_event)
    except Exception as e:
        _emit_process_event("log", "✗ Worker process failed.")
        _emit_process_event("log", f"  Error: {e}")
        return 1
    return 0


def _emit_process_event(event_type: str, message: str = "", **payload):
    event = {"type": event_type, "message": message, **payload}
    print(json.dumps(event, ensure_ascii=False), flush=True)


def _prewarm_runtime() -> None:
    try:
        from scriber.core.audio import prewarm_audio_backend

        prewarm_audio_backend()
    except Exception:
        pass

    try:
        from scriber.core.transcribe import prewarm_transcription_backend

        prewarm_transcription_backend()
    except Exception:
        pass
