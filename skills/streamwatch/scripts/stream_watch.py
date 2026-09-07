#!/usr/bin/env python3
"""/streamwatch entry point.

Resolves a video (URL or local path), gets a transcript (captions first,
Whisper fallback), extracts representative frames, and prints a markdown
report with frame paths for Claude to Read.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from config import frame_cap, get_depth  # noqa: E402
from download import is_url, resolve as resolve_source  # noqa: E402
from frames import (  # noqa: E402
    MAX_FPS, format_time, get_metadata, parse_time,
    select_frames, target_frame_budget, target_frame_budget_focused,
)
from captions import filter_range, parse_vtt, render as render_transcript  # noqa: E402
from whisper import load_api_key, transcribe_video  # noqa: E402

_ENGINE_FOR_DEPTH = {"quick": "keyframe", "standard": "scene", "deep": "scene"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="streamwatch", description="Watch a video: frames + transcript.")
    ap.add_argument("source", help="Video URL or local file path")
    ap.add_argument("--depth", choices=["captions-only", "quick", "standard", "deep"], default=None)
    ap.add_argument("--start", default=None, help="Focus range start (SS, MM:SS, HH:MM:SS)")
    ap.add_argument("--end", default=None, help="Focus range end")
    ap.add_argument("--max-frames", type=int, default=None, help="Override the depth tier's frame cap")
    ap.add_argument("--resolution", type=int, default=512, help="Frame width in px (default 512)")
    ap.add_argument("--fps", type=float, default=None, help="Override auto-fps (clamped to 2 max)")
    ap.add_argument("--out-dir", default=None, help="Working directory (default: a temp dir)")
    ap.add_argument("--no-whisper", action="store_true", help="Never fall back to Whisper")
    ap.add_argument("--whisper", choices=["groq", "openai"], default=None, help="Force a Whisper backend")
    ap.add_argument("--no-dedup", action="store_true", help="Keep near-duplicate frames")
    return ap


def main() -> int:
    args = build_parser().parse_args()

    depth = args.depth or get_depth()
    cap = args.max_frames if args.max_frames is not None else frame_cap(depth)
    if cap is not None and cap < 1:
        raise SystemExit("--max-frames must be positive")

    work = Path(args.out_dir).expanduser().resolve() if args.out_dir else Path(tempfile.mkdtemp(prefix="streamwatch-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"[streamwatch] working dir: {work}", file=sys.stderr)

    url_source = is_url(args.source)
    transcript_segments: list[dict] = []
    transcript_source: str | None = None
    video_path: str | None = None
    dl: dict = {"subtitle_path": None, "info": {}, "downloaded": False}

    # Captions-only pass first for URLs (cheap, no video download needed).
    if url_source:
        from download import fetch_captions_only
        print("[streamwatch] checking for captions…", file=sys.stderr)
        dl = fetch_captions_only(args.source, work / "download")
        if dl.get("subtitle_path"):
            transcript_segments = parse_vtt(dl["subtitle_path"])
            transcript_source = "captions"

    need_video = not (depth == "captions-only" and transcript_segments)
    if need_video:
        audio_only = depth == "captions-only"
        print("[streamwatch] downloading…" if url_source else "[streamwatch] reading local file…", file=sys.stderr)
        dl = resolve_source(args.source, work / "download", audio_only=audio_only)
        video_path = dl["video_path"]
        if not transcript_segments and dl.get("subtitle_path"):
            transcript_segments = parse_vtt(dl["subtitle_path"])
            transcript_source = "captions"

    meta = get_metadata(video_path) if video_path else {
        "duration_seconds": float((dl.get("info") or {}).get("duration") or 0),
        "width": None, "height": None, "codec": None, "has_audio": False,
    }
    full_duration = meta["duration_seconds"]

    start_sec, end_sec = parse_time(args.start), parse_time(args.end)
    if start_sec is not None and start_sec < 0:
        raise SystemExit("--start must be non-negative")
    if end_sec is not None and start_sec is not None and end_sec <= start_sec:
        raise SystemExit("--end must be greater than --start")

    focused = start_sec is not None or end_sec is not None
    eff_start = start_sec or 0.0
    eff_end = end_sec if end_sec is not None else full_duration
    eff_duration = max(0.0, eff_end - eff_start)

    if focused and transcript_segments:
        transcript_segments = filter_range(transcript_segments, start_sec, end_sec)

    frames: list[dict] = []
    frame_info: dict = {"engine": "none", "candidates": 0, "selected": 0, "fallback": False}
    if depth != "captions-only" and video_path:
        budget_fn = target_frame_budget_focused if focused else target_frame_budget
        target = budget_fn(eff_duration, cap if cap is not None else 100)
        engine = _ENGINE_FOR_DEPTH[depth]
        print(f"[streamwatch] extracting frames ({engine})…", file=sys.stderr)
        frames, frame_info = select_frames(
            video_path, work / "frames", engine, cap, target,
            width=args.resolution, start=start_sec, end=end_sec,
            dedup_enabled=not args.no_dedup,
        )

    if not transcript_segments and not args.no_whisper and video_path and meta.get("has_audio"):
        backend, api_key = load_api_key(args.whisper)
        if backend and api_key:
            try:
                segments, used = transcribe_video(video_path, work / "audio.mp3", backend=backend, api_key=api_key)
                transcript_segments = filter_range(segments, start_sec, end_sec) if focused else segments
                transcript_source = f"whisper ({used})"
            except SystemExit as exc:
                print(f"[streamwatch] whisper fallback failed: {exc}", file=sys.stderr)
        else:
            print(f"[streamwatch] no captions and no Whisper key — run {SCRIPT_DIR / 'setup.py'}", file=sys.stderr)

    _print_report(args, depth, full_duration, focused, eff_start, eff_end, eff_duration, meta, dl, cap, frames, frame_info, transcript_segments, transcript_source, work)
    return 0


def _print_report(args, depth, full_duration, focused, eff_start, eff_end, eff_duration, meta, dl, cap, frames, frame_info, transcript_segments, transcript_source, work) -> None:
    info = dl.get("info") or {}
    print()
    print("# streamwatch: video report")
    print()
    print(f"- **Source:** {args.source}")
    if info.get("title"):
        print(f"- **Title:** {info['title']}")
    if info.get("uploader"):
        print(f"- **Uploader:** {info['uploader']}")
    print(f"- **Duration:** {format_time(full_duration)} ({full_duration:.1f}s)")
    if focused:
        print(f"- **Focus range:** {format_time(eff_start)} → {format_time(eff_end)} ({eff_duration:.1f}s)")
    if meta.get("width") and meta.get("height"):
        print(f"- **Resolution:** {meta['width']}x{meta['height']} ({meta.get('codec') or 'unknown'})")
    print(f"- **Depth:** {depth}")

    if depth != "captions-only":
        cap_label = "unlimited" if cap is None else str(cap)
        fb = " (uniform fallback)" if frame_info.get("fallback") else ""
        dd = frame_info.get("deduped", 0)
        dd_note = f", {dd} near-duplicate{'s' if dd != 1 else ''} dropped" if dd else ""
        print(f"- **Frames:** {frame_info.get('selected', 0)} of {frame_info.get('candidates', 0)} candidates ({frame_info.get('engine')}{fb}{dd_note}, cap {cap_label})")
    else:
        print("- **Frames:** skipped (captions-only depth)")

    if transcript_segments:
        print(f"- **Transcript:** {len(transcript_segments)} segments (via {transcript_source or 'captions'})")
    else:
        print("- **Transcript:** none available")

    if depth == "deep" and len(frames) > 250:
        print()
        print(f"> **Warning:** {len(frames)} frames selected — this uses a large number of image tokens.")

    if not focused and full_duration > 600 and depth not in ("captions-only", "deep"):
        print()
        print(
            f"> **Warning:** {int(full_duration // 60)}-minute video — frame coverage is sparse at this "
            "length under this depth tier. Re-run with --start/--end to focus on a section, or "
            "--depth deep for full scene coverage."
        )

    print()
    print("## Frames")
    print()
    if frames:
        print(f"Frames live at: `{work / 'frames'}`")
        print()
        print("**Read each frame path with the Read tool.** Frames are chronological; `t=MM:SS` is absolute source time.")
        print()
        for f in frames:
            print(f"- `{f['path']}` (t={format_time(f['timestamp_seconds'])}, reason={f.get('reason', 'selected')})")
    else:
        print("_No frames extracted._")

    print()
    print("## Transcript")
    print()
    if transcript_segments:
        label = transcript_source or "captions"
        scope = f" Filtered to {format_time(eff_start)} → {format_time(eff_end)}." if focused else ""
        print(f"_Source: {label}.{scope}_")
        print()
        print("```")
        print(render_transcript(transcript_segments))
        print("```")
    else:
        print(f"_No transcript available. Run `python3 {SCRIPT_DIR / 'setup.py'}` to enable the Whisper fallback, then re-run._")

    print()
    print("---")
    print(f"_Work dir: `{work}` — delete when you're done with this video._")


if __name__ == "__main__":
    raise SystemExit(main())
