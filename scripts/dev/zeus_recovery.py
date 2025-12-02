"""Zeus recovery utilities.

This module provides housekeeping helpers that clean up orphaned temporary
artifacts left in the filesystem-based IPC layer. It focuses on removing
items under ``logs/_ipc/tmp`` as well as lingering ``*.tmp`` files that may
appear when atomic writes are interrupted. All operations are deterministic
and work entirely offline.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List

IPC_ROOT = Path("logs") / "_ipc"
TMP_ROOT = IPC_ROOT / "tmp"
DEFAULT_TTL_HOURS = 24


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean orphaned IPC temp artifacts",
    )
    parser.add_argument(
        "--ttl-hours",
        type=float,
        default=DEFAULT_TTL_HOURS,
        help="Minimum age (in hours) before a temp artifact is deleted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything",
    )
    return parser.parse_args()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(path: Path, cutoff: datetime) -> bool:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except (FileNotFoundError, OSError):
        return False
    return mtime <= cutoff


def _delete_path(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _iter_tmp_files() -> Iterable[Path]:
    if not IPC_ROOT.exists():
        return []
    return IPC_ROOT.rglob("*.tmp")


def _cleanup_tmp_root(cutoff: datetime, dry_run: bool) -> List[Path]:
    removed: List[Path] = []
    if not TMP_ROOT.exists():
        return removed

    for entry in TMP_ROOT.iterdir():
        if _is_expired(entry, cutoff):
            removed.append(entry)
            _delete_path(entry, dry_run)
    return removed


def _cleanup_tmp_files(cutoff: datetime, dry_run: bool) -> List[Path]:
    removed: List[Path] = []
    for candidate in _iter_tmp_files():
        if candidate.parent == TMP_ROOT:
            continue  # handled by directory sweep above
        if _is_expired(candidate, cutoff):
            removed.append(candidate)
            _delete_path(candidate, dry_run)
    return removed


def clean_orphan_temps(ttl_hours: float, dry_run: bool = False) -> List[Path]:
    cutoff = _utcnow() - timedelta(hours=ttl_hours)
    removed_paths: List[Path] = []
    removed_paths.extend(_cleanup_tmp_root(cutoff, dry_run))
    removed_paths.extend(_cleanup_tmp_files(cutoff, dry_run))
    return removed_paths


def main() -> None:
    args = _parse_args()
    removed = clean_orphan_temps(ttl_hours=args.ttl_hours, dry_run=args.dry_run)

    if removed:
        print(
            f"TTL: {args.ttl_hours}h | Removed {len(removed)} artifact(s)"
            + (" (dry-run)" if args.dry_run else "")
        )
        for path in removed:
            try:
                relative = path.relative_to(IPC_ROOT.parent)
            except ValueError:
                relative = path
            print(f" - {relative}")
    else:
        suffix = " (dry-run)" if args.dry_run else ""
        print(f"TTL: {args.ttl_hours}h | No orphan temp artifacts found{suffix}")


if __name__ == "__main__":
    main()
