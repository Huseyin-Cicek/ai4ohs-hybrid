"""Utilities for sampling and rate-limiting warning logs.

This module provides deterministic, in-memory rate limiting that caps the number
of times an identical warning can be emitted within a configurable time window.
It is designed for offline, single-process usage (Zeus components) and relies on
standard library data structures only.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Deque, Dict, Optional

__all__ = ["WarningSampler", "default_warning_sampler", "rate_limited_warning"]

__all__ = [
    "WarningSampler",
    "default_warning_sampler",
    "get_warning_sampler",
    "rate_limited_warning",
]

_SAMPLER_WINDOW_SECONDS = 60

@dataclass
class _WarningState:
    """Internal bookkeeping for a single warning key."""

    timestamps: Deque[datetime] = field(default_factory=deque)
    suppressed_count: int = 0


class WarningSampler:
    """Rate-limit repeated warnings within a fixed time window.

    Example
    -------
    >>> sampler = WarningSampler(max_per_window=3, window_seconds=60)
    >>> sampler.log_warning(logger, "Queue depth high", key="queue_depth")

    The sampler keeps per-key state in memory and is safe for multi-threaded
    access.
    """

    def __init__(
        self,
        *,
        max_per_window: int = 5,
        window_seconds: int = 60,
        summary_level: int = logging.INFO,
    ) -> None:
        if max_per_window <= 0:
            raise ValueError("max_per_window must be a positive integer")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be a positive integer")
        self._max_per_window = max_per_window
        self._window = timedelta(seconds=window_seconds)
        self._summary_level = summary_level
        self._states: Dict[str, _WarningState] = defaultdict(_WarningState)
        self._lock = Lock()

    def log_warning(
        self,
        logger: logging.Logger,
        message: str,
        *,
        key: Optional[str] = None,
        level: int = logging.WARNING,
        now: Optional[datetime] = None,
        extra: Optional[dict] = None,
    ) -> bool:
        """Attempt to log the warning, respecting the rate limit.

        Parameters
        ----------
        logger:
            The logger instance to use.
        message:
            The warning message.
        key:
            Optional grouping key. Defaults to the message text when omitted.
        level:
            Logging level for the warning; defaults to ``logging.WARNING``.
        now:
            Optional timestamp used during testing. Defaults to ``datetime.now``.
        extra:
            Optional ``logging`` extra dictionary.

        Returns
        -------
        bool
            ``True`` when the message is logged, ``False`` when it is suppressed.
        """

        record_time = now or datetime.now()
        group_key = key or message

        with self._lock:
            state = self._states[group_key]
            cutoff = record_time - self._window

            # Drop timestamps outside the current window.
            while state.timestamps and state.timestamps[0] < cutoff:
                state.timestamps.popleft()

            if len(state.timestamps) < self._max_per_window:
                # If we suppressed earlier events in this window, emit a summary first.
                if state.suppressed_count:
                    summary = (
                        f"Suppressed {state.suppressed_count} occurrences of warning "
                        f"'{group_key}' in the last {int(self._window.total_seconds())}s"
                    )
                    logger.log(self._summary_level, summary)
                    state.suppressed_count = 0

                state.timestamps.append(record_time)
                logger.log(level, message, extra=extra)
                return True

            # Rate limit reached; increment suppressed counter and skip logging.
            state.suppressed_count += 1
            return False

    def flush(self, logger: logging.Logger, *, now: Optional[datetime] = None) -> None:
        """Emit summaries for any suppressed warnings and reset counters."""

        _ = now  # Reserved for future use (e.g., time-dependent summaries).
        with self._lock:
            for key, state in self._states.items():
                if state.suppressed_count:
                    summary = (
                        f"Suppressed {state.suppressed_count} occurrences of warning "
                        f"'{key}' in the last {int(self._window.total_seconds())}s"
                    )
                    logger.log(self._summary_level, summary)
                    state.suppressed_count = 0


def rate_limited_warning(
_SamplerRegistryKey = tuple[int, int, int]
_sampler_registry: Dict[_SamplerRegistryKey, WarningSampler] = {}


def get_warning_sampler(
    max_per_window: int = 5,
    *,
    window_seconds: int = 60,
    summary_level: int = logging.INFO,
) -> WarningSampler:
    """Return a cached :class:`WarningSampler` for the requested configuration."""

    key: _SamplerRegistryKey = (max_per_window, window_seconds, summary_level)
    if key not in _sampler_registry:
        _sampler_registry[key] = WarningSampler(
            max_per_window=max_per_window,
            window_seconds=window_seconds,
            summary_level=summary_level,
        )
    return _sampler_registry[key]
    logger: logging.Logger,
    message: str,
    *,
    key: Optional[str] = None,
    max_per_minute: int = 5,
    sampler: Optional[WarningSampler] = None,
    level: int = logging.WARNING,
    window_seconds: int = 60,
    extra: Optional[dict] = None,
) -> bool:
    """Helper that logs with a per-minute rate limit."""

    sampler = sampler or default_warning_sampler


    if sampler is None:
        sampler = get_warning_sampler(
            max_per_window=max_per_minute,
            window_seconds=window_seconds,
        )
    else:
        # If caller-provided sampler does not match requested configuration we trust the
        # explicit sampler, but log once when debugging to aid troubleshooting.
        if (
            sampler.max_per_window != max_per_minute
            or sampler.window_seconds != window_seconds
        ):
            logging.getLogger(__name__).debug(
                "Using caller-provided WarningSampler (max=%s/sec window=%ss) "
                "instead of helper arguments (max=%s/min window=%ss)",
                sampler.max_per_window,
                sampler.window_seconds,
                max_per_minute,
                window_seconds,
            )
        logger,
        message,
        key=key,
        level=level,
        extra=extra,
    )


default_warning_sampler = WarningSampler()
default_warning_sampler = get_warning_sampler()
