"""Rulepack manifest validation utilities.

This module validates the offline compliance rulepack before it is used.
It ensures that the rule definitions tracked in :mod:`src.utils.compliance`
match the signed manifest located in ``src/cag/rules/manifest.json``.
The validation is intentionally deterministic and strictly offline.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional

__all__ = [
    "RulepackIntegrityError",
    "RulepackFile",
    "RulepackManifest",
    "validate_ruleset",
    "get_validated_manifest",
    "get_ruleset_version",
]


class RulepackIntegrityError(RuntimeError):
    """Raised when the rulepack manifest or files fail validation."""


@dataclass(frozen=True)
class RulepackFile:
    """A single rule file entry declared in the manifest."""

    path: Path
    sha256: str


@dataclass(frozen=True)
class RulepackManifest:
    """The validated rulepack manifest representation."""

    ruleset_version: str
    files: List[RulepackFile]
    ruleset_sha256: str


_MANIFEST_PATH = Path(__file__).resolve().parent / "rules" / "manifest.json"
# This value is replaced during the build/update process and must match the
# canonical hash of the manifest payload (excluding the ``ruleset_sha256``
# field itself). It acts as a tamper-evident seal for the rulepack.
_EXPECTED_RULESET_SHA256 = "d2a1a1cb0662d40bdb40379bc1b5071e8b66c5bded599ab5c34dba02184e3d06"


def _project_root() -> Path:
    """Return the repository root (two levels above ``src/cag``)."""

    return Path(__file__).resolve().parents[2]


def _canonical_manifest_payload(manifest_dict: Dict[str, object]) -> bytes:
    """Return the canonical JSON payload used for hashing the manifest."""

    rules_iter: Iterable[Dict[str, str]] = (
        {
            "path": entry["path"],
            "sha256": entry["sha256"],
        }
        for entry in sorted(
            manifest_dict.get("rules", []),
            key=lambda item: item["path"],
        )
    )

    payload = {
        "ruleset_version": manifest_dict["ruleset_version"],
        "rules": list(rules_iter),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _compute_manifest_digest(manifest_dict: Dict[str, object]) -> str:
    """Compute the SHA-256 digest of the canonical manifest payload."""

    return hashlib.sha256(_canonical_manifest_payload(manifest_dict)).hexdigest()


def _compute_file_sha256(file_path: Path) -> str:
    """Compute the SHA-256 digest of a file."""

    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_manifest_schema(manifest: Dict[str, object]) -> None:
    """Validate the JSON structure of the manifest."""

    if "ruleset_version" not in manifest or not isinstance(manifest["ruleset_version"], str):
        raise RulepackIntegrityError("Manifest is missing a valid 'ruleset_version' field")

    if "rules" not in manifest or not isinstance(manifest["rules"], list) or not manifest["rules"]:
        raise RulepackIntegrityError("Manifest must declare at least one rule file in 'rules'")

    for entry in manifest["rules"]:
        if not isinstance(entry, dict):
            raise RulepackIntegrityError("Manifest rule entries must be objects")
        if "path" not in entry or "sha256" not in entry:
            raise RulepackIntegrityError("Each manifest entry requires 'path' and 'sha256'")
        if not isinstance(entry["path"], str) or not entry["path"]:
            raise RulepackIntegrityError("Manifest entry 'path' must be a non-empty string")
        if not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64:
            raise RulepackIntegrityError(
                "Manifest entry 'sha256' must be a 64-character hex digest"
            )

    if "ruleset_sha256" not in manifest or not isinstance(manifest["ruleset_sha256"], str):
        raise RulepackIntegrityError("Manifest is missing 'ruleset_sha256' field")


def validate_ruleset(
    manifest_path: Optional[Path] = None,
    *,
    expected_ruleset_sha256: Optional[str] = _EXPECTED_RULESET_SHA256,
) -> RulepackManifest:
    """Validate the rulepack manifest and associated files.

    Args:
        manifest_path: Optional override for the manifest location. Defaults to
            the bundled manifest under ``src/cag/rules``.
        expected_ruleset_sha256: Optional expected digest for the canonical
            manifest payload. When provided (default), the computed digest must
            match this value to prevent tampering.

    Returns:
        A :class:`RulepackManifest` object describing the validated rulepack.

    Raises:
        RulepackIntegrityError: If any validation step fails.
    """

    manifest_path = manifest_path or _MANIFEST_PATH

    if not manifest_path.exists():
        raise RulepackIntegrityError(f"Manifest file not found: {manifest_path}")

    try:
        manifest_dict: Dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RulepackIntegrityError(f"Manifest is not valid JSON: {exc}") from exc

    _validate_manifest_schema(manifest_dict)

    computed_manifest_hash = _compute_manifest_digest(manifest_dict)
    declared_manifest_hash = manifest_dict["ruleset_sha256"]

    if declared_manifest_hash != computed_manifest_hash:
        raise RulepackIntegrityError(
            "Manifest signature mismatch: embedded 'ruleset_sha256' does not match contents"
        )

    if expected_ruleset_sha256 and declared_manifest_hash != expected_ruleset_sha256:
        raise RulepackIntegrityError(
            "Manifest signature does not match the trusted ruleset signature"
        )

    project_root = _project_root()
    rule_files: List[RulepackFile] = []

    for entry in manifest_dict["rules"]:
        relative_path = Path(entry["path"])
        target_path = (project_root / relative_path).resolve()

        try:
            relative_path = target_path.relative_to(project_root)
        except ValueError as exc:
            raise RulepackIntegrityError(
                f"Manifest path escapes project root: {entry['path']}"
            ) from exc

        if not target_path.exists():
            raise RulepackIntegrityError(f"Manifest references missing file: {relative_path}")

        actual_hash = _compute_file_sha256(target_path)
        expected_hash = entry["sha256"]

        if actual_hash != expected_hash:
            raise RulepackIntegrityError(
                f"Hash mismatch for {relative_path}: expected {expected_hash}, got {actual_hash}"
            )

        rule_files.append(RulepackFile(path=relative_path, sha256=actual_hash))

    return RulepackManifest(
        ruleset_version=manifest_dict["ruleset_version"],
        files=rule_files,
        ruleset_sha256=declared_manifest_hash,
    )


@lru_cache(maxsize=1)
def get_validated_manifest() -> RulepackManifest:
    """Cache and return the validated manifest."""

    return validate_ruleset()


def get_ruleset_version() -> str:
    """Return the validated ruleset version string."""

    return get_validated_manifest().ruleset_version
