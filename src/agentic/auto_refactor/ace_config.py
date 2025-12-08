import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ACEConfig:
    """
    ACEConfig – Unified configuration loader for ACE/FERS/LLM subsystems.
    Supports:
    - settings.yaml auto-sync
    - global_profile (FAST_SAFE, BALANCED, DEEP)
    - CLI override via --profile (in run_ace_pipeline.py)
    """

    DEFAULT_SETTINGS_PATH = ".\\config\\settings.yaml"

    def __init__(self, project_root: str, profile_override: Optional[str] = None):
        self.project_root = Path(project_root)
        self.settings_file = self.project_root / self.DEFAULT_SETTINGS_PATH

        if not self.settings_file.exists():
            raise FileNotFoundError(f"settings.yaml bulunamadı: {self.settings_file}")

        self.raw: Dict[str, Any] = {}
        self.last_loaded_timestamp = 0

        # Load settings.yaml (first read)
        self.load()

        # Apply profile logic (global_profile or profile_override)
        self.apply_profile(profile_override)

        # Optional: validate schema
        self.validate_schema()

    # ------------------------------------------------------------------
    # YAML Loader + Auto-Sync
    # ------------------------------------------------------------------
    def load(self):
        """Load settings.yaml into ACEConfig.raw"""
        with open(self.settings_file, "r", encoding="utf-8") as f:
            self.raw = yaml.safe_load(f) or {}

        self.last_loaded_timestamp = time.time()
        print(f"[ACEConfig] settings.yaml loaded at {self.last_loaded_timestamp}")

    def auto_sync(self):
        """
        Automatically reload settings.yaml when modified.
        ACEExecutor will call this periodically.
        """
        try:
            mtime = self.settings_file.stat().st_mtime
            if mtime > self.last_loaded_timestamp:
                print("[ACEConfig] settings.yaml changed → reloading…")
                self.load()
                self.apply_profile()
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    # Profile Resolution
    # ------------------------------------------------------------------
    def apply_profile(self, profile_override: Optional[str] = None):
        """
        Resolve profile selection in order of precedence:

        1) CLI override (highest priority)
        2) settings.yaml → fers_profile
        3) settings.yaml → global_profile (fallback)
        4) BALANCED default
        """

        # Highest priority: CLI override
        if profile_override:
            print(f"[ACEConfig] CLI override profile: {profile_override}")
            self.raw["fers_profile"] = profile_override.upper()

        # Determine chosen profile
        selected = self.raw.get("fers_profile") or self.raw.get("global_profile") or "BALANCED"

        selected = selected.upper()

        # Get profile block
        profiles = self.raw.get("profiles", {})
        profile_block = profiles.get(selected, {})

        # Ensure ACE & FERS nodes exist
        self.raw.setdefault("ace", {})
        self.raw.setdefault("fers", {})

        # Merge ACE parameters
        if "ace" in profile_block:
            self.raw["ace"].update(profile_block["ace"])

        # Merge FERS parameters
        if "fers" in profile_block:
            self.raw["fers"].update(profile_block["fers"])

        print(f"[ACEConfig] Using merged profile: {selected}")

    # ------------------------------------------------------------------
    # Retrieve ACE or FERS blocks
    # ------------------------------------------------------------------
    def get_ace_block(self) -> Dict[str, Any]:
        return self.raw.get("ace", {})

    def get_fers_block(self) -> Dict[str, Any]:
        return self.raw.get("fers", {})

    # ------------------------------------------------------------------
    # settings.yaml schema validator
    # ------------------------------------------------------------------
    def validate_schema(self):
        """
        Basic validation to catch malformed config.
        Not strict; only protects against common errors.
        """
        if "profiles" not in self.raw:
            print("[ACEConfig][WARN] profiles block missing in settings.yaml")

        if "fers" not in self.raw:
            print("[ACEConfig][WARN] fers block missing in settings.yaml")

        if "ace" not in self.raw:
            print("[ACEConfig][WARN] ace block missing in settings.yaml")

        if "global_profile" in self.raw:
            if self.raw["global_profile"] not in ["FAST_SAFE", "BALANCED", "DEEP"]:
                print(f"[ACEConfig][ERROR] Invalid global_profile: {self.raw['global_profile']}")
