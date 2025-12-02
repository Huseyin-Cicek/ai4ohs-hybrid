"""
Zeus Voice Listener - Offline voice command execution

Responsibilities:
- READ stamps (report last run times)
- WRITE logs (command history)
- NO cache operations (stateless)
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import subprocess


class ZeusVoiceListener:
    def __init__(self):
        self.log_file = Path("logs/dev/zeus_commands.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.commands = {
            "run pipelines": self._run_pipelines,
            "start api": self._start_api,
            "format code": self._format_code,
        }

    def _log(self, event_type: str, message: str):
        timestamp = datetime.now().isoformat()
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {event_type}: {message}\n")

    def _run_pipelines(self):
        self._log("COMMAND", "Running pipelines")
        subprocess.run(["python", "scripts/dev/run_all_pipelines.py"])

    def _start_api(self):
        self._log("COMMAND", "Starting API")
        subprocess.run(["uvicorn", "src.ohs.api.main:app", "--reload"])

    def _format_code(self):
        self._log("COMMAND", "Formatting code")
        subprocess.run(["ruff", "check", ".", "--fix"])
        subprocess.run(["black", "."])
        subprocess.run(["isort", "."])

    def listen(self):
        print("Zeus Voice Listener started. Type 'exit' to quit.")
        while True:
            command = input("Zeus> ").strip().lower()
            if command == "exit":
                break
            action = self.commands.get(command)
            if action:
                action()
            else:
                print(f"Unknown command: {command}")


if __name__ == "__main__":
    listener = ZeusVoiceListener()
    listener.listen()
