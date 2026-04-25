"""Export transcript segments to txt, srt, vtt, json, md, html."""

from __future__ import annotations
from pathlib import Path
import json


def export(segments, output_stem: Path, formats: str = "txt"):
    fmts = ["txt", "srt", "vtt", "json", "md", "html"] if formats == "all" else [formats]
    for fmt in fmts:
        if fmt == "txt":   _export_txt(segments, output_stem.with_suffix(".txt"))
        if fmt == "srt":   _export_srt(segments, output_stem.with_suffix(".srt"))
        if fmt == "vtt":   _export_vtt(segments, output_stem.with_suffix(".vtt"))
        if fmt == "json":  _export_json(segments, output_stem.with_suffix(".json"))
        if fmt == "md":    _export_md(segments, output_stem.with_suffix(".md"))
        if fmt == "html":  _export_html(segments, output_stem.with_suffix(".html"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ts_srt(seconds: float) -> str:
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _ts_vtt(seconds: float) -> str:
    return _ts_srt(seconds).replace(",", ".")


def _speaker_prefix(seg) -> str:
    return f"[{seg.speaker}] " if seg.speaker else ""


# ── Exporters ─────────────────────────────────────────────────────────────────

def _export_txt(segments, path: Path):
    lines = []
    current_speaker = None
    for seg in segments:
        if seg.speaker and seg.speaker != current_speaker:
            lines.append(f"\n{seg.speaker}:")
            current_speaker = seg.speaker
        lines.append(seg.text)
    path.write_text("\n".join(lines).strip(), encoding="utf-8")


def _export_srt(segments, path: Path):
    blocks = []
    for i, seg in enumerate(segments, 1):
        blocks.append(
            f"{i}\n"
            f"{_ts_srt(seg.start)} --> {_ts_srt(seg.end)}\n"
            f"{_speaker_prefix(seg)}{seg.text}"
        )
    path.write_text("\n\n".join(blocks), encoding="utf-8")


def _export_vtt(segments, path: Path):
    blocks = ["WEBVTT\n"]
    for seg in segments:
        blocks.append(
            f"{_ts_vtt(seg.start)} --> {_ts_vtt(seg.end)}\n"
            f"{_speaker_prefix(seg)}{seg.text}"
        )
    path.write_text("\n\n".join(blocks), encoding="utf-8")


def _export_json(segments, path: Path):
    data = [
        {
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "speaker": seg.speaker,
        }
        for seg in segments
    ]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _export_md(segments, path: Path):
    lines = []
    current_speaker = None
    for seg in segments:
        if seg.speaker and seg.speaker != current_speaker:
            lines.append(f"\n## {seg.speaker}\n")
            current_speaker = seg.speaker
        lines.append(seg.text)
    path.write_text("\n".join(lines).strip(), encoding="utf-8")


def _export_html(segments, path: Path):
    blocks = []
    current_speaker = None
    for seg in segments:
        if seg.speaker and seg.speaker != current_speaker:
            if blocks:
                blocks.append("</div>")
            blocks.append(f'<div class="speaker">')
            blocks.append(f'<h2>{seg.speaker}</h2>')
            current_speaker = seg.speaker
        ts = _ts_srt(seg.start)
        blocks.append(f'<p><span class="ts">[{ts}]</span> {seg.text}</p>')
    if blocks:
        blocks.append("</div>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transcript</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #222; }}
  h2 {{ color: #444; margin-top: 2em; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  .ts {{ color: #999; font-size: 0.85em; font-family: monospace; }}
  p {{ margin: 0.4em 0; }}
</style>
</head>
<body>
{"".join(blocks)}
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
