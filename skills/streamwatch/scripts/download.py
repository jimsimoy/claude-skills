#!/usr/bin/env python3
"""Resolve a /streamwatch source: download a URL via yt-dlp, or point at a local file.

Also pulls captions (manual, then auto-generated) in VTT form so the
transcript can come from captions before falling back to Whisper.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi", ".flv", ".wmv"}


def is_url(source: str) -> bool:
    if source.startswith("-"):
        return False
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def resolve_local(path: str) -> dict:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise SystemExit(f"File not found: {resolved}")
    return {
        "video_path": str(resolved),
        "subtitle_path": None,
        "info": {"title": resolved.name, "url": str(resolved)},
        "downloaded": False,
    }


def _require_yt_dlp() -> None:
    if shutil.which("yt-dlp") is None:
        raise SystemExit("yt-dlp is not installed. Install: https://github.com/yt-dlp/yt-dlp#installation")


def _find_subtitle(out_dir: Path) -> Path | None:
    candidates = sorted(out_dir.glob("media*.vtt"))
    if not candidates:
        return None
    english = [c for c in candidates if ".en" in c.name]
    return english[0] if english else candidates[0]


def _find_video(out_dir: Path) -> Path | None:
    for ext in (".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".opus"):
        match = next(out_dir.glob(f"media*{ext}"), None)
        if match:
            return match
    return None


def _read_metadata(info_path: Path, url: str) -> dict:
    if not info_path.exists():
        return {"url": url}
    try:
        raw = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"url": url}
    return {
        "title": raw.get("title"),
        "uploader": raw.get("uploader") or raw.get("channel"),
        "duration": raw.get("duration"),
        "url": raw.get("webpage_url") or url,
    }


def fetch_captions_only(url: str, out_dir: Path) -> dict:
    """Get metadata + best-available captions without pulling the video."""
    _require_yt_dlp()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp", "--skip-download",
        "--write-info-json", "--write-subs", "--write-auto-subs",
        "--sub-langs", "en.*", "--sub-format", "vtt", "--convert-subs", "vtt",
        "--no-playlist", "--ignore-errors",
        "-o", str(out_dir / "media.%(ext)s"),
        "--", url,
    ]
    subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    return {
        "video_path": None,
        "subtitle_path": str(sub) if (sub := _find_subtitle(out_dir)) else None,
        "info": _read_metadata(out_dir / "media.info.json", url),
        "downloaded": False,
    }


def download(url: str, out_dir: Path, audio_only: bool = False) -> dict:
    _require_yt_dlp()
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = "ba/bestaudio" if audio_only else "bv*[height<=720]+ba/b[height<=720]/bv+ba/b"
    cmd = [
        "yt-dlp", "-N", "8", "-f", fmt,
        "--merge-output-format", "mp4",
        "--write-info-json", "--write-subs", "--write-auto-subs",
        "--sub-langs", "en.*", "--sub-format", "vtt", "--convert-subs", "vtt",
        "--no-playlist", "--ignore-errors",
        "-o", str(out_dir / "media.%(ext)s"),
        "--", url,
    ]
    result = subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr)
    video = _find_video(out_dir)
    if video is None:
        raise SystemExit(f"yt-dlp produced no media file in {out_dir} (exit {result.returncode})")
    return {
        "video_path": str(video),
        "subtitle_path": str(sub) if (sub := _find_subtitle(out_dir)) else None,
        "info": _read_metadata(out_dir / "media.info.json", url),
        "downloaded": True,
    }


def resolve(source: str, out_dir: Path, audio_only: bool = False) -> dict:
    return download(source, out_dir, audio_only=audio_only) if is_url(source) else resolve_local(source)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: download.py <url-or-path> <out-dir>", file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(resolve(sys.argv[1], Path(sys.argv[2])), indent=2))
