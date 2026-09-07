#!/usr/bin/env python3
"""Extract representative frames from a video via ffmpeg.

Three engines:
  - uniform: fixed fps sampling, used as the fallback when a video is too
    static for scene/keyframe detection to find enough distinct shots.
  - scene: ffmpeg's scene-change filter — full coverage, then thinned to a
    frame cap by even sampling.
  - keyframe: decode only I-frames (`-skip_frame nokey`) — near-instant,
    coarser than scene detection.

All three can be followed by near-duplicate dropping (frame-delta dedup) so
a held slide or static screen recording doesn't burn the frame budget.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MAX_FPS = 2.0
SCENE_THRESHOLD = 0.20
SCENE_MIN_SHOTS = 8       # below this, treat the video as static and fall back to uniform
KEYFRAME_MIN = 4
MAX_FRAME_HEIGHT = 1998   # stay under common image-read size limits
DEDUP_THUMB_SIDE = 16
DEDUP_THRESHOLD = 2.0
_SHOWINFO_TS = re.compile(r"pts_time:([0-9.]+)")


def _scale_filter(width: int) -> str:
    return f"scale=w='min({width},iw)':h='min({MAX_FRAME_HEIGHT},ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"


def parse_time(value: str | float | int | None) -> float | None:
    """SS, MM:SS, or HH:MM:SS -> seconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    parts = str(value).strip().split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    raise SystemExit(f"cannot parse time: {value!r} (expected SS, MM:SS, or HH:MM:SS)")


def format_time(seconds: float) -> str:
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def get_metadata(video_path: str) -> dict:
    if shutil.which("ffprobe") is None:
        raise SystemExit("ffprobe not installed")
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(Path(video_path).resolve())],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()}")
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])
    fmt = data.get("format", {})
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    return {
        "duration_seconds": float(fmt.get("duration") or video_stream.get("duration") or 0),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "codec": video_stream.get("codec_name"),
        "has_audio": has_audio,
    }


def target_frame_budget(duration: float, cap: int) -> int:
    """How many frames a full-video scan should aim for, before capping."""
    if duration <= 30:
        return min(cap, max(12, round(duration)))
    if duration <= 60:
        return min(cap, 40)
    if duration <= 180:
        return min(cap, 60)
    if duration <= 600:
        return min(cap, 80)
    return cap


def target_frame_budget_focused(duration: float, cap: int) -> int:
    """Denser budget for a user-specified range — they're zooming in."""
    if duration <= 5:
        return min(cap, max(10, round(duration * 6)))
    if duration <= 15:
        return min(cap, max(30, round(duration * 4)))
    if duration <= 30:
        return min(cap, 60)
    if duration <= 60:
        return min(cap, 80)
    return cap


def _fps_for_budget(target_frames: int, duration: float) -> float:
    if duration <= 0:
        return 1.0
    return min(MAX_FPS, target_frames / duration)


def extract_uniform(video_path: str, out_dir: Path, fps: float, width: int, cap: int, start: float | None, end: float | None) -> list[dict]:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not installed")
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("frame_*.jpg"):
        f.unlink()

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += [
        "-i", str(Path(video_path).resolve()),
        "-vf", f"fps={fps},{_scale_filter(width)}",
        "-frames:v", str(cap),
        "-q:v", "4",
        str(out_dir / "frame_%04d.jpg"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"uniform frame extraction failed: {result.stderr.strip()}")

    offset = start or 0.0
    frames = sorted(out_dir.glob("frame_*.jpg"))
    return [
        {"index": i, "timestamp_seconds": round(offset + (i / fps if fps > 0 else 0), 2), "path": str(p), "reason": "uniform"}
        for i, p in enumerate(frames)
    ]


def extract_scene_candidates(video_path: str, out_dir: Path, width: int, start: float | None, end: float | None, cap: int | None = None) -> list[dict]:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not installed")
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("frame_*.jpg"):
        f.unlink()

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "info", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    vf = f"select='eq(n\\,0)+gt(scene\\,{SCENE_THRESHOLD})',{_scale_filter(width)},showinfo"
    cmd += ["-i", str(Path(video_path).resolve()), "-vf", vf, "-vsync", "vfr"]
    if cap is not None:
        cmd += ["-frames:v", str(cap)]
    cmd += ["-q:v", "4", str(out_dir / "frame_%04d.jpg")]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"scene extraction failed: {result.stderr.strip()}")

    offset = start or 0.0
    timestamps = [round(offset + float(m.group(1)), 2) for m in _SHOWINFO_TS.finditer(result.stderr)]
    frames = sorted(out_dir.glob("frame_*.jpg"))
    return [
        {"index": i, "timestamp_seconds": timestamps[i] if i < len(timestamps) else offset, "path": str(p), "reason": "first-frame" if i == 0 else "scene-change"}
        for i, p in enumerate(frames)
    ]


def extract_keyframes(video_path: str, out_dir: Path, width: int, start: float | None, end: float | None) -> list[dict]:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not installed")
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("frame_*.jpg"):
        f.unlink()

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "info", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += [
        "-skip_frame", "nokey",
        "-i", str(Path(video_path).resolve()),
        "-vf", f"{_scale_filter(width)},showinfo",
        "-vsync", "vfr", "-q:v", "4",
        str(out_dir / "frame_%04d.jpg"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"keyframe extraction failed: {result.stderr.strip()}")

    offset = start or 0.0
    timestamps = [round(offset + float(m.group(1)), 2) for m in _SHOWINFO_TS.finditer(result.stderr)]
    frames = sorted(out_dir.glob("frame_*.jpg"))
    return [
        {"index": i, "timestamp_seconds": timestamps[i] if i < len(timestamps) else offset, "path": str(p), "reason": "keyframe"}
        for i, p in enumerate(frames)
    ]


def _even_sample_indices(count: int, n: int) -> list[int]:
    if n >= count:
        return list(range(count))
    if n <= 1:
        return [0]
    return [round(i * (count - 1) / (n - 1)) for i in range(n)]


def thin_to_cap(candidates: list[dict], cap: int) -> list[dict]:
    """Even-sample down to `cap` (always keeping first + last), deleting the rest."""
    keep = [candidates[i] for i in _even_sample_indices(len(candidates), cap)]
    keep_paths = {f["path"] for f in keep}
    for cand in candidates:
        if cand["path"] not in keep_paths:
            Path(cand["path"]).unlink(missing_ok=True)
    for i, frame in enumerate(keep):
        frame["index"] = i
    return keep


def _thumbnails(paths: list[Path]) -> list[bytes]:
    """One ffmpeg pass, decoding every frame to a tiny grayscale thumbnail."""
    if not paths:
        return []
    m = re.match(r"(.*?)(\d+)(\.[A-Za-z0-9]+)$", paths[0].name)
    if m is None:
        return []
    prefix, digits, ext = m.groups()
    pattern = str(paths[0].parent / f"{prefix}%0{len(digits)}d{ext}")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-start_number", str(int(digits)), "-i", pattern,
        "-vf", f"scale={DEDUP_THUMB_SIDE}:{DEDUP_THUMB_SIDE},format=gray",
        "-f", "rawvideo", "-",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return []
    chunk = DEDUP_THUMB_SIDE * DEDUP_THUMB_SIDE
    data = result.stdout
    if len(data) != chunk * len(paths):
        return []
    return [data[i * chunk:(i + 1) * chunk] for i in range(len(paths))]


def _mean_delta(a: bytes, b: bytes) -> float:
    if not a or len(a) != len(b):
        return float("inf")
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def dedupe(candidates: list[dict], threshold: float = DEDUP_THRESHOLD) -> tuple[list[dict], int]:
    """Drop frames that are visually near-identical to the previous kept one."""
    if len(candidates) <= 1:
        return candidates, 0
    thumbs = _thumbnails([Path(c["path"]) for c in candidates])
    if len(thumbs) != len(candidates):
        return candidates, 0

    kept = [candidates[0]]
    last_thumb = thumbs[0]
    dropped = []
    for cand, thumb in zip(candidates[1:], thumbs[1:]):
        if _mean_delta(thumb, last_thumb) <= threshold:
            dropped.append(cand)
        else:
            kept.append(cand)
            last_thumb = thumb

    for cand in dropped:
        Path(cand["path"]).unlink(missing_ok=True)
    for i, frame in enumerate(kept):
        frame["index"] = i
    return kept, len(dropped)


def select_frames(
    video_path: str,
    out_dir: Path,
    engine: str,
    cap: int | None,
    target: int,
    width: int = 512,
    start: float | None = None,
    end: float | None = None,
    dedup_enabled: bool = True,
) -> tuple[list[dict], dict]:
    """Top-level entry: pick an engine, run it, dedup, thin to cap."""
    if engine == "keyframe":
        candidates = extract_keyframes(video_path, out_dir, width, start, end)
        if len(candidates) < KEYFRAME_MIN:
            return _uniform_fallback(video_path, out_dir, width, cap, target, start, end, dedup_enabled, len(candidates))
        deduped, n_dropped = dedupe(candidates) if dedup_enabled else (candidates, 0)
        selected = thin_to_cap(deduped, cap if cap is not None else len(deduped))
        return selected, {"engine": "keyframe", "candidates": len(candidates), "deduped": n_dropped, "selected": len(selected), "fallback": False}

    # scene (used for both "balanced" and "token-burner")
    candidates = extract_scene_candidates(video_path, out_dir, width, start, end, cap=None)
    if len(candidates) < SCENE_MIN_SHOTS:
        return _uniform_fallback(video_path, out_dir, width, cap, target, start, end, dedup_enabled, len(candidates))
    deduped, n_dropped = dedupe(candidates) if dedup_enabled else (candidates, 0)
    selected = thin_to_cap(deduped, cap if cap is not None else len(deduped))
    return selected, {"engine": "scene", "candidates": len(candidates), "deduped": n_dropped, "selected": len(selected), "fallback": False}


def _uniform_fallback(video_path, out_dir, width, cap, target, start, end, dedup_enabled, candidate_count) -> tuple[list[dict], dict]:
    fallback_cap = target if cap is None else min(cap, target)
    duration = (end or 0) - (start or 0) if (start is not None or end is not None) else get_metadata(video_path)["duration_seconds"]
    fps = _fps_for_budget(fallback_cap, duration)
    frames = extract_uniform(video_path, out_dir, fps, width, fallback_cap, start, end)
    n_dropped = 0
    if dedup_enabled:
        frames, n_dropped = dedupe(frames)
    return frames, {"engine": "uniform", "candidates": candidate_count, "deduped": n_dropped, "selected": len(frames), "fallback": True}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: frames.py <video> <out-dir> [--engine scene|keyframe|uniform] [--cap N] [--width W] [--start T] [--end T]", file=sys.stderr)
        raise SystemExit(2)
    video, out = sys.argv[1], Path(sys.argv[2])
    args = sys.argv[3:]
    engine, cap, width = "scene", 100, 512
    start_arg = end_arg = None
    i = 0
    while i < len(args):
        if args[i] == "--engine":
            engine = args[i + 1]; i += 2
        elif args[i] == "--cap":
            cap = int(args[i + 1]); i += 2
        elif args[i] == "--width":
            width = int(args[i + 1]); i += 2
        elif args[i] == "--start":
            start_arg = args[i + 1]; i += 2
        elif args[i] == "--end":
            end_arg = args[i + 1]; i += 2
        else:
            i += 1
    start = parse_time(start_arg)
    end = parse_time(end_arg)
    meta = get_metadata(video)
    duration = (end or meta["duration_seconds"]) - (start or 0.0)
    target = target_frame_budget(duration, cap)
    frames, info = select_frames(video, out, engine, cap, target, width, start, end)
    print(json.dumps({"meta": meta, "info": info, "frames": frames}, indent=2))
