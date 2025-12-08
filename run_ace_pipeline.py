import argparse
import sys
from pathlib import Path

from src.agentic.auto_refactor.ace_executor import ACEConfig, ACEExecutor


# --------------------------------------------------------------------
# CLI argument parser with --profile switch
# --------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="AI4OHS-HYBRID — Autonomous ACE/FERS Refactor Pipeline"
    )

    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        choices=["fast", "balanced", "deep"],
        help="Override FERS/ACE refactor profile: fast, balanced, deep",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without applying patches to production repo",
    )

    return parser.parse_args()


# --------------------------------------------------------------------
# Map CLI profile names → settings.yaml profile identifiers
# --------------------------------------------------------------------
PROFILE_MAP = {
    "fast": "FAST_SAFE",
    "balanced": "BALANCED",
    "deep": "DEEP",
}


# --------------------------------------------------------------------
# Load and optionally override ACEConfig
# --------------------------------------------------------------------
def load_config(project_root: Path, profile_override: str | None) -> ACEConfig:
    config = ACEConfig(project_root=str(project_root))

    if profile_override:
        mapped = PROFILE_MAP.get(profile_override.lower())
        if mapped:
            print(f"[CLI] Overriding FERS profile → {mapped}")
            config.raw["fers_profile"] = mapped
        else:
            print(f"[CLI] Invalid profile override ignored: {profile_override}")

    return config


# --------------------------------------------------------------------
# MAIN EXECUTION PIPELINE
# --------------------------------------------------------------------
def main():
    args = parse_args()

    project_root = Path(__file__).resolve().parent

    # Load config with optional CLI override
    config = load_config(project_root, args.profile)

    # Initialize executor
    ace = ACEExecutor(project_root=str(project_root), config=config)

    print("\n=== AI4OHS-HYBRID — ACE PIPELINE ===")
    print("Full autonomous code-refactor pipeline başlatılıyor...\n")
    print(f"ACE MODE: FULL AUTONOMY AKTİF")
    print(f"Using profile: {config.raw.get('fers_profile')}")
    print(f"Dry-run mode: {args.dry_run}")
    print("---------------------------------------\n")

    # Execute pipeline
    result = ace.run_full_refactor_cycle(dry_run=args.dry_run)

    print("\n=== PIPELINE SONUCU ===")
    print(result)
    print("=======================")

    if result.get("status") == "FAIL_TESTS":
        print("\n>>> Patch uygulanamadı. Test hataları mevcut.")
    elif result.get("status") == "APPLIED":
        print("\n>>> Patch başarıyla uygulandı.")
    elif result.get("status") == "NO_CHANGES":
        print("\n>>> Değişiklik üretilmedi.")
    else:
        print("\n>>> Pipeline tamamlandı.")


if __name__ == "__main__":
    main()
