"""Filesystem-backed cache with version and content hash invalidation."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class CacheMetadata:
    """Metadata stored alongside cache payload."""

    cache_version: str
    content_hash: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheMetadata":
        return cls(
            cache_version=str(data["cache_version"]),
            content_hash=str(data["content_hash"]),
            created_at=str(data["created_at"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CacheManager:
    """Manage cached payloads with automatic invalidation."""

    def __init__(self, root: Path, cache_version: str) -> None:
        self._root = root
        self._cache_version = cache_version
        self._root.mkdir(parents=True, exist_ok=True)

    def load(
        self,
        name: str,
        *,
        decoder: Optional[Callable[[bytes], Any]] = None,
        default: Any = None,
    ) -> Any:
        payload_path = self._payload_path(name)
        metadata = self._read_metadata(name)
        if metadata is None:
            return default

        payload = self._read_bytes(payload_path)
        if payload is None:
            self.delete(name)
            return default

        if metadata.cache_version != self._cache_version:
            self.delete(name)
            return default

        if self._calculate_hash(payload) != metadata.content_hash:
            self.delete(name)
            return default

        decoder_fn = decoder or self._default_decoder
        try:
            return decoder_fn(payload)
        except Exception:
            self.delete(name)
            return default

    def save(
        self,
        name: str,
        data: Any,
        *,
        encoder: Optional[Callable[[Any], bytes]] = None,
    ) -> CacheMetadata:
        payload_path = self._payload_path(name)
        serialized = self._serialize(data, encoder)
        metadata = CacheMetadata(
            cache_version=self._cache_version,
            content_hash=self._calculate_hash(serialized),
            created_at=datetime.utcnow().isoformat(),
        )

        self._write_bytes_atomic(payload_path, serialized)
        self._write_text_atomic(self._metadata_path(name), json.dumps(metadata.to_dict(), ensure_ascii=False))
        return metadata

    def delete(self, name: str) -> None:
        payload_path = self._payload_path(name)
        metadata_path = self._metadata_path(name)
        self._remove_file(payload_path)
        self._remove_file(metadata_path)

    def clear(self) -> None:
        for path in self._root.glob("*.cache"):
            self._remove_file(path)
        for path in self._root.glob("*.cache.meta"):
            self._remove_file(path)

    def _payload_path(self, name: str) -> Path:
        return self._root / f"{name}.cache"

    def _metadata_path(self, name: str) -> Path:
        return self._root / f"{name}.cache.meta"

    def _serialize(self, data: Any, encoder: Optional[Callable[[Any], bytes]]) -> bytes:
        if encoder:
            result = encoder(data)
            if not isinstance(result, bytes):
                raise TypeError("Custom encoder must return bytes")
            return result

        try:
            return json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise TypeError("Default serializer requires JSON serializable data") from exc

    def _default_decoder(self, payload: bytes) -> Any:
        return json.loads(payload.decode("utf-8"))

    def _read_metadata(self, name: str) -> Optional[CacheMetadata]:
        metadata_path = self._metadata_path(name)
        raw = self._read_bytes(metadata_path)
        if raw is None:
            return None

        try:
            return CacheMetadata.from_dict(json.loads(raw.decode("utf-8")))
        except (ValueError, KeyError, TypeError):
            self.delete(name)
            return None

    def _read_bytes(self, path: Path) -> Optional[bytes]:
        try:
            return path.read_bytes()
        except OSError:
            return None

    def _write_bytes_atomic(self, path: Path, data: bytes) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_bytes(data)
        temp_path.replace(path)

    def _write_text_atomic(self, path: Path, content: str) -> None:
        self._write_bytes_atomic(path, content.encode("utf-8"))

    def _remove_file(self, path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            return
        except OSError:
            return

    def _calculate_hash(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()
```
