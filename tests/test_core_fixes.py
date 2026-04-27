import io
import json
from types import SimpleNamespace
import sys

import numpy as np
import pytest

from scriber.core.transcribe import Segment


def test_cli_annotation_passes_loaded_audio_to_diarize(monkeypatch, tmp_path):
    from scriber.cli import run_cli

    audio = np.array([0.0, 0.1], dtype=np.float32)
    seen = {}

    monkeypatch.setattr("scriber.core.audio.load_audio", lambda path: audio)
    monkeypatch.setattr(
        "scriber.core.transcribe.transcribe",
        lambda *args, **kwargs: ([Segment(0.0, 1.0, "hello")], "en"),
    )

    def fake_diarize(value, hf_token):
        seen["audio"] = value
        seen["hf_token"] = hf_token
        return []

    monkeypatch.setattr("scriber.core.diarize.diarize", fake_diarize)
    monkeypatch.setattr("scriber.core.merge.merge", lambda segments, speakers: segments)
    monkeypatch.setattr("scriber.core.export.export", lambda segments, output_stem, **kwargs: seen.setdefault("output_stem", output_stem))
    monkeypatch.setattr("scriber.core.model_cache.is_model_cached", lambda model, backend: True)
    monkeypatch.setattr("scriber.core.model_cache.is_pyannote_cached", lambda: True)

    args = SimpleNamespace(
        files=[str(tmp_path / "input.m4a")],
        model="tiny",
        language=None,
        export="txt",
        output=str(tmp_path),
        annotate=True,
        hf_token="hf_test",
        device="cpu",
        translate=False,
    )

    run_cli(args)

    assert seen["audio"] is audio
    assert seen["hf_token"] == "hf_test"
    assert seen["output_stem"] == tmp_path / "input" / "input"


def test_cli_annotation_requires_hf_token():
    from scriber.cli import run_cli

    args = SimpleNamespace(
        files=[],
        model="tiny",
        language=None,
        export="txt",
        output=None,
        annotate=True,
        hf_token=None,
        device="cpu",
        translate=False,
    )

    with pytest.raises(SystemExit, match="--annotate requires --hf-token"):
        run_cli(args)


def test_cli_keyboard_interrupt_exits_cleanly(monkeypatch, tmp_path):
    from scriber.cli import run_cli

    monkeypatch.setattr("scriber.core.audio.load_audio", lambda path: np.array([0.0], dtype=np.float32))
    monkeypatch.setattr("scriber.core.transcribe.transcribe", lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr("scriber.core.model_cache.is_model_cached", lambda model, backend: True)

    args = SimpleNamespace(
        files=[str(tmp_path / "input.m4a")],
        model="tiny",
        language=None,
        export="txt",
        output=str(tmp_path),
        annotate=False,
        hf_token=None,
        device="cpu",
        translate=False,
    )

    with pytest.raises(SystemExit) as exc:
        run_cli(args)

    assert exc.value.code == 130


def test_cache_path_prints_scriber_cache(monkeypatch, tmp_path, capsys):
    from scriber.cli import run_cache

    cache = tmp_path / "models"
    monkeypatch.setattr("scriber.core.model_cache.scriber_cache", lambda: cache)

    run_cache(SimpleNamespace(cache_command="path"))

    assert capsys.readouterr().out.strip() == str(cache)


def test_cache_clear_only_clears_scriber_cache(monkeypatch, tmp_path, capsys):
    from scriber.cli import run_cache

    cache = tmp_path / "models"
    cache.mkdir()
    (cache / "model.bin").write_bytes(b"abc")
    (cache / "nested").mkdir()
    (cache / "nested" / "weights.bin").write_bytes(b"def")

    global_hf_cache = tmp_path / "huggingface"
    global_hf_cache.mkdir()
    (global_hf_cache / "other-model.bin").write_bytes(b"keep")

    monkeypatch.setattr("scriber.core.model_cache.scriber_cache", lambda: cache)

    run_cache(SimpleNamespace(cache_command="clear"))

    assert cache.exists()
    assert list(cache.iterdir()) == []
    assert (global_hf_cache / "other-model.bin").read_bytes() == b"keep"
    output = capsys.readouterr().out
    assert "Cleared Scriber model cache." in output
    assert str(cache) in output
    assert "Freed: 6 B" in output


def test_auto_backend_does_not_select_mlx_on_macos_13(monkeypatch):
    import scriber.core.transcribe as transcribe

    monkeypatch.setattr(transcribe.sys, "platform", "darwin")
    monkeypatch.setattr(transcribe.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(transcribe.platform, "mac_ver", lambda: ("13.6.0", ("", "", ""), ""))
    monkeypatch.setattr(transcribe, "_has_mlx_whisper", lambda: True)

    assert transcribe._get_backend("auto") == "faster-whisper"
    with pytest.raises(RuntimeError, match="macOS 14"):
        transcribe._get_backend("mlx")


def test_auto_backend_uses_faster_whisper_when_mlx_missing(monkeypatch):
    import scriber.core.transcribe as transcribe

    monkeypatch.setattr(transcribe.sys, "platform", "darwin")
    monkeypatch.setattr(transcribe.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(transcribe.platform, "mac_ver", lambda: ("14.0.0", ("", "", ""), ""))
    monkeypatch.setattr(transcribe, "_has_mlx_whisper", lambda: False)
    monkeypatch.setattr(transcribe, "_mlx_import_error", lambda: ImportError("No module named mlx_whisper"))

    assert transcribe._get_backend("auto") == "faster-whisper"
    with pytest.raises(RuntimeError, match="mlx[_-]whisper"):
        transcribe._get_backend("mlx")


def test_gpu_backend_uses_mlx_on_supported_mac(monkeypatch):
    import scriber.core.transcribe as transcribe

    monkeypatch.setattr(transcribe.sys, "platform", "darwin")
    monkeypatch.setattr(transcribe.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(transcribe.platform, "mac_ver", lambda: ("14.4.0", ("", "", ""), ""))
    monkeypatch.setattr(transcribe, "_has_mlx_whisper", lambda: True)

    assert transcribe._get_backend("gpu") == "mlx"


def test_faster_whisper_runtime_uses_library_auto_defaults():
    import scriber.core.transcribe as transcribe

    assert transcribe._faster_whisper_runtime("auto") == ("auto", "default")
    assert transcribe._faster_whisper_runtime("cpu") == ("cpu", "int8")


def test_faster_whisper_runtime_avoids_cuda_on_mac_gpu(monkeypatch):
    import scriber.core.transcribe as transcribe

    monkeypatch.setattr(transcribe.sys, "platform", "darwin")

    assert transcribe._faster_whisper_runtime("gpu") == ("auto", "default")


def test_gpu_init_error_is_user_friendly(monkeypatch):
    import scriber.core.transcribe as transcribe

    class BrokenWhisperModel:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("CUDA driver version is insufficient for CUDA runtime version")

    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=BrokenWhisperModel))

    with pytest.raises(RuntimeError, match="CUDA GPU mode is unavailable on this system"):
        transcribe._transcribe_faster_whisper(
            np.array([0.0], dtype=np.float32),
            model="large-v3-turbo",
            language=None,
            device="gpu",
            task="transcribe",
        )


def test_html_export_escapes_transcript_and_speaker(tmp_path):
    from scriber.core.export import export

    output = tmp_path / "transcript"
    segments = [
        Segment(0.0, 1.0, '<script>alert("x")</script> & text', speaker="A&B <lead>"),
        Segment(2.0, 3.0, "plain", speaker=None),
    ]

    export(segments, output, formats="html", pause_markers=True, pause_threshold=0.5)

    html = output.with_suffix(".html").read_text(encoding="utf-8")
    assert "<script>" not in html
    assert "A&amp;B &lt;lead&gt;" in html
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; text" in html
    assert "[pause 1s]" in html


def test_faster_whisper_turbo_uses_correct_hf_repo():
    from scriber.core.model_cache import model_repo

    assert model_repo("large-v3-turbo", "faster-whisper") == "mobiuslabsgmbh/faster-whisper-large-v3-turbo"


def test_batch_logs_loading_before_transcribing_and_resets_timer_at_transcription(monkeypatch, tmp_path):
    from scriber.core.batch import BatchConfig, run_batch

    monkeypatch.setattr("scriber.core.audio.load_audio", lambda path: np.array([0.0], dtype=np.float32))
    monkeypatch.setattr(
        "scriber.core.transcribe.transcribe",
        lambda *args, **kwargs: ([Segment(0.0, 1.0, "hello")], "en"),
    )
    monkeypatch.setattr("scriber.core.transcribe._get_backend", lambda device: "mlx")
    monkeypatch.setattr("scriber.core.export.export", lambda *args, **kwargs: None)
    monkeypatch.setattr("scriber.core.model_cache.is_model_cached", lambda model, backend: True)
    monkeypatch.setattr("scriber.core.model_cache.is_pyannote_cached", lambda: True)

    events = []

    def emit(event_type: str, message: str = "", **payload):
        events.append((event_type, message))

    config = BatchConfig(
        files=[tmp_path / "input.m4a"],
        output_folder=tmp_path / "out",
        model="large-v3-turbo",
        device="auto",
        export="txt",
    )

    run_batch(config, emit)

    logged_messages = [message for event_type, message in events if event_type == "log"]
    load_index = logged_messages.index("  Loading audio...")
    transcribe_index = logged_messages.index("  Transcribing...")

    assert load_index < transcribe_index

    reset_indices = [i for i, (event_type, _) in enumerate(events) if event_type == "reset_timer"]
    transcribe_log_event_index = next(
        i for i, (event_type, message) in enumerate(events)
        if event_type == "log" and message == "  Transcribing..."
    )
    assert reset_indices == [transcribe_log_event_index - 1]


def test_worker_runtime_emits_ready_before_running_batch(monkeypatch):
    from scriber.gui.worker_runtime import run_worker_from_stdin

    seen = {"order": []}

    def fake_run_batch(config, emit):
        seen["order"].append("run_batch")
        seen["files"] = [str(path) for path in config.files]

    monkeypatch.setattr("scriber.gui.worker_runtime._prewarm_runtime", lambda: seen["order"].append("prewarm"))
    monkeypatch.setattr("scriber.gui.worker_runtime.run_batch", fake_run_batch)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"files": ["input.m4a"], "device": "auto", "model": "large-v3-turbo"})),
    )
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout)

    assert run_worker_from_stdin() == 0
    lines = stdout.getvalue().splitlines()
    assert json.loads(lines[0])["type"] == "ready"
    assert seen["order"] == ["prewarm", "run_batch"]
    assert seen["files"] == ["input.m4a"]


def test_worker_runtime_prewarm_calls_audio_and_transcription_helpers(monkeypatch):
    from scriber.gui.worker_runtime import _prewarm_runtime

    seen = []

    monkeypatch.setattr("scriber.core.audio.prewarm_audio_backend", lambda: seen.append("audio"))
    monkeypatch.setattr(
        "scriber.core.transcribe.prewarm_transcription_backend",
        lambda: seen.append("transcribe"),
    )

    _prewarm_runtime()

    assert seen == ["audio", "transcribe"]
