"""Utilities for producing Windows-safe filesystem paths.

This module focuses on enforcing Windows path constraints, including the
traditional ``MAX_PATH`` limit and the requirement to avoid reserved names
and disallowed characters. All sanitisation functions normalise Unicode text
and emit ASCII-only output to keep downstream tooling predictable.

The helpers are designed for use by the Zeus automation layer when it moves
and organises files inside the Data Lake. They can also be reused by other
pipelines that need deterministic filename munging.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import unicodedata
from contextlib import suppress
from pathlib import Path
from typing import Iterable, Iterator, Optional, Union

# Windows limits – conservative defaults leave a small buffer for future
# suffixes that callers might append.
WINDOWS_MAX_PATH = 260
WINDOWS_MAX_DIRNAME = 248
WINDOWS_MAX_FILENAME = 255

# Characters that Windows refuses in path components.
_WINDOWS_INVALID = set('<>:"/\\|?*')
# Reserved device names (case-insensitive) that cannot be used as standalone
# file or directory names.
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "CLOCK$",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}

# Regular expressions reused by the sanitisation helpers.
_COLLAPSE_RE = re.compile(r"[_\s]+")
_TRAILING_RE = re.compile(r"[._-]+$")


def normalize_unicode(value: str) -> str:
    """Return the NFC-normalised version of ``value``."""

    return unicodedata.normalize("NFC", value)


def ascii_safe(value: str) -> str:
    """Convert ``value`` to ASCII by stripping non-ASCII code points.

    The function uses NFKD decomposition to separate base characters from their
    diacritics, making the ASCII stripping more faithful while remaining free of
    third-party dependencies such as ``unidecode``.
    """

    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def sanitize_filename(
    name: str, max_length: int = WINDOWS_MAX_FILENAME, *, replacement: str = "_"
) -> str:
    """Return a safe filename component.

    The sanitisation pipeline applies the following steps:

    * Unicode NFC normalisation followed by ASCII coercion.
    * Replacement of characters that are illegal on Windows or below ASCII 32.
    * Collapsing consecutive replacements into a single underscore.
    * Stripping leading/trailing separators, dots, and spaces.
    * Avoidance of reserved Windows device names.
    * Length enforcement – truncating with a stable hash suffix when required.
    """

    if not name:
        return "unnamed"

    value = normalize_unicode(name)
    value = ascii_safe(value)
    value = value.strip()

    if not value:
        value = "unnamed"

    sanitized = []
    for char in value:
        if char in _WINDOWS_INVALID or ord(char) < 32:
            sanitized.append(replacement)
        else:
            sanitized.append(char)

    candidate = "".join(sanitized)
    candidate = _COLLAPSE_RE.sub("_", candidate)
    candidate = candidate.strip(" .")

    if not candidate:
        candidate = "unnamed"

    candidate = _ensure_not_reserved(candidate)

    if len(candidate) > max_length:
        candidate = _truncate_component(candidate, max_length)

    return candidate


def sanitize_path(
    path: Union[str, Path],
    *,
    base_dir: Optional[Union[str, Path]] = None,
    max_path_length: int = WINDOWS_MAX_PATH,
    symlink_policy: str = "ignore",
    symlink_max_depth: int = 32,
    resolve_symlinks: bool = False,
) -> Path:
    """Sanitise a path by cleaning each component and enforcing length limits.

    Parameters
    ----------
    path:
        Raw input path to sanitise. Can be relative or absolute.
    base_dir:
        Optional base directory used when evaluating total path length.
    max_path_length:
        Maximum permitted path length; defaults to the Windows ``MAX_PATH``.
    Apply filename rules component-wise and enforce symlink policy if requested.

    Parameters
    ----------
    path:
        Raw input path to sanitise. Can be relative or absolute.
    base_dir:
        Optional base directory used when evaluating total path length.
    max_path_length:
        Maximum permitted path length; defaults to the Windows ``MAX_PATH``.
    symlink_policy:
        Controls behaviour when the original path points at a symlink or junction.
        Accepted values are ``"ignore"`` (default, current behaviour),
        ``"reject"`` (raise :class:`DisallowedSymlinkError`) and ``"follow"``
        (resolve while detecting loops).
    symlink_max_depth:
        Maximum chain length allowed when ``symlink_policy="follow"``.
    resolve_symlinks:
        When ``True`` and ``symlink_policy`` is ``"follow"``, return the resolved
        path instead of the original value. Ignored otherwise.
    """

    path_obj = Path(path)
    is_absolute = path_obj.is_absolute()
    anchor = path_obj.anchor if is_absolute else ""

    policy = symlink_policy.lower()
    if policy not in {"ignore", "reject", "follow"}:
        raise ValueError(
            "symlink_policy must be one of 'ignore', 'reject', or 'follow'",
        )
    if symlink_max_depth < 1:
        raise ValueError("symlink_max_depth must be >= 1")

    if policy != "ignore" and path_obj.exists():
        enforce_symlink_policy(
            path_obj,
            follow_symlinks=(policy == "follow"),
            max_depth=symlink_max_depth,
            resolve=resolve_symlinks,
        )

    # Sanitize individual components while preserving anchor/drive information.
    parts: Iterable[str]
    if is_absolute:
        parts = path_obj.parts[1:]
    else:
        parts = path_obj.parts

    sanitized_parts = [sanitize_filename(part) for part in parts if part]

    sanitized_path = _build_path(anchor, sanitized_parts)

    effective_base = Path(base_dir) if base_dir is not None else None
    target_path = sanitized_path if effective_base is None else effective_base / sanitized_path

    if os.name == "nt":
        # Respect directory-level limit for absolute paths.
        if is_absolute and len(str(sanitized_path.parent)) > WINDOWS_MAX_DIRNAME:
            sanitized_path = _enforce_parent_limit(sanitized_path, WINDOWS_MAX_DIRNAME)
            target_path = (
                sanitized_path if effective_base is None else effective_base / sanitized_path
            )

        if len(str(target_path)) > max_path_length:
            sanitized_path = _enforce_max_path(sanitized_path, effective_base, max_path_length)

    return (
        enforce_symlink_policy(
            sanitized_path,
            follow_symlinks=True,
            max_depth=symlink_max_depth,
            resolve=True,
        )
        if resolve_symlinks and policy == "follow"
        else sanitized_path
    )


class SymlinkPolicyError(RuntimeError):
    """Base exception raised when a symlink/junction policy is violated."""


class DisallowedSymlinkError(SymlinkPolicyError):
    """Raised when a symlink/junction is encountered but the policy forbids it."""


class SymlinkLoopError(SymlinkPolicyError):
    """Raised when a symlink/junction loop is detected while following links."""


def enforce_symlink_policy(
    path: Union[str, Path],
    *,
    follow_symlinks: bool = False,
    max_depth: int = 32,
    resolve: bool = False,
) -> Path:
    """Enforce symlink/junction rules on ``path``.

    Parameters
    ----------
    path:
        Filesystem path to inspect.
    follow_symlinks:
        When ``False`` the function raises :class:`DisallowedSymlinkError` if any
        component is a symlink or junction. When ``True`` the function validates
        that following symlinks does not create loops.
    max_depth:
        Maximum symlink depth to traverse when ``follow_symlinks`` is ``True``.
    resolve:
        When ``True`` return the resolved path (subject to ``follow_symlinks``);
        otherwise the original value is returned.
    """

    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")

    path_obj = Path(path)

    if not follow_symlinks:
        for component in _iter_existing_components(path_obj):
            if _is_symlink_or_junction(component):
                raise DisallowedSymlinkError(f"Symlink or junction not allowed: {component}")
        return path_obj

    resolved_target = _resolve_with_loop_detection(path_obj, max_depth)

    return resolved_target if resolve else path_obj


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_path(anchor: str, parts: Iterable[str]) -> Path:
    if anchor:
        return Path(anchor, *parts)
    return Path(*parts)


def _ensure_not_reserved(name: str) -> str:
    upper = name.split(".")[0].upper()
    if upper in _WINDOWS_RESERVED:
        return f"{name}_"
    return name


def _truncate_component(name: str, max_length: int) -> str:
    if len(name) <= max_length:
        return name

    base, dot, ext = name.partition(".")
    if not dot:  # no extension
        ext = ""
        base = name
    else:
        ext = f".{ext}"

    hash_fragment = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    allowed = max(max_length - len(ext) - len(hash_fragment) - 1, 8)
    trimmed = base[:allowed].rstrip("._-")
    if not trimmed:
        trimmed = "file"
    return f"{trimmed}_{hash_fragment}{ext}"[:max_length]


def _enforce_parent_limit(path: Path, limit: int) -> Path:
    """Ensure parent directory string representation does not exceed ``limit``."""

    if len(str(path.parent)) <= limit:
        return path

    parts = list(path.parts)
    start_idx = 1 if path.is_absolute() else 0
    for idx in range(len(parts) - 1, start_idx - 1, -1):
        if len(str(Path(*parts[: idx + 1]))) <= limit:
            break
        parts[idx] = _truncate_component(parts[idx], WINDOWS_MAX_FILENAME)

    return Path(*parts)


def _enforce_max_path(path: Path, base_dir: Optional[Path], limit: int) -> Path:
    """Shorten components until the combined path is within ``limit`` characters."""

    parts = list(path.parts)
    start_idx = 1 if path.is_absolute() else 0

    def current_length(candidate_parts: Iterable[str]) -> int:
        candidate = Path(*candidate_parts)
        resolved = candidate if base_dir is None else base_dir / candidate
        return len(str(resolved))

    if current_length(parts) <= limit:
        return path

    for idx in range(len(parts) - 1, start_idx - 1, -1):
        parts[idx] = _truncate_component(parts[idx], WINDOWS_MAX_FILENAME)
        if current_length(parts) <= limit:
            return Path(*parts)

    # Last resort: hash the entire path while preserving anchor.
    hashed = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:40]
    if start_idx:
        anchor = parts[0]
        return Path(anchor, hashed)
    return Path(hashed)
