"""Utility to execute commands within the offline CI sandbox.

The script injects the local ``sitecustomize`` module, forces offline-related
environment variables (``OFFLINE_MODE``, ``PIP_NO_INDEX``), and then delegates
the requested command to ``subprocess.run``.  It serves as the entry point for
VS Code tasks and CI jobs that must simulate an environment with no internet
connectivity.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from typing import List

HOOK_DIR = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute a command with offline network guard")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute (everything after '--' is treated as the command)",
    )
    parser.add_argument(
        "--allow-host",
        action="append",
        default=[],
        help="Additional host that should be reachable (loopback is allowed by default)",
    )
    return parser


def prepare_environment(allowed_hosts: List[str]) -> dict:
    env = os.environ.copy()

    # Inject the offline sitecustomize directory at the front of PYTHONPATH.
    pythonpath_entries = [str(HOOK_DIR)]
    if env.get("PYTHONPATH"):
        pythonpath_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

    # Advertise offline mode to the rest of the stack.
    env.setdefault("OFFLINE_MODE", "true")

    # Ensure pip works against local wheel cache only.
    packages_dir = Path("packages").resolve()
    env.setdefault("PIP_NO_INDEX", "1")
    env.setdefault("PIP_FIND_LINKS", str(packages_dir))

    if allowed_hosts:
        env["OFFLINE_CI_ALLOW_HOSTS"] = ",".join(allowed_hosts)

    return env


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.error("No command supplied. Use '-- <cmd> [args]' to pass the command.")

    env = prepare_environment(args.allow_host)

    result = subprocess.run(args.command, env=env, text=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
