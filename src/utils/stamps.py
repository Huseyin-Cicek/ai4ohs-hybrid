"""
Zeus Stamp Management Utilities

Provides atomic write/read operations for pipeline completion stamps.

Usage:
    from src.utils.stamps import write_stamp_atomic, read_stamp_or_epoch
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Final

# Default timestamp format (ISO 8601 with seconds and microseconds)
STAMP_TIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S.%f"


def write_stamp_atomic(stamp_dir: Path, stage: str) -> None:
    """
    Atomically write a completion stamp for a pipeline stage.

    This creates the directory (if needed), writes the timestamp to a temporary
    file, and then renames it over the final file to avoid partial writes.

    Args:
        stamp_dir: Directory for stamp files (e.g., PROJECT_ROOT / "logs" / "pipelines").
        stage: Pipeline stage name (e.g., "00_ingest", "01_staging").
    """
    stamp_dir.mkdir(parents=True, exist_ok=True)

    stamp_file = stamp_dir / f"{stage}.stamp"
    tmp_file = stamp_file.with_suffix(".stamp.tmp")

    # Use ISO 8601 representation; datetime.now().isoformat() is fine, but we
    # keep format explicit to avoid locale surprises.
    now_str = datetime.now().strftime(STAMP_TIME_FORMAT)
    tmp_file.write_text(now_str, encoding="utf-8")

    # Atomic replace on the same filesystem
    tmp_file.replace(stamp_file)


def read_stamp_or_epoch(stamp_dir: Path, stage: str) -> datetime:
    """
    Read the completion stamp timestamp or return Unix epoch if missing/invalid.

    Args:
        stamp_dir: Directory for stamp files.
        stage: Pipeline stage name.

    Returns:
        datetime: Parsed timestamp from the stamp file, or epoch
        (datetime.fromtimestamp(0)) if the file is missing or cannot be parsed.
    """
    stamp_file = stamp_dir / f"{stage}.stamp"

    if not stamp_file.exists():
        return datetime.fromtimestamp(0)

    try:
        raw = stamp_file.read_text(encoding="utf-8").strip()
        # Try strict ISO 8601 first (our own format), then fall back to fromisoformat
        try:
            return datetime.strptime(raw, STAMP_TIME_FORMAT)
        except ValueError:
            # If format changes in the future, fromisoformat can still parse many variants.
            return datetime.fromisoformat(raw)
    except Exception:
        # On any IO or parse error, fall back to epoch to keep callers simple and robust.
        return datetime.fromtimestamp(0)
