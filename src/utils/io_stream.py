"""Streaming utilities for working with large files in small chunks."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, Union

ChunkProcessor = Callable[[bytes], None]
PathLike = Union[str, Path]

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _ensure_path(path: PathLike) -> Path:
    """Coerce ``path`` into a :class:`Path` instance."""
    return path if isinstance(path, Path) else Path(path)


def read_chunks(path: PathLike, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
    """Yield file content in ``chunk_size`` byte chunks without loading the whole file."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    file_path = _ensure_path(path)
    with file_path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk


def iter_lines(
    path: PathLike,
    *,
    encoding: str = "utf-8",
    errors: str = "ignore",
    strip_newline: bool = False,
) -> Iterator[str]:
    """Yield lines lazily from a text file."""
    file_path = _ensure_path(path)
    with file_path.open("r", encoding=encoding, errors=errors) as stream:
        for line in stream:
            yield line.rstrip("\r\n") if strip_newline else line


def process_in_chunks(
    path: PathLike,
    processor: ChunkProcessor,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> None:
    """Call ``processor`` for every chunk of the file."""
    for chunk in read_chunks(path, chunk_size=chunk_size):
        processor(chunk)


def copy_file_stream(
    source: PathLike,
    destination: PathLike,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mkdirs: bool = True,
) -> Path:
    """Copy ``source`` to ``destination`` using streaming reads."""
    src_path = _ensure_path(source)
    dest_path = _ensure_path(destination)

    if mkdirs:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    with src_path.open("rb") as src_stream, dest_path.open("wb") as dst_stream:
        while True:
            chunk = src_stream.read(chunk_size)
            if not chunk:
                break
            dst_stream.write(chunk)

    return dest_path


__all__ = [
    "DEFAULT_CHUNK_SIZE",
    "copy_file_stream",
    "iter_lines",
    "process_in_chunks",
    "read_chunks",
]
