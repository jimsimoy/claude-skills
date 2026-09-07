#!/usr/bin/env python3
"""Parse a WebVTT file into clean, timestamped segments.

Auto-generated YouTube captions repeat each line 2-3 times as it scrolls
into view; consecutive-duplicate collapsing removes that noise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_TIMECODE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})"
)
_TAG = re.compile(r"<[^>]+>")


def _seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_vtt(path: str) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    segments: list[dict] = []
    i = 0
    while i < len(lines):
        match = _TIMECODE.match(lines[i])
        if not match:
            i += 1
            continue
        start = _seconds(*match.groups()[:4])
        end = _seconds(*match.groups()[4:])
        i += 1

        text_lines = []
        while i < len(lines) and lines[i].strip():
            cleaned = _TAG.sub("", lines[i]).strip()
            if cleaned:
                text_lines.append(cleaned)
            i += 1
        text = " ".join(text_lines).strip()
        if text:
            segments.append({"start": round(start, 2), "end": round(end, 2), "text": text})
        i += 1
    return _collapse_duplicates(segments)


def _collapse_duplicates(segments: list[dict]) -> list[dict]:
    out: list[dict] = []
    for seg in segments:
        if out and seg["text"] == out[-1]["text"]:
            out[-1]["end"] = seg["end"]
            continue
        if out and seg["text"].startswith(out[-1]["text"] + " "):
            out[-1]["text"], out[-1]["end"] = seg["text"], seg["end"]
            continue
        out.append(seg)
    return out


def filter_range(segments: list[dict], start: float | None, end: float | None) -> list[dict]:
    if start is None and end is None:
        return segments
    lo = start if start is not None else float("-inf")
    hi = end if end is not None else float("inf")
    return [s for s in segments if s["end"] >= lo and s["start"] <= hi]


def render(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        t = int(seg["start"])
        lines.append(f"[{t // 60:02d}:{t % 60:02d}] {seg['text']}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: transcribe.py <vtt-path>", file=sys.stderr)
        raise SystemExit(2)
    print(render(parse_vtt(sys.argv[1])))
