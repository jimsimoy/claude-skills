#!/usr/bin/env python3
"""Shared configuration helpers for /stream-watch."""
from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "stream-watch"
CONFIG_FILE = CONFIG_DIR / ".env"

DEFAULT_DEPTH = "standard"
VALID_DEPTHS = {"captions-only", "quick", "standard", "deep"}

DEPTH_CAPS = {
    "captions-only": None,
    "quick": 50,
    "standard": 100,
    "deep": None,
}


def read_dotenv(path: Path | None = None) -> dict[str, str]:
    path = path or CONFIG_FILE
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        values[key] = value
    return values


def get_depth() -> str:
    env_values = read_dotenv()
    depth = os.environ.get("STREAMWATCH_DEPTH") or env_values.get("STREAMWATCH_DEPTH") or DEFAULT_DEPTH
    return depth if depth in VALID_DEPTHS else DEFAULT_DEPTH


def frame_cap(depth: str) -> int | None:
    return DEPTH_CAPS.get(depth, 100)
