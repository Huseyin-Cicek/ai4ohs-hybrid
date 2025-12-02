"""Unit tests for warning rate-limiting utilities."""

import logging
from datetime import datetime, timedelta

import pytest

from src.utils.warnings import WarningSampler, rate_limited_warning


class _MemoryLogger:
    """Simple stand-in for :class:`logging.Logger`."""

    def __init__(self) -> None:
        self.records: list[tuple[int, str]] = []

    def log(self, level: int, message: str, *args, **kwargs) -> None:  # noqa: D401
        # Ignore ``*args``/``**kwargs`` to mirror logging behaviour.
        self.records.append((level, message))


@pytest.fixture
def memory_logger() -> _MemoryLogger:
    return _MemoryLogger()


def _make_timestamp(offset_seconds: int = 0) -> datetime:
    base = datetime(2025, 1, 1, 12, 0, 0)
    return base + timedelta(seconds=offset_seconds)


def test_warning_sampler_allows_within_limit(memory_logger: _MemoryLogger) -> None:
    sampler = WarningSampler(max_per_window=3, window_seconds=60)

    for offset in (0, 10, 20):
        logged = sampler.log_warning(memory_logger, "queue depth high", now=_make_timestamp(offset))
        assert logged is True

    assert len(memory_logger.records) == 3
    assert all(level == logging.WARNING for level, _ in memory_logger.records)


def test_warning_sampler_suppresses_and_summarises(memory_logger: _MemoryLogger) -> None:
    sampler = WarningSampler(max_per_window=2, window_seconds=60)

    # First two warnings pass through.
    assert sampler.log_warning(memory_logger, "queue depth high", now=_make_timestamp(0)) is True
    assert sampler.log_warning(memory_logger, "queue depth high", now=_make_timestamp(10)) is True

    # Third warning inside the window is suppressed.
    assert sampler.log_warning(memory_logger, "queue depth high", now=_make_timestamp(20)) is False
    assert len(memory_logger.records) == 2

    # Next warning with new timestamp should flush summary + message.
    assert sampler.log_warning(memory_logger, "queue depth high", now=_make_timestamp(61)) is True

    summary_level, summary_msg = memory_logger.records[-2]
    warning_level, warning_msg = memory_logger.records[-1]

    assert summary_level == logging.INFO
    assert "Suppressed 1 occurrences" in summary_msg
    assert warning_level == logging.WARNING
    assert warning_msg == "queue depth high"


def test_rate_limited_warning_uses_helper(memory_logger: _MemoryLogger) -> None:
    sampler = WarningSampler(max_per_window=1, window_seconds=60)

    assert rate_limited_warning(memory_logger, "cache miss", sampler=sampler) is True
    assert rate_limited_warning(memory_logger, "cache miss", sampler=sampler) is False

    assert len(memory_logger.records) == 1
    assert memory_logger.records[0][1] == "cache miss"
