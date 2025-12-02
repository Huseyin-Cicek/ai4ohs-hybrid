"""Cross-platform file locking helpers.

Provides an exclusive file lock context manager that prefers the optional
``portalocker`` dependency when available and otherwise falls back to
platform-specific primitives.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

try:
    import portalocker  # type: ignore
except ImportError:  # pragma: no cover
    portalocker = None  # type: ignore


LockPath = Union[str, Path]


class FileLock:
    """Exclusive file lock with timeout support."""

    def __init__(
        self,
        lock_path: LockPath,
        *,
        timeout: Optional[float] = 10.0,
        poll_interval: float = 0.1,
    ) -> None:
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._handle: Optional[object] = None

    def acquire(self) -> None:
        """Acquire the lock within the configured timeout."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = None if self.timeout is None else time.monotonic() + self.timeout

        if portalocker is not None:
            self._acquire_portalocker(deadline)
        elif os.name == "nt":
            self._acquire_windows(deadline)
        else:
            self._acquire_posix(deadline)

    def release(self) -> None:
        """Release the lock if held."""
        if self._handle is None:
            return

        try:
            if portalocker is not None:
                portalocker.unlock(self._handle)
            elif os.name == "nt":
                self._release_windows()
            else:
                self._release_posix()
        finally:
            try:
                self._handle.close()  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
            self._handle = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    # Internal helpers -------------------------------------------------
    def _acquire_portalocker(self, deadline: Optional[float]) -> None:
        assert portalocker is not None
        while True:
            handle = self.lock_path.open("a+b")
            try:
                portalocker.lock(handle, portalocker.LockFlags.EXCLUSIVE)
                self._handle = handle
                return
            except portalocker.LockException:
                handle.close()
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError(f"Timeout while waiting for lock: {self.lock_path}")
                time.sleep(self.poll_interval)

    def _acquire_windows(self, deadline: Optional[float]) -> None:
        import msvcrt  # type: ignore

        lock_size = 1
        while True:
            handle = self.lock_path.open("a+b")
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, lock_size)
                self._handle = handle
                return
            except OSError:
                handle.close()
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError(f"Timeout while waiting for lock: {self.lock_path}")
                time.sleep(self.poll_interval)

    def _acquire_posix(self, deadline: Optional[float]) -> None:
        import fcntl  # type: ignore

        while True:
            handle = self.lock_path.open("a+b")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._handle = handle
                return
            except BlockingIOError:
                handle.close()
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError(f"Timeout while waiting for lock: {self.lock_path}")
                time.sleep(self.poll_interval)

    def _release_windows(self) -> None:
        import msvcrt  # type: ignore

        assert self._handle is not None
        msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]

    def _release_posix(self) -> None:
        import fcntl  # type: ignore

        assert self._handle is not None
        fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


@contextmanager
def file_lock(
    lock_path: LockPath,
    *,
    timeout: Optional[float] = 10.0,
    poll_interval: float = 0.1,
) -> Iterator[FileLock]:
    """Context manager helper for short-lived lock usage."""
    lock = FileLock(lock_path, timeout=timeout, poll_interval=poll_interval)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()
