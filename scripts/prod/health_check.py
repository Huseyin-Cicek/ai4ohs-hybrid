"""
Production health check for all Zeus components
Validates system health, component status, and generates comprehensive reports
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))


class HealthChecker:
    """Comprehensive health checker for Zeus system."""

    def __init__(self):
        self.project_root = Path(__file__).parents[2]
        self.stamp_dir = self.project_root / "logs" / "pipelines"
        self.log_dir = self.project_root / "logs" / "dev"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "components": {},
            "pipelines": {},
            "system": {},
        }

    def check_process_running(self, process_name: str) -> bool:
        """Check if process is running (cross-platform)."""
        try:
            # Windows
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Check if script name in command line (approximate)
            return process_name in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def parse_log_file(self, log_file: Path, hours: int = 24) -> Dict:
        """Parse log file and extract metrics."""
        if not log_file.exists():
            return {"last_entry": None, "last_time": None, "total_count": 0, "error_count": 0}

        cutoff = datetime.now().timestamp() - (hours * 3600)
        entries = []
        error_count = 0

        try:
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # Extract timestamp
                        ts_str = line.split("]")[0].strip("[")
                        ts = datetime.fromisoformat(ts_str)

                        if ts.timestamp() >= cutoff:
                            entries.append((ts, line.rstrip()))

                            # Count errors
                            if "ERROR" in line or "CRITICAL" in line:
                                error_count += 1

                    except (ValueError, IndexError):
                        continue

        except OSError:
            pass

        if entries:
            last_time, last_entry = entries[-1]
            return {
                "last_entry": last_entry,
                "last_time": last_time.isoformat(),
                "total_count": len(entries),
                "error_count": error_count,
            }

        return {"last_entry": None, "last_time": None, "total_count": 0, "error_count": 0}

    def check_component_health(self, component_name: str, script_name: str) -> Dict:
        """Check health of Zeus component."""
        log_file = self.log_dir / f"{component_name.lower().replace(' ', '_')}.log"

        # Parse log
        log_data = self.parse_log_file(log_file, hours=24)

        # Determine status
        running = self.check_process_running(script_name)

        if running:
            if log_data["error_count"] > 10:
                status = "degraded"
            else:
                status = "healthy"
        else:
            if log_data["last_time"]:
                last_time = datetime.fromisoformat(log_data["last_time"])
                age_hours = (datetime.now() - last_time).total_seconds() / 3600
                status = "down" if age_hours > 1 else "stopped"
            else:
                status = "never_run"

        return {
            "name": component_name,
            "running": running,
            "status": status,
            "last_log_entry": log_data["last_entry"],
            "last_log_time": log_data["last_time"],
            "log_entries_24h": log_data["total_count"],
            "error_count_24h": log_data["error_count"],
        }

    def check_pipeline_health(self, stage_name: str, threshold_hours: int) -> Dict:
        """Check health of pipeline stage."""
        stamp_file = self.stamp_dir / f"{stage_name}.stamp"

        if stamp_file.exists():
            try:
                ts_str = stamp_file.read_text(encoding="utf-8").strip()
                last_run = datetime.fromisoformat(ts_str)
                age = datetime.now() - last_run
                age_hours = age.total_seconds() / 3600
                is_stale = age_hours > threshold_hours
            except (ValueError, OSError):
                last_run = None
                age_hours = float("inf")
                is_stale = True
        else:
            last_run = None
            age_hours = float("inf")
            is_stale = True

        return {
            "name": stage_name,
            "last_run": last_run.isoformat() if last_run else None,
            "age_hours": age_hours if age_hours != float("inf") else None,
            "is_stale": is_stale,
            "threshold_hours": threshold_hours,
            "status": "never_run" if last_run is None else ("stale" if is_stale else "fresh"),
        }

    def check_api_health(self, url: str = "http://localhost:8000/health") -> Dict:
        """Check API health endpoint."""
        try:
            import requests

            response = requests.get(url, timeout=5)
            return {
                "accessible": True,
                "status_code": response.status_code,
                "healthy": response.status_code == 200,
            }
        except ImportError:
            # requests not installed, try with basic urllib
            try:
                import urllib.request

                with urllib.request.urlopen(url, timeout=5) as response:
                    return {
                        "accessible": True,
                        "status_code": response.status,
                        "healthy": response.status == 200,
                    }
            except:
                return {"accessible": False, "status_code": None, "healthy": False}
        except Exception:
            return {"accessible": False, "status_code": None, "healthy": False}

    def check_disk_space(self) -> Dict:
        """Check disk space for critical directories."""
        results = {}

        critical_dirs = [
            ("project_root", self.project_root),
            ("logs", self.log_dir),
            ("stamps", self.stamp_dir),
        ]

        for name, path in critical_dirs:
            try:
                if path.exists():
                    # Windows-specific disk space check
                    import shutil

                    usage = shutil.disk_usage(path)

                    results[name] = {
                        "path": str(path),
                        "total_gb": usage.total / (1024**3),
                        "used_gb": usage.used / (1024**3),
                        "free_gb": usage.free / (1024**3),
                        "percent_used": (usage.used / usage.total) * 100,
                        "status": (
                            "critical"
                            if usage.free < 1024**3
                            else "warning" if usage.free < 5 * 1024**3 else "ok"
                        ),
                    }
                else:
                    results[name] = {"path": str(path), "status": "not_found"}
            except Exception as e:
                results[name] = {"path": str(path), "status": "error", "error": str(e)}

        return results

    def check_system_health(self) -> Dict:
        """Get comprehensive system health report."""
        # Check Zeus components
        components = {
            "zeus_listener": self.check_component_health("zeus_listener", "zeus_listener.py"),
            "reorg_sanitizer": self.check_component_health("reorg_sanitizer", "reorg_sanitizer.py"),
            "auto_ml_worker": self.check_component_health("auto_ml_worker", "auto_ml_worker.py"),
        }

        # Check pipelines
        pipelines = {
            "00_ingest": self.check_pipeline_health("00_ingest", 24),
            "01_staging": self.check_pipeline_health("01_staging", 12),
            "02_processing": self.check_pipeline_health("02_processing", 6),
            "03_rag": self.check_pipeline_health("03_rag", 6),
        }

        # Check API
        api_health = self.check_api_health()

        # Check disk space
        disk_health = self.check_disk_space()

        # Determine overall status
        component_statuses = [c["status"] for c in components.values()]
        pipeline_statuses = [p["status"] for p in pipelines.values()]

        if all(s == "healthy" for s in component_statuses):
            overall_status = "healthy"
        elif any(s == "down" for s in component_statuses):
            overall_status = "critical"
        elif any(s == "degraded" for s in component_statuses):
            overall_status = "degraded"
        elif all(s in ["never_run", "stopped"] for s in component_statuses):
            overall_status = "not_started"
        else:
            overall_status = "warning"

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "components": components,
            "pipelines": pipelines,
            "api": api_health,
            "system": {"disk_space": disk_health},
        }

    def print_health_report(self, health: Optional[Dict] = None):
        """Print human-readable health report."""
        if health is None:
            health = self.check_system_health()

        print("\n" + "=" * 70)
        print("ZEUS SYSTEM HEALTH REPORT")
        print("=" * 70)
        print(f"Timestamp: {health['timestamp']}")
        print(f"Overall Status: {health['overall_status'].upper()}")

        print("\n" + "-" * 70)
        print("COMPONENTS")
        print("-" * 70)

        status_icons = {
            "healthy": "✓",
            "degraded": "⚠",
            "down": "✗",
            "stopped": "○",
            "never_run": "?",
            "unknown": "?",
        }

        for comp_name, comp in health["components"].items():
            icon = status_icons.get(comp["status"], "?")
            print(f"\n{icon} {comp['name']:20s} [{comp['status'].upper()}]")
            print(f"  Running: {comp['running']}")
            print(f"  Log Entries (24h): {comp['log_entries_24h']}")
            print(f"  Errors (24h): {comp['error_count_24h']}")

            if comp["last_log_time"]:
                last_time = datetime.fromisoformat(comp["last_log_time"])
                age = datetime.now() - last_time
                print(f"  Last Activity: {age.total_seconds() / 60:.1f} minutes ago")

        print("\n" + "-" * 70)
        print("PIPELINES")
        print("-" * 70)

        for pipe_name, pipe in health["pipelines"].items():
            icon = "✗" if pipe["is_stale"] else "✓"

            print(f"\n{icon} {pipe['name']:20s}")

            if pipe["last_run"]:
                print(f"  Last Run: {pipe['age_hours']:.1f} hours ago")
                print(f"  Threshold: {pipe['threshold_hours']} hours")
                print(f"  Status: {pipe['status'].upper()}")
            else:
                print("  Last Run: Never")
                print("  Status: NEVER RUN")

        print("\n" + "-" * 70)
        print("API SERVER")
        print("-" * 70)

        api = health["api"]
        api_icon = "✓" if api["healthy"] else "✗"
        print(f"{api_icon} API Accessible: {api['accessible']}")
        if api["status_code"]:
            print(f"  Status Code: {api['status_code']}")
        print(f"  Healthy: {api['healthy']}")

        print("\n" + "-" * 70)
        print("DISK SPACE")
        print("-" * 70)

        for name, disk in health["system"]["disk_space"].items():
            if disk["status"] in ["ok", "warning", "critical"]:
                status_icon = (
                    "✓" if disk["status"] == "ok" else "⚠" if disk["status"] == "warning" else "✗"
                )
                print(
                    f"{status_icon} {name:15s}: {disk['free_gb']:.1f}GB free / {disk['total_gb']:.1f}GB total ({disk['percent_used']:.1f}% used)"
                )
            else:
                print(f"✗ {name:15s}: {disk['status']}")

        print("\n" + "=" * 70)
        print(f"Overall Health: {health['overall_status'].upper()}")
        print("=" * 70 + "\n")

    def save_health_report(self, output_file: Path, health: Optional[Dict] = None):
        """Save health report to JSON file."""
        if health is None:
            health = self.check_system_health()

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(health, indent=2, default=str), encoding="utf-8")
        print(f"Health report saved to: {output_file}")

    def get_exit_code(self, health: Optional[Dict] = None) -> int:
        """Get exit code based on health status."""
        if health is None:
            health = self.check_system_health()

        status = health["overall_status"]

        if status == "healthy":
            return 0
        elif status in ["warning", "degraded"]:
            return 1
        elif status in ["critical", "down"]:
            return 2
        else:
            return 3

    def check_component(self, name: str, command: list) -> Dict:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            status = "ok" if result.returncode == 0 else "error"
            return {"status": status, "output": result.stdout, "error": result.stderr}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_checks(self):
        self.results["checks"]["pipelines"] = self.check_component(
            "pipelines", [sys.executable, "scripts/dev/run_all_pipelines.py"]
        )
        self.results["checks"]["api"] = self.check_component(
            "api", [sys.executable, "-m", "uvicorn", "--help"]
        )
        # Add more checks as needed

    def generate_report(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Report saved to {output_path}")


def main():
    """Main entry point with error handling."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Zeus System Health Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/prod/health_check.py
  python scripts/prod/health_check.py --json logs/health_report.json
  python scripts/prod/health_check.py --quiet
        """,
    )
    parser.add_argument("--json", type=Path, help="Save health report to JSON file")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (useful for monitoring scripts)",
    )

    args = parser.parse_args()

    try:
        checker = HealthChecker()
        health = checker.check_system_health()

        if not args.quiet:
            checker.print_health_report(health)

        if args.json:
            checker.save_health_report(args.json, health)

        exit_code = checker.get_exit_code(health)

        if not args.quiet:
            if exit_code != 0:
                print(f"\n⚠ ALERT: System is not fully healthy (exit code: {exit_code})")
                print("Check the report above for details.")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n\nHealth check interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ HEALTH CHECK FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
