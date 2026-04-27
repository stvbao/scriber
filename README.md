# Scriber

Transcription tool built for social scientists and qualitative researchers.

Drop in an audio file, get a transcript. Scriber runs entirely on your own machine — no cloud service, no subscription, and once the model downloads it works offline. Your recordings stay on your desk.

## Contents

- [Features](#features)
- [Installation](#installation)
- [How to Use](#how-to-use)
- [Speaker Annotation](#speaker-annotation)
- [Data Privacy](#data-privacy)
- [Device Selection](#device-selection)
- [Platform Support](#platform-support)
- [CLI Reference](#cli-reference)
- [License](#license)
- [Credits](#credits)

## Features

- **Desktop GUI and CLI** — use a point-and-click app or work in Terminal
- **Offline transcription** — audio stays on your machine
- **Batch processing** — transcribe one file or many in a single pass
- **Speaker annotation** — optional diarization with pyannote
- **Multiple export formats** — `txt`, `srt`, `vtt`, `json`, `md`, `html`
- **Pause markers** — optional pause labels in GUI exports
- **Apple Silicon optimized** — uses MLX automatically where available
- **Translation** — optionally translate speech to English
- **Local model cache** — models download once, then are reused

## Installation

### macOS

**Homebrew (recommended)** — Apple Silicon only:

```bash
brew tap stvbao/scriber https://github.com/stvbao/scriber
brew install scriber
```

Intel Mac need to install from source, brew install is still in development.

**From source** — any Mac (requires [uv](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/stvbao/scriber.git
cd scriber
uv sync
```

### Windows

Packaged Windows releases are still in development. To install on Windows today, first install Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```powershell
git clone https://github.com/stvbao/scriber.git
cd scriber
uv sync
```

## How to Use

Run `scriber` or `scriber app` to open the GUI. If you installed from source, prefix with `uv run`.

For CLI usage, see [CLI Reference](#cli-reference) below.

## Speaker Annotation

Speaker annotation labels who is speaking — for example `SPEAKER_00`, `SPEAKER_01`, and so on.

To use it:

1. Create a Hugging Face token at [hf.co/settings/tokens](https://hf.co/settings/tokens)
2. Accept the model license for [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
3. Paste the token into the GUI field, or pass `--hf-token` in the CLI

The annotation model is downloaded once and cached locally.

If you know how many speakers are in the recording, enter that number in the GUI — it helps pyannote assign speakers more accurately. Leave it at 0 to auto-detect.

Speaker diarization works best when speakers take clear turns. Accuracy drops when multiple people speak at the same time — a common occurrence in focus groups. Results also vary with audio quality and the number of speakers.

## Data Privacy

- Audio files are processed locally
- No transcription data is sent to a cloud service
- No API key is required for basic transcription
- Hugging Face is contacted only to download models
- Scriber does not send telemetry

## Device Selection

Scriber uses two transcription backends: [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) on Apple Silicon and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) everywhere else. The `auto` setting picks the right one for your machine.

| Your system | Setting | Backend | Supported models |
|---|---|---|---|
| Apple Silicon Mac, macOS 14+ | `auto` | mlx-whisper | All models |
| Apple Silicon Mac, macOS 13 | `auto` | faster-whisper | All models |
| Intel Mac | `auto` | faster-whisper | All models |
| Apple Silicon Mac, force MLX | `mlx` | mlx-whisper | All models |
| Windows/Linux with NVIDIA GPU | `gpu` | faster-whisper + CUDA | All models |
| CPU-only system | `cpu` | faster-whisper | All models |

Available models, from most to least capable: `large-v3-turbo` (default), `large-v3`, `large-v2`, `medium`, `small`, `base`, `tiny`.

Models download on first use and are reused from the local cache. When translation is enabled, Scriber automatically uses `large-v3` instead of `large-v3-turbo`, because the current turbo variant does not support translation.

## Platform Support

| Platform | Backend | Packaged release |
|---|---|---|
| Apple Silicon macOS 14+ | MLX (default) | Homebrew |
| Apple Silicon macOS 13 | faster-whisper fallback | Homebrew |
| Intel macOS | faster-whisper | Source only |
| Windows with NVIDIA GPU | faster-whisper with CUDA | Source only |
| Windows or Linux, CPU only | faster-whisper | Source only |

A standalone macOS DMG and a packaged Windows release are not currently being shipped and are still in development.

## CLI Reference

```
$ scriber --help

Offline transcription for qualitative researchers

commands:
  app          Launch the GUI
  transcribe   Transcribe audio files
  cache        Manage the local model cache
```

```
$ scriber transcribe --help

usage: scriber transcribe [options] files...

positional arguments:
  files                   Audio files to transcribe

options:
  --model    {large-v3-turbo,large-v3,large-v2,medium,small,base,tiny}
                          Whisper model to use (default: large-v3-turbo)
  --language LANGUAGE     Language code e.g. en, zh, fr (default: auto-detect)
  --export   {txt,srt,vtt,json,md,html,all}
                          Export format (default: all)
  --output   OUTPUT       Output directory (default: same as input)
  --device   {auto,cpu,gpu,mlx}
                          Device to use (default: auto)
  --annotate              Enable speaker annotation (requires --hf-token)
  --hf-token HF_TOKEN     HuggingFace token for speaker annotation
  --translate             Translate audio to English
```

**Examples:**

```bash
scriber transcribe interview.m4a
scriber transcribe interview.m4a --model large-v3 --export srt
scriber transcribe *.m4a --output ~/Desktop/transcripts
scriber transcribe interview.m4a --annotate --hf-token hf_xxxxx
```

```bash
# Model cache
scriber cache path
scriber cache clear
```

## License

Scriber is licensed under [GPL-3.0](./LICENSE).

By contributing code, documentation, or assets, you agree that your contribution may be distributed under `GPL-3.0-only` and may be relicensed as part of future versions of Scriber.

## Credits

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — transcription backend for Intel Mac, Windows, and Linux
- [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — transcription backend for Apple Silicon
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — speaker diarization
- [noScribe](https://github.com/kaixxx/noScribe) — GUI inspiration
- [whisply](https://github.com/tsmdt/whisply) — architecture inspiration
- Developed with assistance from Claude and OpenAI Codex
