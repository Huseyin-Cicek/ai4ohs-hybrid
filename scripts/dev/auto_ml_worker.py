"""
Zeus ML Worker - Scheduled pipeline execution based on staleness
Responsibilities:
- READ stamps (detect stale pipelines)
- WRITE logs (task execution results)
- WRITE cache (last run timestamp, status summary)
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.config.settings import settings

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))


class MLWorker:
    """Zero-config ML worker for scheduled pipeline execution."""

    def __init__(self):
        self.project_root = Path(__file__).parents[2]
        self.stamp_dir = self.project_root / "logs" / "pipelines"
        self.log_file = self.project_root / "logs" / "dev" / "ml_worker.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Cache files (WRITE responsibility)
        self.last_run_file = self.project_root / "logs" / "dev" / "ml_worker_last_run.txt"
        self.summary_file = self.project_root / "logs" / "dev" / "zeus_ml_summary.json"

        # Pipeline stages and staleness thresholds (hours)
        self.stages = [
            ("00_ingest", settings.ML_WORKER_INTERVAL_HOURS),
            ("01_staging", 12),  # 12 hours
            ("02_processing", 6),  # 6 hours
            ("03_rag", 6),  # 6 hours
        ]

        print("ML Worker initialized")
        print(f"Stamp directory: {self.stamp_dir}")
        print(f"Log file: {self.log_file}")

    def _log(self, event_type: str, message: str):
        """Append event to log (WRITE responsibility)."""
        timestamp = datetime.now().isoformat()
        line = f"[{timestamp}] {event_type}: {message}\n"
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(line)
        print(f"[{event_type}] {message}")

    def _read_stamp(self, stage: str) -> datetime:
        """Read pipeline stamp (READ responsibility)."""
        stamp_file = self.stamp_dir / f"{stage}.stamp"
        if not stamp_file.exists():
            return datetime.fromtimestamp(0)  # Unix epoch = never run

        try:
            timestamp_str = stamp_file.read_text(encoding="utf-8").strip()
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, OSError):
            return datetime.fromtimestamp(0)

    def _is_stale(self, stage: str, threshold_hours: int) -> bool:
        """Check if stage exceeds staleness threshold."""
        last_run = self._read_stamp(stage)
        age = datetime.now() - last_run
        return age > timedelta(hours=threshold_hours)

    def _execute_pipeline(self, stage: str) -> bool:
        """Execute single pipeline stage."""
        self._log("EXECUTE", f"Starting pipeline: {stage}")

        pipeline_script = self.project_root / "src" / "pipelines" / stage / "run.py"

        if not pipeline_script.exists():
            self._log("ERROR", f"Pipeline script not found: {pipeline_script}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(pipeline_script)],
                check=True,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                cwd=str(self.project_root),
            )
            self._log("SUCCESS", f"Completed pipeline: {stage}")
            return True

        except subprocess.TimeoutExpired:
            self._log("ERROR", f"Pipeline timeout: {stage}")
            return False

        except subprocess.CalledProcessError as e:
            self._log("ERROR", f"Pipeline failed: {stage} - {e.stderr[:200]}")
            return False

        except Exception as e:
            self._log("ERROR", f"Unexpected error in pipeline {stage}: {e}")
            return False

    def _update_cache(self, tasks_completed: List[str], tasks_failed: List[str]):
        """Update cache files (WRITE responsibility)."""
        # Update last run timestamp
        self.last_run_file.write_text(datetime.now().isoformat())

        # Update summary JSON (atomic write)
        summary = {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "next_scheduled": (datetime.now() + timedelta(hours=6)).isoformat(),
            "pipeline_status": {
                stage: {
                    "last_run": self._read_stamp(stage).isoformat(),
                    "is_stale": self._is_stale(stage, threshold),
                }
                for stage, threshold in self.stages
            },
        }

        temp_file = self.summary_file.with_suffix(".tmp")
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        temp_file.replace(self.summary_file)

    def run(self):
        """Main worker execution."""
        self._log("INFO", "ML Worker started")

        tasks_completed = []
        tasks_failed = []

        # Check each stage for staleness
        for stage, threshold in self.stages:
            if self._is_stale(stage, threshold):
                last_run = self._read_stamp(stage)
                age = datetime.now() - last_run
                hours = int(age.total_seconds() / 3600)

                self._log(
                    "INFO",
                    f"Stage {stage} is stale (last run: {hours}h ago, threshold: {threshold}h)",
                )

                if self._execute_pipeline(stage):
                    tasks_completed.append(stage)
                else:
                    tasks_failed.append(stage)
            else:
                self._log("INFO", f"Stage {stage} is fresh, skipping")

        # Update cache with results
        self._update_cache(tasks_completed, tasks_failed)

        # Summary log
        if tasks_completed or tasks_failed:
            self._log(
                "SUMMARY",
                f"Completed: {len(tasks_completed)}, Failed: {len(tasks_failed)}",
            )
            if tasks_completed:
                print(f"\n✓ Completed pipelines: {', '.join(tasks_completed)}")
            if tasks_failed:
                print(f"\n✗ Failed pipelines: {', '.join(tasks_failed)}")
        else:
            self._log("SUMMARY", "No stale pipelines detected")
            print("\n✓ All pipelines are fresh, no execution needed")


def main():
    """Main entry point."""
    worker = MLWorker()
    worker.run()


if __name__ == "__main__":
    main()
