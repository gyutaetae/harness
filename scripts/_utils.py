"""Shared utilities for harness scripts."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))


def find_project_root() -> Path:
    """Walk up from this file until a directory containing `.codex/`, `.git/`,
    or `tasks/` is found. Falls back to two levels up.
    """
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (
            (current / ".git").exists()
            or (current / ".codex").exists()
            or (current / "tasks").exists()
        ):
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def now_iso() -> str:
    """ISO 8601 timestamp in KST. Example: 2026-05-04T02:09:18+0900"""
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z")
