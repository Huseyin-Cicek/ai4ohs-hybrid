#!/usr/bin/env bash
set -euo pipefail

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
  FORCE=true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

create_venv() {
  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "[*] Creating virtual environment at ${VENV_DIR}"
    if command -v python3 >/dev/null 2>&1; then
      python3 -m venv "${VENV_DIR}"
    else
      python -m venv "${VENV_DIR}"
    fi
  else
    echo "[i] Virtual environment already exists"
  fi
}

resolve_python() {
  if [[ "${OS:-}" == "Windows_NT" ]]; then
    PY_BIN="${VENV_DIR}/Scripts/python.exe"
  else
    PY_BIN="${VENV_DIR}/bin/python"
  fi

  if [[ ! -f "${PY_BIN}" ]]; then
    echo "[!] Python executable not found at ${PY_BIN}" >&2
    exit 1
  fi

  echo "${PY_BIN}"
}

install_packages() {
  local python_bin="$1"
  "${python_bin}" -m pip install --upgrade pip

  local requirements_file
  if [[ -f "${REPO_ROOT}/requirements.lock" ]]; then
    requirements_file="${REPO_ROOT}/requirements.lock"
  else
    requirements_file="${REPO_ROOT}/requirements.performans.txt"
  fi

  echo "[*] Installing packages from ${requirements_file}"
  "${python_bin}" -m pip install -r "${requirements_file}"

  echo "[*] Installing pre-commit hooks"
  "${python_bin}" -m pre_commit install
}

write_tasks() {
  local tasks_dir="${REPO_ROOT}/.vscode"
  local tasks_file="${tasks_dir}/tasks.json"

  mkdir -p "${tasks_dir}"

  if [[ "${FORCE}" == true || ! -f "${tasks_file}" ]]; then
    echo "[*] Writing VS Code tasks to ${tasks_file}"
    cat >"${tasks_file}" <<'JSON'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Pipelines",
      "type": "shell",
      "command": "python src/pipelines/00_ingest/run.py && python src/pipelines/01_staging/run.py && python src/pipelines/02_processing/run.py && python src/pipelines/03_rag/run.py",
      "group": { "kind": "build", "isDefault": true }
    },
    {
      "label": "Start API",
      "type": "shell",
      "command": "uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000"
    },
    {
      "label": "Run Full System Validation",
      "type": "shell",
      "command": "python scripts/dev/run_all_pipelines.py",
      "group": { "kind": "build", "isDefault": true },
      "problemMatcher": [],
      "presentation": { "reveal": "always", "panel": "shared" }
    },
    {
      "label": "Format Code",
      "type": "shell",
      "command": "ruff check . --fix && black . && isort ."
    },
    {
      "label": "Docs Check",
      "type": "shell",
      "command": "python scripts/tools/check_md_links.py"
    }
  ]
}
JSON
  else
    echo "[i] Existing VS Code tasks preserved"
  fi
}

create_venv
PYTHON_BIN="$(resolve_python)"
install_packages "${PYTHON_BIN}"
write_tasks

echo "[✓] Bootstrap complete"
