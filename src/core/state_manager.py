"""Utilities for managing filesystem-backed state with clock drift protection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


class ClockDriftError(RuntimeError):
    """Raised when a stamp timestamp is outside the allowed drift tolerance."""


@dataclass(frozen=True)
class StateManagerConfig:
    """Configuration for :class:`StateManager`."""

    root: Path
    stamp_dir: Path
    log_dir: Path
    cache_dir: Path
    clock_drift_tolerance: timedelta = timedelta(seconds=5)


class StateManager:
    """Manage stamps, logs, and cache files in the local filesystem.

    The manager provides deterministic, offline-safe utilities for interacting with
    the three-tier state model described in the project documentation:

    * ``stamps`` – single-value ISO timestamps used for pipeline coordination.
    * ``logs`` – append-only text files for audit trails.
    * ``cache`` – JSON documents storing structured state.

    The manager implements a clock drift guard that tolerates small forward/backward
    jumps in the system clock while rejecting negative durations that exceed the
    configured tolerance.
    """

    def __init__(self, config: StateManagerConfig) -> None:
        self._config = config
        self._config.stamp_dir.mkdir(parents=True, exist_ok=True)
        self._config.log_dir.mkdir(parents=True, exist_ok=True)
        self._config.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Stamp utilities
    # ------------------------------------------------------------------
    def get_stamp(self, name: str) -> Optional[datetime]:
        """Return the stored timestamp for ``name`` or ``None`` if missing."""

        path = self._stamp_path(name)
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            return None

        if not content:
            return None

        try:
            return datetime.fromisoformat(content)
        except ValueError:
            return None

    def set_stamp(self, name: str, value: Optional[datetime] = None) -> datetime:
        """Persist ``value`` (defaults to current time) as ISO timestamp for ``name``."""

        timestamp = value or datetime.now()
        self._write_text_atomic(self._stamp_path(name), timestamp.isoformat())
        return timestamp

    def stamp_age(self, name: str, *, now: Optional[datetime] = None) -> Optional[timedelta]:
        """Return the age of ``name`` relative to ``now`` with clock drift guard.

        ``None`` is returned when the stamp does not exist. When the stored timestamp
        appears to be in the future the difference is tolerated up to the configured
        ``clock_drift_tolerance`` and clamped to zero. Larger negative deltas raise a
        :class:`ClockDriftError`.
        """

        stamp = self.get_stamp(name)
        if stamp is None:
            return None

        current_time = now or datetime.now()
        delta = current_time - stamp

        if delta >= timedelta(0):
            return delta

        drift = abs(delta)
        tolerance = self._config.clock_drift_tolerance

        if drift <= tolerance:
            return timedelta(0)

        raise ClockDriftError(
            f"Stamp '{name}' is {drift.total_seconds():.3f}s ahead of current time "
            f"(tolerance {tolerance.total_seconds():.3f}s)."
        )

    # ------------------------------------------------------------------
    # Log utilities
    # ------------------------------------------------------------------
    def append_log(self, name: str, text: str) -> None:
        """Append ``text`` with newline to the log identified by ``name``."""

        line = text if text.endswith("\n") else f"{text}\n"
        path = self._log_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError:
            # Fail silently to maintain offline determinism; callers can inspect logs.
            pass

    # ------------------------------------------------------------------
    # Cache utilities
    # ------------------------------------------------------------------
    def cache_get(self, name: str, loader) -> Any:
        """Load data from cache ``name`` using ``loader`` (callable(file_path))."""

        path = self._cache_path(name)
        if not path.exists():
            return None

        try:
            return loader(path)
        except (OSError, ValueError, TypeError):
            return None

    def cache_set(self, name: str, dumper, data: Any) -> bool:
        """Persist ``data`` to cache ``name`` using ``dumper(file_path, data)``."""

        path = self._cache_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            dumper(path, data)
            return True
        except (OSError, ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _stamp_path(self, name: str) -> Path:
        return self._config.stamp_dir / f"{name}.stamp"

    def _log_path(self, name: str) -> Path:
        return self._config.log_dir / name

    def _cache_path(self, name: str) -> Path:
        return self._config.cache_dir / name

    def _write_text_atomic(self, path: Path, content: str) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(path)
        except OSError:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise
