"""Utilities for managing Zeus system health indicator files.

This script writes status markers under ``logs/system`` so other tooling can
check whether Zeus is healthy, degraded, or down without calling an API. The
convention is that exactly one of ``health.ok``, ``health.degraded`` or
``health.down`` exists at a time. When a new status is written the other marker
files are removed. Status files store a tiny JSON payload with the status,
timestamp, and optional message explaining the state.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

HEALTH_DIR = Path("logs") / "system"
STATUS_FILES: Dict[str, Path] = {
    "ok": HEALTH_DIR / "health.ok",
    "degraded": HEALTH_DIR / "health.degraded",
    "down": HEALTH_DIR / "health.down",
}


def _ensure_directory() -> None:
    """Create the health directory if it does not already exist."""

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)


def _write_status(status: str, message: Optional[str]) -> Path:
    """Write the selected status file, removing the others."""

    _ensure_directory()

    payload = {
        "status": status,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    if message:
        payload["message"] = message

    target_path = STATUS_FILES[status]
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for other_status, other_path in STATUS_FILES.items():
        if other_status != status and other_path.exists():
            other_path.unlink()

    return target_path


def _read_current_status() -> Tuple[Optional[str], Optional[dict]]:
    """Return the current status and payload if any marker exists."""

    for status, marker_path in STATUS_FILES.items():
        if marker_path.exists():
            try:
                payload = json.loads(marker_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return status, None
            return status, payload
    return None, None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage Zeus system health indicator files. Without arguments, "
        "the script prints the current status if one exists."
    )
    parser.add_argument(
        "--status",
        choices=STATUS_FILES.keys(),
        help="Status to set (creates the corresponding health file).",
    )
    parser.add_argument(
        "--message",
        help="Optional message to store alongside the status.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the current status payload after performing any updates.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.status:
        path = _write_status(args.status, args.message)
        print(f"Wrote {args.status!r} health marker to {path}")

    status, payload = _read_current_status()

    if args.show or not args.status:
        if status is None:
            print("No health marker present. Use --status to create one.")
        else:
            print(json.dumps({"status": status, "payload": payload}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
