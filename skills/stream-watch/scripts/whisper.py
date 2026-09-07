#!/usr/bin/env python3
"""Whisper fallback transcription via Groq or OpenAI — used only when a
source has no captions. Pure stdlib: no `groq`/`openai` SDK dependency.

Only ever contacts api.groq.com or api.openai.com, and only the extracted
audio (never the video itself) is uploaded.
"""
from __future__ import annotations

import io
import json
import math
import mimetypes
import os
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"
OPENAI_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_MODEL = "whisper-1"

# Both providers cap uploads at 25MB; stay comfortably under for multipart overhead.
MAX_UPLOAD_BYTES = 24 * 1024 * 1024
MAX_ATTEMPTS = 4
MAX_RATE_LIMIT_RETRIES = 2
RETRY_BASE_DELAY = 2.0


def load_api_key(prefer: str | None = None) -> tuple[str, str] | tuple[None, None]:
    def from_env(name: str) -> str | None:
        v = os.environ.get(name)
        return v.strip() if v and v.strip() else None

    def from_dotenv(path: Path, name: str) -> str | None:
        if not path.exists():
            return None
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() != name:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
                value = value[1:-1]
            return value or None
        return None

    dotenv_candidates = [Path.home() / ".config" / "stream-watch" / ".env", Path.cwd() / ".env"]
    order = [("GROQ_API_KEY", "groq"), ("OPENAI_API_KEY", "openai")]
    if prefer:
        order = [pair for pair in order if pair[1] == prefer]

    for env_name, backend in order:
        value = from_env(env_name)
        if not value:
            for candidate in dotenv_candidates:
                value = from_dotenv(candidate, env_name)
                if value:
                    break
        if value:
            return backend, value
    return None, None


def extract_audio(video_path: str, out_path: Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg not installed")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(Path(video_path).resolve()),
        "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1", "-b:a", "64k",
        str(out_path.resolve()),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        raise SystemExit(f"audio extraction failed: {result.stderr.strip()}")
    return out_path


def audio_duration(path: Path) -> float:
    if shutil.which("ffprobe") is None:
        raise SystemExit("ffprobe not installed")
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path.resolve())],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"ffprobe failed: {result.stderr.strip()}")
    return float(json.loads(result.stdout or "{}").get("format", {}).get("duration") or 0.0)


def plan_chunks(total_seconds: float, total_bytes: int, max_bytes: int = MAX_UPLOAD_BYTES) -> list[tuple[float, float]]:
    if total_bytes <= max_bytes or total_seconds <= 0:
        return [(0.0, total_seconds)]
    n = math.ceil(total_bytes / max_bytes)
    step = total_seconds / n
    plan = []
    for i in range(n):
        offset = i * step
        duration = (total_seconds - offset) if i == n - 1 else step
        plan.append((round(offset, 3), round(duration, 3)))
    return plan


def split_audio(full_audio: Path, out_dir: Path, plan: list[tuple[float, float]]) -> list[tuple[Path, float]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = []
    for i, (offset, duration) in enumerate(plan):
        chunk_path = out_dir / f"chunk_{i:03d}.mp3"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{offset:.3f}", "-i", str(full_audio.resolve()),
            "-t", f"{duration:.3f}", "-c", "copy", str(chunk_path.resolve()),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not chunk_path.exists():
            raise SystemExit(f"chunk {i} split failed: {result.stderr.strip()}")
        chunks.append((chunk_path, offset))
    return chunks


def _multipart_body(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = f"----streamwatch{uuid.uuid4().hex}"
    eol = b"\r\n"
    buf = io.BytesIO()
    for name, value in fields.items():
        buf.write(f"--{boundary}".encode() + eol)
        buf.write(f'Content-Disposition: form-data; name="{name}"'.encode() + eol + eol)
        buf.write(str(value).encode() + eol)
    mimetype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    buf.write(f"--{boundary}".encode() + eol)
    buf.write(f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"'.encode() + eol)
    buf.write(f"Content-Type: {mimetype}".encode() + eol + eol)
    buf.write(file_path.read_bytes() + eol)
    buf.write(f"--{boundary}--".encode() + eol)
    return buf.getvalue(), boundary


def _post(endpoint: str, api_key: str, model: str, audio_path: Path) -> dict:
    body, boundary = _multipart_body(
        {"model": model, "response_format": "verbose_json", "temperature": "0"}, audio_path
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "stream-watch/1.0 (+claude-code)",
    }
    context = ssl.create_default_context()
    rate_limit_hits = 0
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        request = Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=300, context=context) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if 400 <= exc.code < 500 and exc.code != 429:
                raise SystemExit(f"Whisper request failed: {exc}")
            if exc.code == 429:
                rate_limit_hits += 1
                if rate_limit_hits >= MAX_RATE_LIMIT_RETRIES:
                    raise SystemExit(f"Whisper rate-limited past retry budget: {exc}")
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            if attempt < MAX_ATTEMPTS - 1:
                print(f"[stream-watch] whisper HTTP {exc.code} — retrying in {delay:.1f}s", file=sys.stderr)
                time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                delay = RETRY_BASE_DELAY * (attempt + 1)
                print(f"[stream-watch] whisper network error — retrying in {delay:.1f}s", file=sys.stderr)
                time.sleep(delay)

    raise SystemExit(f"Whisper request failed after {MAX_ATTEMPTS} attempts: {last_error}")


def _segments_from_response(data: dict) -> list[dict]:
    out = []
    for seg in data.get("segments") or []:
        text = (seg.get("text") or "").strip()
        if text:
            out.append({"start": round(float(seg.get("start") or 0), 2), "end": round(float(seg.get("end") or 0), 2), "text": text})
    if not out and (full := (data.get("text") or "").strip()):
        out.append({"start": 0.0, "end": 0.0, "text": full})
    return out


def _shift(segments: list[dict], offset: float) -> list[dict]:
    if offset == 0:
        return segments
    return [{"start": round(s["start"] + offset, 2), "end": round(s["end"] + offset, 2), "text": s["text"]} for s in segments]


def transcribe_video(video_path: str, audio_out: Path, backend: str | None = None, api_key: str | None = None) -> tuple[list[dict], str]:
    if backend is None or api_key is None:
        detected_backend, detected_key = load_api_key()
        backend, api_key = backend or detected_backend, api_key or detected_key
    if not backend or not api_key:
        raise SystemExit(
            "No Whisper API key set (GROQ_API_KEY or OPENAI_API_KEY). "
            "Run setup.py, or skip Whisper entirely with --no-whisper."
        )

    endpoint, model = (GROQ_ENDPOINT, GROQ_MODEL) if backend == "groq" else (OPENAI_ENDPOINT, OPENAI_MODEL)
    print(f"[stream-watch] extracting audio for Whisper ({backend})…", file=sys.stderr)
    audio_path = extract_audio(video_path, audio_out)
    audio_bytes = audio_path.stat().st_size

    def transcribe_one(path: Path) -> list[dict]:
        return _segments_from_response(_post(endpoint, api_key, model, path))

    if audio_bytes <= MAX_UPLOAD_BYTES:
        segments = transcribe_one(audio_path)
    else:
        duration = audio_duration(audio_path)
        plan = plan_chunks(duration, audio_bytes)
        chunks = split_audio(audio_path, audio_out.parent / "chunks", plan)
        segments = []
        failures = 0
        for i, (path, offset) in enumerate(chunks):
            try:
                segments.extend(_shift(transcribe_one(path), offset))
            except SystemExit as exc:
                failures += 1
                print(f"[stream-watch] chunk {i + 1}/{len(chunks)} failed: {exc}", file=sys.stderr)
        if failures == len(chunks):
            raise SystemExit("Whisper failed on every audio chunk")

    if not segments:
        raise SystemExit("Whisper returned no segments")
    return segments, backend


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: whisper.py <video-path> [audio-out.mp3] [--backend groq|openai]", file=sys.stderr)
        raise SystemExit(2)
    video = sys.argv[1]
    audio_out = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else Path("audio.mp3")
    backend_override = sys.argv[sys.argv.index("--backend") + 1] if "--backend" in sys.argv else None
    segments, backend = transcribe_video(video, audio_out, backend=backend_override)
    print(json.dumps({"backend": backend, "segments": segments}, indent=2))
