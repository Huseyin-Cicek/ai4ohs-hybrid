"""
Centralized settings for AI4OHS-HYBRID project.

- Uses Pydantic v2 + pydantic-settings with .env support
- Loads feature flags from a YAML file (features.yaml) when present
- Provides typed, overrideable defaults for file system, pipelines, and workers
"""

from __future__ import annotations

import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Callable, Dict, Final, List

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------
# Global constants & project root
# ---------------------------------------------------------------------

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
ENV_PATH: Final[Path] = PROJECT_ROOT / ".env"
FEATURES_DEFAULT_PATH: Final[Path] = Path(__file__).resolve().with_name("features.yaml")
DEFAULT_RANDOM_SEED: Final[int] = 42
MONOTONIC_CLOCK: Final[Callable[[], float]] = time.monotonic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Determinism / randomness hygiene
# ---------------------------------------------------------------------

os.environ.setdefault("PYTHONHASHSEED", "0")
random.seed(DEFAULT_RANDOM_SEED)

# ---------------------------------------------------------------------
# Feature flag helpers
# ---------------------------------------------------------------------


def _read_feature_flags(path: Path) -> Dict[str, Any]:
    """Load feature flags from the provided YAML file path."""
    try:
        if not path.exists():
            logger.debug("Feature flag file not found at %s; returning empty map", path)
            return {}

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        if not isinstance(data, dict):
            logger.warning("Feature flag file %s must contain a mapping at the root", path)
            return {}

        return data
    except (OSError, yaml.YAMLError) as exc:
        logger.error("Failed to load feature flags from %s: %s", path, exc)
        return {}


# ---------------------------------------------------------------------
# Settings model (Pydantic v2 + pydantic-settings)
# ---------------------------------------------------------------------


class Settings(BaseSettings):
    """Application settings with sensible defaults and .env overrides."""

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Paths (as Path, but env can provide strings)
    RAW_ROOT: Path = Path(r"H:/DataLake/ai4hsse-raw")
    CLEAN_ROOT: Path = Path(r"H:/DataWarehouse/ai4hsse-clean")
    LOG_ROOT: Path = PROJECT_ROOT / "logs"

    # Environment / runtime mode
    OFFLINE_MODE: bool = True
    GPU_ACCELERATION: bool = True

    # Pipeline execution settings
    PIPELINE_RUN_TIMEOUT: int = 3600  # seconds
    PIPELINE_RUN_MAX_RETRIES: int = 2
    PIPELINE_RUN_BACKOFF: int = 5  # seconds

    # File processing limits
    FILE_STABLE_SECONDS: int = 2
    MAX_FILE_SIZE_MB: int = 100
    MAX_FOLDER_SIZE_MB: int = 500
    HASH_CHUNK_BYTES: int = 1_048_576  # 1 MB

    # Voice listener settings
    VOICE_CMD_CONFIDENCE: float = 0.8
    WAKE_DEBOUNCE_S: float = 1.0

    # ML Worker / health polling
    ML_WORKER_INTERVAL_HOURS: int = 6
    HEALTH_POLL_SECONDS: int = 30

    # Embedding and Reranking models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L12-v2"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # API server (local service) configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Allowed file extensions and MIME types
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".txt",
        ".csv",
        ".pptx",
        ".ppt",
        ".md",
        ".msg",
        ".eml",
    ]

    ALLOWED_MIME_PREFIXES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument",
        "application/msword",
        "image/",
        "text/",
    ]

    # Feature flag configuration
    FEATURES_FILE: str = str(FEATURES_DEFAULT_PATH)
    feature_flags: Dict[str, Any] = {}

    # -----------------------------------------------------------------
    # Validators / helpers (Pydantic v2 style)
    # -----------------------------------------------------------------

    @field_validator("feature_flags", mode="before")
    @classmethod
    def _load_feature_flags(
        cls,
        value: Dict[str, Any] | None,
        info,
    ) -> Dict[str, Any]:
        """Populate feature flags from YAML if not explicitly provided."""
        if value:
            return value

        # Access other fields via info.data
        features_file = info.data.get("FEATURES_FILE") or str(FEATURES_DEFAULT_PATH)
        features_path = Path(features_file).expanduser()
        return _read_feature_flags(features_path)

    def get_feature_flag(self, *path: str, default: Any = None) -> Any:
        """Retrieve a nested feature flag by path, returning ``default`` when absent."""
        cursor: Any = self.feature_flags
        for key in path:
            if isinstance(cursor, dict) and key in cursor:
                cursor = cursor[key]
            else:
                return default
        return cursor

    def reload_feature_flags(self) -> Dict[str, Any]:
        """Reload feature flags from disk and update the settings instance."""
        flags = _read_feature_flags(Path(self.FEATURES_FILE).expanduser())
        object.__setattr__(self, "feature_flags", flags)
        return flags


# Global settings instance
settings = Settings()
