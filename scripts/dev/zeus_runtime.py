"""Zeus runtime task utilities.

This module provides a minimal filesystem-backed task runner helper with a
simple dead-letter queue (DLQ) policy. Any task that fails three times is
moved under ``logs/_ipc/dlq`` for further inspection.

The design follows the project's offline-first philosophy: all coordination
happens through plain files so that the behaviour remains deterministic and
fully auditable.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

IPC_ROOT = Path("logs") / "_ipc"
TASK_ROOT = IPC_ROOT / "tasks"
DLQ_ROOT = IPC_ROOT / "dlq"
MAX_FAILURES = 3
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _ensure_directory(path: Path) -> None:
    """Create the parent directory for *path* when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> Dict[str, Any]:
    """Load JSON data from *path* returning an empty dict on failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Persist *payload* as UTF-8 encoded JSON at *path*."""
    _ensure_directory(path)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _parse_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        return datetime.strptime(value, ISO_FORMAT).astimezone(timezone.utc)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)


@dataclass
class TaskEnvelope:
    """Represents a single task file along with its metadata."""

    path: Path
    payload: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: Optional[str] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dlq_at: Optional[datetime] = None

    @classmethod
    def load(cls, path: Path) -> "TaskEnvelope":
        data = _read_json(path)
        updated_at = _parse_timestamp(data.get("updated_at"))
        dlq_value = data.get("dlq_at")
        dlq_at = _parse_timestamp(dlq_value) if dlq_value else None
        return cls(
            path=path,
            payload=data.get("payload", {}),
            attempts=int(data.get("attempts", 0)),
            last_error=data.get("last_error"),
            updated_at=updated_at,
            dlq_at=dlq_at,
        )

    def save(self) -> None:
        payload = {
            "payload": self.payload,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "updated_at": self.updated_at.strftime(ISO_FORMAT),
        }
        if self.dlq_at is not None:
            payload["dlq_at"] = self.dlq_at.strftime(ISO_FORMAT)
        _write_json(self.path, payload)

    def record_success(self) -> None:
        self.attempts = 0
        self.last_error = None
        self.updated_at = datetime.now(timezone.utc)
        self.save()

    def record_failure(self, error_message: str) -> None:
        self.attempts += 1
        self.last_error = error_message
        self.updated_at = datetime.now(timezone.utc)
        if self.attempts >= MAX_FAILURES:
            self._move_to_dlq()
        else:
            self.save()

    def _move_to_dlq(self) -> None:
        self.dlq_at = datetime.now(timezone.utc)
        self.save()  # Persist final state before moving
        # Preserve original queue hierarchy by mirroring the relative path inside DLQ_ROOT.
        try:
            relative_path = self.path.relative_to(TASK_ROOT)
        except ValueError:
            relative_path = Path(self.path.name)

        dlq_dir = DLQ_ROOT / relative_path.parent if relative_path.parent != Path(".") else DLQ_ROOT
        dlq_dir.mkdir(parents=True, exist_ok=True)

        timestamp = self.dlq_at.strftime("%Y%m%dT%H%M%S%f")
        base_name = relative_path.stem
        suffix = relative_path.suffix
        target_path = dlq_dir / f"{base_name}__dlq_{timestamp}{suffix}"
        counter = 1
        while target_path.exists():
            target_path = dlq_dir / f"{base_name}__dlq_{timestamp}_{counter}{suffix}"
            counter += 1
        shutil.move(str(self.path), target_path)
        self.path = target_path


__all__ = [
    "TaskEnvelope",
    "DLQ_ROOT",
    "TASK_ROOT",
    "IPC_ROOT",
    "MAX_FAILURES",
]
