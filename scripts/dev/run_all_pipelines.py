#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run all pipeline stages sequentially."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------
# Path / import setup
# ---------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.pipeline_order import PIPELINE_STAGES, PROJECT_ROOT, PipelineStage  # type: ignore


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all AI4OHS pipeline stages.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution and report planned outputs without writing files.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _make_logger(dry_run: bool):
    if dry_run:

        def _log(message: str) -> None:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Use ASCII-safe output for Windows console
            safe_message = message.encode("ascii", errors="replace").decode("ascii")
            print(f"[{ts}] {safe_message}")

        return _log

    log_dir = PROJECT_ROOT / "logs" / "pipelines"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "run_all.log"

    def _log(message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        # Use ASCII-safe output for Windows console
        safe_line = line.encode("ascii", errors="replace").decode("ascii")
        print(safe_line)
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    return _log


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------
# Command builder: decide whether to call via "-m src...." or as script
# ---------------------------------------------------------------------
def _build_command(script_path: Path) -> list[str]:
    """
    Build the subprocess command for a given stage script.

    - If script is under PROJECT_ROOT/src and is a .py file:
        python -m src.pipelines.00_ingest.run
      so that "import src.xxx" works correctly.
    - Otherwise:
        python <absolute_script_path>
    """
    script = script_path.resolve()
    try:
        rel = script.relative_to(PROJECT_ROOT)
    except ValueError:
        # Outside project root: fall back to plain script execution
        return [sys.executable, str(script)]

    if rel.suffix == ".py" and rel.parts and rel.parts[0] == "src":
        # e.g. src/pipelines/00_ingest/run.py -> "src.pipelines.00_ingest.run"
        module = ".".join(rel.with_suffix("").parts)
        return [sys.executable, "-m", module]

    # Default: run as script
    return [sys.executable, str(script)]


def _plan_pipeline(log, stages: Iterable[PipelineStage]) -> int:
    log("=" * 60)
    log("🏗 AI4OHS-HYBRID — Full Pipeline Run DRY-RUN")
    for stage in stages:
        cmd = _build_command(stage.script)
        log(f"[PLAN] Stage {stage.name}")
        log(f"       Would execute: {' '.join(cmd)}")
        log(f"       Would update: {_relative(stage.stamp_path)}")
    log(f"🏁 Planned {len(PIPELINE_STAGES)}/{len(PIPELINE_STAGES)} stages (no execution).")
    log("=" * 60)
    return 0


def _execute_pipeline(log, stages: Iterable[PipelineStage]) -> int:
    log("=" * 60)
    log("🚀 AI4OHS-HYBRID — Full Pipeline Run START")
    completed = 0
    exit_code = 0

    for stage in stages:
        cmd = _build_command(stage.script)
        log(f"▶ Starting stage: {stage.name} ({_relative(stage.script)})")
        log(f"   Command      : {' '.join(cmd)}")
        t0 = time.time()
        try:
            # Always run from PROJECT_ROOT so that src/ is importable as a package
            subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
            elapsed = round(time.time() - t0, 2)
            log(f"✅ Completed {stage.name} in {elapsed}s")
            completed += 1
        except subprocess.CalledProcessError as exc:
            exit_code = exc.returncode or 1
            log(f"❌ ERROR in {stage.name}: {exc}")
            log("⚠️ Skipping remaining stages due to error.")
            break

    log(f"🏁 Finished {completed}/{len(PIPELINE_STAGES)} stages")
    log("=" * 60)
    return exit_code


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    log = _make_logger(args.dry_run)

    if args.dry_run:
        return _plan_pipeline(log, PIPELINE_STAGES)

    return _execute_pipeline(log, PIPELINE_STAGES)


if __name__ == "__main__":
    raise SystemExit(main())
