"""Chunked file streaming utilities for large file operations.

These helpers complement the BOM-aware text I/O helpers in ``io_safe`` by
providing streaming read/write patterns that minimise memory usage while
respecting UTF-8 BOM preservation and ``surrogateescape`` error handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator, Optional, Union

from .io_safe import UTF8_BOM, detect_utf8_bom

PathLike = Union[str, Path]
DEFAULT_CHUNK_SIZE = 1024 * 1024


def _ensure_path(path: PathLike) -> Path:
    """Return ``path`` as a :class:`Path` instance."""
    return path if isinstance(path, Path) else Path(path)


def _is_utf8(encoding: str) -> bool:
    """Return ``True`` when ``encoding`` resolves to UTF-8."""
    normalized = encoding.replace("_", "-").lower()
    return normalized in {"utf-8", "utf8", "utf-8-sig"}


def stream_bytes(path: PathLike, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
    """Yield chunks of bytes from ``path`` without loading the whole file."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    file_path = _ensure_path(path)
    with file_path.open("rb") as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk


def stream_text(
    path: PathLike,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    encoding: str = "utf-8",
    errors: str = "surrogateescape",
    strip_bom: bool = True,
) -> Iterator[str]:
    """Yield decoded text chunks from ``path`` with BOM and error handling."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    file_path = _ensure_path(path)
    with file_path.open("rb") as stream:
        bom_processed = False
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break

            if not bom_processed and _is_utf8(encoding) and chunk.startswith(UTF8_BOM):
                bom_processed = True
                if strip_bom:
                    chunk = chunk[len(UTF8_BOM) :]
                # When the BOM consumes the whole chunk, read the next block
                if not chunk:
                    continue
            else:
                bom_processed = True

            yield chunk.decode(encoding, errors=errors)


def write_bytes_stream(
    path: PathLike,
    chunks: Iterable[Union[bytes, bytearray, memoryview]],
    *,
    mkdirs: bool = True,
) -> Path:
    """Write ``chunks`` of bytes to ``path`` in a streaming manner."""
    file_path = _ensure_path(path)
    if mkdirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("wb") as stream:
        for chunk in chunks:
            if isinstance(chunk, memoryview):
                stream.write(chunk.tobytes())
            else:
                stream.write(bytes(chunk))

    return file_path


def write_text_stream(
    path: PathLike,
    chunks: Iterable[str],
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    newline: Optional[str] = None,
    bom: Optional[bool] = None,
    preserve_bom: bool = True,
    mkdirs: bool = True,
) -> Path:
    """Write text ``chunks`` to ``path`` while handling UTF-8 BOM preservation."""
    file_path = _ensure_path(path)
    if mkdirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    add_bom = False
    if _is_utf8(encoding):
        if bom is not None:
            add_bom = bom
        elif preserve_bom and file_path.exists():
            add_bom = detect_utf8_bom(file_path)

    with file_path.open("wb") as stream:
        if add_bom:
            stream.write(UTF8_BOM)

        for chunk in chunks:
            data = chunk
            if newline is not None:
                data = data.replace("\n", newline)
            stream.write(data.encode(encoding, errors=errors))

    return file_path


def copy_file_stream(
    src: PathLike,
    dest: PathLike,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    mkdirs: bool = True,
) -> Path:
    """Copy ``src`` to ``dest`` using chunked streaming."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    dest_path = _ensure_path(dest)
    if mkdirs:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    with _ensure_path(src).open("rb") as reader, dest_path.open("wb") as writer:
        while True:
            chunk = reader.read(chunk_size)
            if not chunk:
                break
            writer.write(chunk)

    return dest_path


__all__ = [
    "DEFAULT_CHUNK_SIZE",
    "copy_file_stream",
    "stream_bytes",
    "stream_text",
    "write_bytes_stream",
    "write_text_stream",
]
