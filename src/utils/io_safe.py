"""BOM-aware text I/O helpers with surrogateescape tolerance."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

PathLike = Union[str, Path]

UTF8_BOM = b"\xef\xbb\xbf"


def _ensure_path(path: PathLike) -> Path:
    """Return ``path`` as a :class:`Path` instance."""
    return path if isinstance(path, Path) else Path(path)


def _is_utf8(encoding: str) -> bool:
    """Return ``True`` when ``encoding`` resolves to UTF-8."""
    normalized = encoding.replace("_", "-").lower()
    return normalized in {"utf-8", "utf8", "utf-8-sig"}


def detect_utf8_bom(path: PathLike) -> bool:
    """Check whether ``path`` starts with a UTF-8 BOM."""
    file_path = _ensure_path(path)
    if not file_path.exists() or not file_path.is_file():
        return False

    try:
        with file_path.open("rb") as stream:
            start = stream.read(len(UTF8_BOM))
    except OSError:
        return False

    return start.startswith(UTF8_BOM)


def read_text_with_bom(
    path: PathLike,
    *,
    encoding: str = "utf-8",
    errors: str = "surrogateescape",
    strip_bom: bool = True,
) -> Tuple[str, bool]:
    """Read text while reporting if a UTF-8 BOM was present."""
    file_path = _ensure_path(path)
    data = file_path.read_bytes()

    had_bom = False
    if _is_utf8(encoding) and data.startswith(UTF8_BOM):
        had_bom = True
        if strip_bom:
            data = data[len(UTF8_BOM) :]

    text = data.decode(encoding, errors=errors)
    return text, had_bom


def read_text_safe(
    path: PathLike,
    *,
    encoding: str = "utf-8",
    errors: str = "surrogateescape",
    strip_bom: bool = True,
) -> str:
    """Read text with surrogateescape tolerance and optional BOM stripping."""
    text, _ = read_text_with_bom(
        path,
        encoding=encoding,
        errors=errors,
        strip_bom=strip_bom,
    )
    return text


def write_text_safe(
    path: PathLike,
    text: str,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    newline: Optional[str] = None,
    bom: Optional[bool] = None,
    preserve_bom: bool = True,
    mkdirs: bool = True,
) -> Path:
    """Write ``text`` while optionally preserving or forcing a UTF-8 BOM."""
    file_path = _ensure_path(path)

    if mkdirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    add_bom = False
    if _is_utf8(encoding):
        if bom is not None:
            add_bom = bom
        elif preserve_bom and file_path.exists():
            _, had_bom = read_text_with_bom(
                file_path,
                encoding=encoding,
                errors=errors,
                strip_bom=False,
            )
            add_bom = had_bom

    effective_encoding = "utf-8-sig" if add_bom and _is_utf8(encoding) else encoding

    with file_path.open(
        "w",
        encoding=effective_encoding,
        errors=errors,
        newline=newline,
    ) as stream:
        stream.write(text)

    return file_path


__all__ = [
    "UTF8_BOM",
    "detect_utf8_bom",
    "read_text_safe",
    "read_text_with_bom",
    "write_text_safe",
]
