# Scriber — Build Plan

Offline transcription app for qualitative researchers. No cloud, no dependencies to install, no terminal knowledge required.

---

## What Scriber Is

A desktop app + CLI tool that transcribes audio files (interviews, focus groups, field recordings) entirely on the user's machine. Built for social scientists and qualitative researchers.

**Key principles:**
- Zero install friction — download and run, nothing else
- No internet required after first model download
- Works on Mac and Windows
- Fast on Apple Silicon, solid on Windows CPU/GPU

---

## Stack

| Component | Technology | Why |
|---|---|---|
| GUI | PyQt6 | Cross-platform, already built |
| Mac transcription | MLX-Whisper | Fastest on Apple Silicon |
| Windows/Linux transcription | faster-whisper | No k2, no WhisperX issues, works on CPU |
| Audio loading | PyAV | Bundled ffmpeg libs, no separate install |
| Speaker annotation | pyannote v4 | Best open-source diarization |
| Packaging | PyInstaller | Single binary, no Python install needed |
| Distribution (Mac) | Homebrew tap + unsigned DMG | Free, familiar to researchers |
| Distribution (Windows) | PowerShell install script + .exe zip | Simple download and run |

---

## Architecture

```
scriber/
├── scriber/
│   ├── __main__.py          ← entry point, routes to CLI or GUI
│   ├── cli.py               ← CLI argument parsing + runner
│   ├── app.py               ← GUI launcher
│   ├── core/
│   │   ├── audio.py         ← PyAV audio loading + resampling to 16kHz mono
│   │   ├── transcribe.py    ← MLX / faster-whisper, auto-selects backend
│   │   ├── diarize.py       ← pyannote v4 speaker diarization
│   │   ├── merge.py         ← align transcript segments with speaker labels
│   │   └── export.py        ← txt / srt / vtt / json export
│   └── gui/
│       ├── main_window.py   ← PyQt6 main window
│       ├── worker.py        ← QThread background worker
│       └── widgets.py       ← custom UI components
├── tests/
├── Formula/
│   └── scriber.rb           ← Homebrew formula
├── .github/
│   └── workflows/
│       └── release.yml      ← GitHub Actions: build Mac + Windows on tag
├── pyproject.toml
└── PLAN.md                  ← this file
```

---

## Backend Selection Logic

```python
if mac AND apple_silicon AND macOS >= 14.0:
    backend = MLX-Whisper
else:
    backend = faster-whisper (CPU or CUDA)
```

**Device → backend mapping:**

| Platform | Hardware | Backend | Speed |
|---|---|---|---|
| Mac (M1–M5) | Apple Silicon, macOS 14+ | MLX-Whisper | Very fast |
| Mac (M1–M5) | Apple Silicon, macOS 13 | faster-whisper | Good |
| Mac | Intel | faster-whisper | Moderate |
| Windows/Linux | NVIDIA GPU | faster-whisper (CUDA) | Fast |
| Windows/Linux | CPU only | faster-whisper (CPU) | Slow but works |

---

## Model

**Default: `large-v3-turbo`** — best balance of speed and accuracy.

| Model | Size | Speed | Accuracy |
|---|---|---|---|
| tiny | 39M | ~10x | Basic |
| base | 74M | ~7x | Decent |
| small | 244M | ~4x | Good |
| medium | 769M | ~2x | Very good |
| large-v2 | 1550M | 1x | Excellent |
| large-v3 | 1550M | 1x | Excellent |
| **large-v3-turbo** | **809M** | **~8x** | **Excellent (recommended)** |

### Pause Markers

Optional feature (checkbox in GUI, `--pause-markers` / `--pause-threshold` in CLI). When enabled, inserts `[pause Xs]` between segments where the silence gap meets or exceeds the threshold (default: 2s).

| Format | Pause markers |
|---|---|
| txt | Inline text |
| md | Inline text |
| html | Italic grey line, no timestamp |
| srt | Not included (would break subtitle timing) |
| vtt | Not included (would break subtitle timing) |
| json | Not included (raw segment data only) |

---

Models download automatically on first use and cache locally:
- Mac: `~/Library/Caches/scriber/models/`
- Windows: `C:\Users\<user>\AppData\Local\scriber\Cache\models\`
- Linux: `~/.cache/scriber/models/`

---

## Speaker Annotation

Uses **pyannote v4** — `pyannote/speaker-diarization-community-1`

- Requires a free HuggingFace account
- User must accept the model license at huggingface.co once
- HF token entered once in GUI settings panel (or `--hf-token` in CLI)
- Model cached locally after first download (~1GB)
- Optional — basic transcription works without it

---

## CLI Interface

```bash
# Launch GUI
scriber app
scriber              # no args also launches GUI

# Transcribe
scriber transcribe interview.m4a
scriber transcribe interview.m4a --model large-v3-turbo --export srt
scriber transcribe *.m4a --output ~/Desktop/transcripts --export all

# With speaker annotation
scriber transcribe interview.m4a --annotate --hf-token hf_xxxxx

# Options
--model       tiny|base|small|medium|large-v2|large-v3|large-v3-turbo
--language    en|zh|fr|de|... (default: auto-detect)
--export      txt|srt|vtt|json|all (default: txt)
--output      output directory
--device      auto|cpu|gpu|mlx (default: auto)
--annotate    enable speaker annotation
--hf-token    HuggingFace token
--translate   translate audio to English (all models + backends)
```

---

## Platform Requirements

| Platform | Minimum version | Notes |
|---|---|---|
| macOS (Apple Silicon) | 14.0 Sonoma | MLX requires 14+ |
| macOS (Intel) | 13.0 Ventura | faster-whisper only |
| Windows | 10 22H2 | Still common in universities |
| Linux | Ubuntu 22.04 | faster-whisper |

---

## Build Phases

### Phase 1 — Core
- [x] Set up project with uv + pyproject.toml
- [x] `audio.py` — PyAV loading, resample to 16kHz mono float32
- [x] `transcribe.py` — faster-whisper first (Mac + Windows), platform auto-detect
- [x] `export.py` — txt, srt, vtt, json, md, html
- [x] `export.py` — pause markers support (txt/md/html only)
- [x] `download.py` — model download with progress bar callback
- [x] `cli.py` — basic CLI working end to end
- [x] `transcribe.py` — translation to English (`--translate` / `task="translate"`, all models + backends)
- [x] Test on Mac with real interview files (Serbian + English, large-v3-turbo)
- [ ] Test on Windows

### Phase 2 — MLX
- [x] Add MLX-Whisper path in `transcribe.py`
- [x] Auto-detect Apple Silicon + macOS version
- [x] Benchmark vs faster-whisper on same file (MLX 1.5x faster on 30s, larger gap on longer audio)
- [x] Fallback to faster-whisper if MLX unavailable

### Phase 3 — Speaker Annotation
- [x] `diarize.py` — pyannote v4 pipeline (speaker-diarization-community-1)
- [x] `merge.py` — overlap-based speaker assignment
- [x] Add `--annotate` + `--hf-token` to CLI
- [x] Full pipeline tested (transcribe + diarize + merge + export all formats)
- [x] pyannote accepts pre-loaded audio tensor (no re-decoding)
- [x] MPS / CUDA acceleration for pyannote; CPU fallback
- [x] Pipeline cached in memory across batch files
- [ ] Test with multi-speaker interview files

### Phase 4 — GUI
- [x] Port existing Transcriber PyQt6 GUI to new core
- [x] Replace whisply subprocess calls with direct core module calls
- [x] Progress signals from core → GUI worker thread
- [x] Settings panel: HF token inline under Speaker annotation (no tabs)
- [x] Export formats updated: txt, srt, vtt, json, md, html, all
- [x] Model download progress bar (custom tqdm → log_replace signal)
- [x] Per-file elapsed timer (resets at start of each file, resets again at annotation)
- [x] Pulse suspended during audio load and download to avoid overlap
- [x] "Loading audio..." status message before load
- [x] Pause markers option: checkbox (2s default), inserted in txt/md/html
- [x] Soft stop: sets flag, finishes current file, prints ◼ Stopped
- [x] app.setStyle("Fusion") for correct dark theme rendering
- [x] Unified model cache: HF_HUB_CACHE set to ~/Library/Caches/scriber/models/ in __main__.py
- [x] Pyannote runs on MPS (Apple Silicon) or CUDA (NVIDIA), falls back to CPU
- [x] Pyannote receives pre-loaded audio tensor (avoids re-decoding source file)
- [x] Pyannote pipeline cached in memory across batch files
- [x] Translate to English checkbox (all models + backends, MLX + faster-whisper)
- [x] Download progress preserves "Downloading, first time only..." line in GUI log

### Phase 5 — Packaging
- [ ] PyInstaller spec file for Mac → `.app` → unsigned DMG
- [ ] PyInstaller spec file for Windows → `.exe` → zip
- [ ] GitHub Actions workflow: build both on git tag push
- [ ] Homebrew formula (`Formula/scriber.rb`)
- [ ] PowerShell install script for Windows
- [ ] Test on clean machines (no Python, no dev tools)

### Phase 6 — Polish
- [x] Auto model download with progress in GUI
- [ ] User-friendly error messages (no stack traces for end users)
- [ ] Hallucination suppression (VAD filter already in faster-whisper)
- [ ] Large file handling (chunking for memory)
- [ ] README for end users (non-technical)

### Backlog — Future Features
- [x] **Text translation via NLLB-200** — `facebook/nllb-200-distilled-600M` via transformers pipeline. Translates transcript text segments to English after transcription. Works with any Whisper model including turbo (Whisper turbo's audio translation is broken). ~600MB one-time download.
- [ ] **Dual-language output** — "Export language" dropdown: `Original` / `English` / `Both`. When `Both`, transcribe once (original language) then run NLLB-200 on segments for English. Diarization runs once, speaker labels merge into both outputs.

---

## Key Problems to Solve

| Problem | Approach |
|---|---|
| Large model download (~3GB) | Progress bar, download in background, cache |
| Out of memory on low-RAM machines | Offer smaller models, clear error message |
| Unsupported audio formats | PyAV handles most; catch av.AVError and show message |
| Hallucinations on silence | VAD filter (built into faster-whisper) |
| Non-Latin script rendering | UTF-8 everywhere, already handled |
| Speaker count wrong | Let pyannote auto-detect; offer manual override |
| SRT timing off | Segment-level timestamps are accurate; no word alignment needed |
| Windows Gatekeeper equivalent (SmartScreen) | Sign with free cert or instruct users to allow |

---

## What We Are NOT Building

- Web interface (wrong audience)
- REST API (wrong audience)
- WhisperX dependency (k2 broken on Windows)
- ffmpeg as separate install (PyAV replaces it)
- whisply dependency (full control now)

---

## References

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — primary Windows/Linux backend
- [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — primary Mac backend
- [pyannote-audio v4](https://github.com/pyannote/pyannote-audio) — speaker diarization
- [PyAV](https://github.com/PyAV-Org/PyAV) — audio loading
- [noScribe](https://github.com/kaixxx/noScribe) — reference implementation (faster-whisper + pyannote, GUI only, no MLX)
- [PyInstaller](https://pyinstaller.org) — packaging
