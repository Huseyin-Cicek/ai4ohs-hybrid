"""
Unified CLI entrypoint for ops/maintenance tasks.

Komutlar:
  - zeus-runtime / zeus-recovery
  - health-check
  - sanitize-workspace
  - refactor-prompts
  - autonomy-cycle
  - pipelines-ingest / pipelines-rag
  - ml-worker
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import ops_dispatcher  # noqa: E402


def run_ml_worker():
    script = PROJECT_ROOT / "scripts" / "dev" / "ml_worker.py"
    subprocess.check_call([sys.executable, str(script)])


def run_pipeline(stage: str):
    script = PROJECT_ROOT / "src" / "pipelines" / stage / "run.py"
    subprocess.check_call([sys.executable, str(script)], cwd=PROJECT_ROOT)


def run_autonomy():
    script = PROJECT_ROOT / "scripts" / "run_autonomy_cycle.py"
    subprocess.check_call([sys.executable, str(script)])


def main():
    parser = argparse.ArgumentParser(description="AI4OHS ops CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("zeus-runtime")
    sub.add_parser("zeus-recovery")
    sub.add_parser("health-check")
    sub.add_parser("sanitize-workspace")
    sub.add_parser("refactor-prompts")
    sub.add_parser("autonomy-cycle")
    sub.add_parser("pipelines-ingest")
    sub.add_parser("pipelines-rag")
    sub.add_parser("ml-worker")

    args = parser.parse_args()

    if args.cmd == "zeus-runtime":
        ops_dispatcher.run_zeus_runtime()
    elif args.cmd == "zeus-recovery":
        ops_dispatcher.run_zeus_recovery()
    elif args.cmd == "health-check":
        ops_dispatcher.run_health_check()
    elif args.cmd == "sanitize-workspace":
        ops_dispatcher.run_workspace_sanitizer()
    elif args.cmd == "refactor-prompts":
        ops_dispatcher.run_refactor_prompt_templates()
    elif args.cmd == "autonomy-cycle":
        run_autonomy()
    elif args.cmd == "pipelines-ingest":
        run_pipeline("00_ingest")
    elif args.cmd == "pipelines-rag":
        run_pipeline("03_rag")
    elif args.cmd == "ml-worker":
        run_ml_worker()
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()
