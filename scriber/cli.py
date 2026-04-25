import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        prog="scriber",
        description="Offline transcription for qualitative researchers",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # GUI subcommand
    subparsers.add_parser("app", help="Launch the GUI")

    # Transcribe subcommand
    transcribe = subparsers.add_parser("transcribe", help="Transcribe audio files")
    transcribe.add_argument("files", nargs="+", help="Audio files to transcribe")
    transcribe.add_argument(
        "--model", default="large-v3-turbo",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"],
        help="Whisper model to use (default: large-v3-turbo)",
    )
    transcribe.add_argument(
        "--language", default=None,
        help="Language code e.g. en, zh, fr (default: auto-detect)",
    )
    transcribe.add_argument(
        "--export", default="txt",
        choices=["txt", "srt", "vtt", "json", "md", "html", "all"],
        help="Export format (default: txt)",
    )
    transcribe.add_argument(
        "--output", default=None,
        help="Output directory (default: same as input file)",
    )
    transcribe.add_argument(
        "--annotate", action="store_true",
        help="Enable speaker annotation (requires --hf-token)",
    )
    transcribe.add_argument(
        "--hf-token", default=None,
        help="HuggingFace token for speaker annotation",
    )
    transcribe.add_argument(
        "--device", default="auto",
        choices=["auto", "cpu", "gpu", "mlx"],
        help="Device to use (default: auto)",
    )
    transcribe.add_argument(
        "--translate", action="store_true",
        help="Translate audio to English (instead of transcribing in source language)",
    )

    return parser.parse_args()


def run_cli(args):
    from pathlib import Path
    from scriber.core.audio import load_audio
    from scriber.core.transcribe import transcribe
    from scriber.core.export import export
    from scriber.core.diarize import diarize
    from scriber.core.merge import merge

    for file_path in args.files:
        file = Path(file_path)
        print(f"Processing: {file.name}")

        audio = load_audio(file)
        task = "translate" if args.translate else "transcribe"
        segments = transcribe(audio, model=args.model, language=args.language, device=args.device, task=task)

        if args.annotate and args.hf_token:
            speakers = diarize(file, hf_token=args.hf_token)
            segments = merge(segments, speakers)

        output_dir = Path(args.output) if args.output else file.parent
        export(segments, output_dir / file.stem, formats=args.export)
        print(f"Done: {file.name}")
