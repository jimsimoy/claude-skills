#!/usr/bin/env python3
"""Shared configuration helpers for /watch."""
from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "watch-skill"
CONFIG_FILE = CONFIG_DIR / ".env"

DEFAULT_DETAIL = "balanced"
VALID_DETAILS = {"transcript", "efficient", "balanced", "token-burner"}

DETAIL_CAPS = {
    "transcript": None,
    "efficient": 50,
    "balanced": 100,
    "token-burner": None,
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


def get_detail() -> str:
    env_values = read_dotenv()
    detail = os.environ.get("WATCH_DETAIL") or env_values.get("WATCH_DETAIL") or DEFAULT_DETAIL
    return detail if detail in VALID_DETAILS else DEFAULT_DETAIL


def frame_cap(detail: str) -> int | None:
    return DETAIL_CAPS.get(detail, 100)
