#!/usr/bin/env python3
"""Preflight / installer for /streamwatch.

  setup.py --check   Silent on success (exit 0). Prints one line + non-zero
                      exit code when something needs fixing.
  setup.py --json    Machine-readable status.
  setup.py           Installer: installs missing binaries where possible,
                      scaffolds the config file. Never touches an existing key.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CONFIG_FILE, CONFIG_DIR, get_depth  # noqa: E402

REQUIRED = ["ffmpeg", "ffprobe", "yt-dlp"]

ENV_TEMPLATE = """# /streamwatch configuration
#
# Whisper fallback is used only when yt-dlp can't find captions (or the
# input is a local file with no subtitle track). Leave both keys blank to
# skip it — /streamwatch still works, just frames-only for uncaptioned
# sources.
#
# Groq: https://console.groq.com/keys  (cheaper/faster, preferred)
# OpenAI: https://platform.openai.com/api-keys  (fallback)

GROQ_API_KEY=
OPENAI_API_KEY=

# captions-only | quick | standard | deep
# STREAMWATCH_DEPTH=standard
"""


def which(name: str) -> str | None:
    return shutil.which(name)


def missing_binaries() -> list[str]:
    return [b for b in REQUIRED if not which(b)]


def _read_key(name: str) -> str | None:
    value = os.environ.get(name)
    if value and value.strip():
        return value.strip()
    if not CONFIG_FILE.exists():
        return None
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        if key.strip() == name and raw.strip():
            return raw.strip()
    return None


def has_api_key() -> tuple[bool, str | None]:
    if _read_key("GROQ_API_KEY"):
        return True, "groq"
    if _read_key("OPENAI_API_KEY"):
        return True, "openai"
    return False, None


def setup_complete() -> bool:
    return _read_key("SETUP_COMPLETE") == "true"


def scaffold_config() -> bool:
    if CONFIG_FILE.exists():
        return False
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(ENV_TEMPLATE, encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass
    return True


def mark_setup_complete() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else ""
    if "SETUP_COMPLETE=" in existing:
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    CONFIG_FILE.write_text((existing or ENV_TEMPLATE) + "SETUP_COMPLETE=true\n", encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def _warn_if_world_readable() -> None:
    if not CONFIG_FILE.exists():
        return
    try:
        if CONFIG_FILE.stat().st_mode & 0o044:
            print(f"[streamwatch] warning: {CONFIG_FILE} is readable by other users — chmod 600 it.", file=sys.stderr)
    except OSError:
        pass


def status() -> dict:
    missing = missing_binaries()
    key_present, backend = has_api_key()
    complete = setup_complete()
    _warn_if_world_readable()

    if not missing and key_present:
        state = "ready"
    elif missing and not key_present:
        state = "needs_install_and_key"
    elif missing:
        state = "needs_install"
    else:
        state = "needs_key"

    return {
        "status": state,
        "can_proceed": (not missing) and (key_present or complete),
        "first_run": not complete,
        "missing_binaries": missing,
        "whisper_backend": backend,
        "has_api_key": key_present,
        "config_file": str(CONFIG_FILE),
        "depth": get_depth(),
        "platform": platform.system(),
    }


def cmd_check() -> int:
    s = status()
    if s["can_proceed"]:
        return 0
    bits = []
    if s["missing_binaries"]:
        bits.append(f"missing: {', '.join(s['missing_binaries'])}")
    if not s["has_api_key"] and s["first_run"]:
        bits.append("no Whisper key")
    print(f"[streamwatch] setup needed ({'; '.join(bits)}). Run: python3 {Path(__file__).resolve()}", file=sys.stderr)
    if s["missing_binaries"] and not s["has_api_key"]:
        return 4
    if s["missing_binaries"]:
        return 2
    return 3


def cmd_json() -> int:
    json.dump(status(), sys.stdout, indent=2)
    print()
    return 0


def cmd_install() -> int:
    missing = missing_binaries()
    if missing:
        system = platform.system()
        if system == "Darwin" and which("brew"):
            pkgs = sorted({"ffmpeg" if b in ("ffmpeg", "ffprobe") else b for b in missing})
            print(f"[setup] installing via brew: {' '.join(pkgs)}", file=sys.stderr)
            result = subprocess.run(["brew", "install", *pkgs])
            if result.returncode != 0 or missing_binaries():
                print("[setup] brew install did not resolve all dependencies", file=sys.stderr)
                return 2
        else:
            print(f"[setup] missing binaries: {', '.join(missing)}. Install manually:", file=sys.stderr)
            print("  ffmpeg/ffprobe: https://ffmpeg.org/download.html", file=sys.stderr)
            print("  yt-dlp: https://github.com/yt-dlp/yt-dlp#installation", file=sys.stderr)
            return 2

    created = scaffold_config()
    print(f"[setup] {'created' if created else 'found existing'} config: {CONFIG_FILE}")

    key_present, backend = has_api_key()
    if key_present:
        mark_setup_complete()
        print(f"[setup] ready — whisper backend: {backend}")
        return 0

    print("[setup] one step left (optional): add a Whisper API key to the config file above.")
    print("        Without one, /streamwatch still works but falls back to frames-only when captions are missing.")
    return 3


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == "--check":
        return cmd_check()
    if arg == "--json":
        return cmd_json()
    return cmd_install()


if __name__ == "__main__":
    raise SystemExit(main())
