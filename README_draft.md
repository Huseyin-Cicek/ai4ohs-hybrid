Here’s the agreed folder layout for **code**, **raw (Data Lake)**, and **clean (Data Warehouse)**. I’ve fully expanded the **code** tree with practical submodules and config files so you can scaffold it 1:1.

# 1) CODE — `C:\vscode-projects\ai4ohs-hybrid\`

```text
ai4ohs-hybrid/
├── .gitignore
├── .env.example
├── LICENSE
├── README.md
├── requirements.txt
├── pyproject.toml
├── setup.cfg
├── .editorconfig
├── .pre-commit-config.yaml
├── .vscode/
│   ├── extensions.json
│   ├── settings.json
│   ├── launch.json
│   └── tasks.json
├── scripts/
│   ├── dev/
│   │   ├── zeus_listener.py
│   │   ├── auto_ml_worker.py
│   │   ├── reorg_sanitizer.py
│   │   ├── register_zeus_startup.ps1
│   │   ├── zeus_ml_summary_example.json
│   │   └── startup/
│   │       ├── zeus_listener_startup.cmd
│   │       └── readme.txt
│   └── tools/
│       ├── backup_dataset.py
│       ├── validate_tree.py
│       └── check_md_links.py
├── docs/
│   ├── ai4ohs-hybrid-roadmap.md
│   ├── ai4ohs-hybrid-system-instructions.md
│   ├── ai4ohs-hybrid-rag-cag-instructions.txt
│   ├── ai4ohs_data_flow_pipeline.md
│   ├── zeus_listener.md
│   ├── ffmp.md
│   ├── faiss.md
│   └── secrets.md
├── logs/                          # git-ignored (runtime)
│   ├── dev/
│   ├── api/
│   ├── pipelines/
│   └── tools/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # OFFLINE_MODE, paths, model names
│   │   ├── paths.py               # central path resolver (code/raw/clean)
│   │   ├── logging_conf.yaml
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── documents.py       # Pydantic models (DocMeta, DocChunk…)
│   │       └── datasets.py        # Dataset schemas (incidents, NCR, SOF…)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_extract.py        # pdf/docx/ocr dispatchers
│   │   ├── ocr.py
│   │   ├── cleaners.py            # unicode/whitespace/boilerplate removal
│   │   ├── splitters.py           # rule-based & token-aware splitting
│   │   ├── hashing.py
│   │   ├── files.py               # safe fs ops, sanitizer, dedupe
│   │   ├── embeddings.py
│   │   ├── faiss_index.py
│   │   ├── reranker.py
│   │   ├── search.py              # retriever + hybrid scoring
│   │   ├── compliance.py          # CAG guardrail rules
│   │   └── wb_ifc_mappers.py      # ESS/EHS mapping helpers
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── 00_ingest/
│   │   │   ├── __init__.py
│   │   │   ├── run.py             # entrypoint
│   │   │   ├── loaders/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fs_loader.py   # local FS, mail backups, OneDrive exports
│   │   │   │   ├── pdf_loader.py
│   │   │   │   ├── docx_loader.py
│   │   │   │   ├── image_loader.py
│   │   │   │   └── excel_loader.py
│   │   │   ├── validators/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mime_checks.py
│   │   │   │   └── filename_policy.py
│   │   │   └── parsers/
│   │   │       ├── __init__.py
│   │   │       ├── pdf_parser.py
│   │   │       ├── docx_parser.py
│   │   │       └── image_ocr_parser.py
│   │   ├── 01_staging/
│   │   │   ├── __init__.py
│   │   │   ├── run.py
│   │   │   ├── normalizers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── text_normalizer.py
│   │   │   │   └── metadata_normalizer.py
│   │   │   ├── enrichers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── language_detect.py
│   │   │   │   └── date_location_tagging.py
│   │   │   └── qc/
│   │   │       ├── __init__.py
│   │   │       └── staging_validations.py
│   │   ├── 02_processing/
│   │   │   ├── __init__.py
│   │   │   ├── run.py
│   │   │   ├── chunking/
│   │   │   │   ├── __init__.py
│   │   │   │   └── rules.py
│   │   │   ├── embedding/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── build_embeddings.py
│   │   │   │   └── models.py      # sentence-transformers config
│   │   │   ├── index/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── build_faiss.py
│   │   │   │   └── index_layout.py
│   │   │   └── stats/
│   │   │       ├── __init__.py
│   │   │       └── dataset_stats.py
│   │   ├── 03_rag/
│   │   │   ├── __init__.py
│   │   │   ├── run.py
│   │   │   ├── retriever/
│   │   │   │   ├── __init__.py
│   │   │   │   └── bm25_hybrid.py
│   │   │   ├── reranker/
│   │   │   │   ├── __init__.py
│   │   │   │   └── cross_encoder.py
│   │   │   └── eval/
│   │   │       ├── __init__.py
│   │   │       └── rag_eval.py
│   └── ohs/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py            # FastAPI app (uvicorn entrypoint)
│       │   ├── routers/
│       │   │   ├── __init__.py
│       │   │   ├── health.py
│       │   │   ├── search.py      # /search?q=... (RAG)
│       │   │   ├── guardrails.py  # /validate (CAG checks)
│       │   │   └── datasets.py    # list/query indexed datasets
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── request.py
│       │   │   └── response.py
│       │   └── deps/
│       │       ├── __init__.py
│       │       └── containers.py  # DI wiring, settings, logger
│       └── services/
│           ├── __init__.py
│           ├── rag_service.py
│           ├── cag_service.py
│           └── logging_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_cleaners.py
│   │   ├── test_splitters.py
│   │   ├── test_embeddings.py
│   │   └── test_faiss_index.py
│   └── api/
│       ├── test_health.py
│       ├── test_search.py
│       └── test_guardrails.py
└── examples/
    ├── curl_search.http
    └── postman_collection.json
```

**Notes (code):**

* **Entrypoints**

  * Pipelines:

    ```powershell
    python src/pipelines/00_ingest/run.py
    python src/pipelines/01_staging/run.py
    python src/pipelines/02_processing/run.py
    python src/pipelines/03_rag/run.py
    ```
  * API:

    ```powershell
    uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000
    ```
* **Key env toggles** in `src/config/settings.py`: `OFFLINE_MODE`, `EMBEDDING_MODEL`, `RERANKER_MODEL`, `GPU_ACCELERATION`, base paths for **raw/clean**.
* **.env.example** should define `RAW_ROOT`, `CLEAN_ROOT`, `LOG_ROOT`, `OFFLINE_MODE`, etc.
* **logs/** stays Git-ignored.
* **pre-commit** handles Ruff/Black/Isort and MD link checks.

---

# 2) RAW — Data Lake — `H:\DataLake\ai4ohs-hybrid-datasets-raw\`

```text
ai4ohs-hybrid-datasets-raw/
├── _archive/                                # long-term frozen sources
│   ├── 2024/
│   └── 2025/
├── _system/
│   ├── _bin/
│   ├── _cache/
│   ├── _inventory/                          # file inventory (parquet/csv)
│   ├── _reports/
│   ├── config/
│   ├── logs/
│   └── backup/
├── 00_sources/
│   ├── mailbackup/
│   ├── onedrive_local/
│   ├── hsse-docs/
│   ├── isg-docs/
│   ├── images/
│   ├── video/
│   └── _dropzone/                           # hot folder (FFMP sanitizes)
├── 01_staging/
│   ├── _workdir_tmp/
│   ├── normalized_text/
│   ├── ocr/
│   ├── metadata/                            # extracted front-matter JSON
│   └── qc_reports/
└── 02_processing/
    ├── chunks/
    ├── embeddings/
    ├── faiss/
    ├── hybrid_indexes/
    └── stats/
```

**Notes (raw):**

* **FFMP** writes sanitized copies from `00_sources/_dropzone` → into proper subfolders.
* `01_staging` holds normalized text & OCR outputs with per-file `*.meta.json`.

---

# 3) CLEAN — Data Warehouse — `H:\DataWarehouse\ai4ohs-datasets-clean\`

```text
ai4ohs-datasets-clean/
├── dims/                                     # slowly changing dims
│   ├── dim_projects.parquet
│   ├── dim_contractors.parquet
│   ├── dim_locations.parquet
│   ├── dim_assets.parquet
│   └── dim_workers.parquet
├── facts/
│   ├── fact_incidents_daily.parquet
│   ├── fact_near_miss.parquet
│   ├── fact_ncr.parquet
│   ├── fact_sof.parquet
│   ├── fact_training_hours.parquet
│   └── fact_kpi_monthly.parquet
├── entities/                                  # curated entity tables
│   ├── incidents/
│   ├── ncr/
│   ├── sof/
│   ├── permits/
│   ├── audits/
│   └── trainings/
├── marts/                                     # reporting-ready views
│   ├── wb_ifc_esmf_annex9/
│   ├── iso_45001_dash/
│   └── exec_summary/
├── exports/
│   ├── excel/
│   ├── csv/
│   └── json/
└── backup/
```

**Notes (clean):**

* **facts/** and **dims/** are the canonical star-schema layers for reporting.
* **marts/** aligns directly to deliverables (e.g., ESMF Annex 9, ILBANK dashboards).

---

## Suggested `.gitignore` (key lines)

```gitignore
# Python
.venv/
__pycache__/
*.pyc

# Local config
.env
logs/
*.log
*.sqlite

# Data (never commit)
H:/DataLake/
H:/DataWarehouse/

# Tools
.vscode/.ropeproject/
```

## Quick Scaffolding (PowerShell)

```powershell
# run from C:\vscode-projects
mkdir ai4ohs-hybrid, cd ai4ohs-hybrid
# create folders
"scripts/dev","scripts/tools",".vscode","docs","logs","tests/unit","tests/api",
"src","src/config/schemas","src/utils","src/pipelines/00_ingest/loaders",
"src/pipelines/00_ingest/validators","src/pipelines/00_ingest/parsers",
"src/pipelines/01_staging/normalizers","src/pipelines/01_staging/enrichers","src/pipelines/01_staging/qc",
"src/pipelines/02_processing/chunking","src/pipelines/02_processing/embedding","src/pipelines/02_processing/index","src/pipelines/02_processing/stats",
"src/pipelines/03_rag/retriever","src/pipelines/03_rag/reranker","src/pipelines/03_rag/eval",
"src/ohs/api/routers","src/ohs/api/models","src/ohs/api/deps","src/ohs/services","examples" |
% { mkdir $_ -Force } | Out-Null
# touch common files
"README.md",".gitignore",".env.example","requirements.txt","pyproject.toml","setup.cfg",".editorconfig",".pre-commit-config.yaml" |
% { ni $_ -ItemType File -Force } | Out-Null
```

## README.md
# AI4OHS-HYBRID — Dual-Mode OHS Intelligence Engine
RAG + CAG + Compliance Guardrails + Zeus Automation Layer

---

### Overview
AI4OHS-HYBRID is a dual-mode (offline/online) intelligent Occupational Health & Safety system
designed for high-compliance infrastructure projects (WB / IFC ESS, ISO 45001, OSHA, 6331).

| Layer | Purpose |
|-------|----------|
| **RAG** | Local + cloud-optional semantic retrieval across OHS datasets |
| **CAG** | Compliance-Augmented Generation — rule-based legal & standard validation |
| **ETL Pipelines** | Ingest → Staging → Processing → RAG Index |
| **Zeus Automation** | Local voice trigger, file sanitizer, task scheduler |
| **Dual Execution** | Works 100 % offline or cloud-assisted |

---

### Quick Start
```bash
# 1️⃣ Install
python -m venv .venv && .\.venv\Scripts\activate
pip install -r requirements.txt

# 2️⃣ Run Pipelines
python src/pipelines/00_ingest/run.py
python src/pipelines/01_staging/run.py
python src/pipelines/02_processing/run.py
python src/pipelines/03_rag/run.py

# 3️⃣ Start API
uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000

Core Paths

Raw Data Lake: H:\DataLake\ai4ohs-hybrid-datasets-raw\

Clean Data Warehouse: H:\DataWarehouse\ai4ohs-datasets-clean\

Logs: logs\ (auto-excluded from Git)

Key Environment Flags
Variable	Description
OFFLINE_MODE	"true" = no remote model downloads
EMBEDDING_MODEL	Sentence Transformer used for RAG
RERANKER_MODEL	Cross-encoder reranker
GPU_ACCELERATION	Enable CUDA if available
Compliance Guardrails

Enforced via rule sets from ISO 45001, OSHA 29 CFR, Law 6331, and WB/IFC ESS.

Unsafe or non-regulatory recommendations are auto-blocked.

Developer Shortcuts
Command	Description
task: Run Pipelines	Runs all ETL stages sequentially
task: Start API	Launch FastAPI server
task: Format Code	Ruff + Black + Isort
task: Docs Check	Markdown link validation

© 2025 AI4OHS-HYBRID Project | OHS Compliance & Automation Framework


---

## ⚙️ `.gitignore`
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.venv/
.env
env/
venv/

# Logs & caches
logs/
*.log
.cache/
__snapshots__/

# Data paths
H:/DataLake/ #raw data
H:/DataWarehouse/ #processed data

# VS Code
.vscode/.ropeproject/
.vscode/ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db

🔑 .env.example
# === Core Paths ===
RAW_ROOT=H:\DataLake\ai4ohs-hybrid-datasets-raw
CLEAN_ROOT=H:\DataWarehouse\ai4ohs-datasets-clean
LOG_ROOT=C:\vscode-projects\ai4ohs-hybrid\logs

# === Runtime ===
OFFLINE_MODE=true
GPU_ACCELERATION=true

# === Models ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L12-v2
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# === API ===
API_HOST=127.0.0.1
API_PORT=8000

🧾 requirements.txt
fastapi
uvicorn
pydantic
python-dotenv
sentence-transformers
faiss-cpu
rank-bm25
numpy
pandas
openpyxl
python-docx
pdfplumber
pytesseract
pillow
scikit-learn
loguru
black
isort
ruff
pre-commit
jinja2
pyyaml
watchdog

🧱 pyproject.toml
[build-system]
requires = ["setuptools", "wheel"]

[tool.black]
line-length = 100
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.ruff]
select = ["E", "F", "I"]
ignore = ["E501"]
line-length = 100

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
show_missing = true

⚙️ setup.cfg
[metadata]
name = ai4ohs-hybrid
version = 2025.11.0
description = Dual-Mode OHS Intelligence Engine (RAG + CAG)
author = AI4OHS-HYBRID Team
license = MIT

[options]
packages = find:
install_requires =
    fastapi
    uvicorn
    pydantic
python_requires = >=3.10

[flake8]
max-line-length = 100
exclude = .venv,logs,__pycache__

✏️ .editorconfig
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 4
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

🧹 .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-isort
    rev: v5.13.2
    hooks:
      - id: isort
  - repo: local
    hooks:
      - id: check-md-links
        name: Markdown Link Checker
        entry: python scripts/tools/check_md_links.py
        language: system
        files: \.md$

💻 .vscode/settings.json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.minimap.enabled": false,
    "editor.wordWrap": "on",
    "editor.rulers": [100],
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "terminal.integrated.shellIntegration.enabled": true,
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "notebook.formatOnSave.enabled": true,
    "notebook.cellToolbarVisibility": "hover",
    "notebook.output.textLineLimit": 50,
    "notebook.output.wordWrap": "on"
}

🧭 .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run FastAPI (AI4OHS-HYBRID)",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.ohs.api.main:app",
                "--reload",
                "--host", "127.0.0.1",
                "--port", "8000"
            ],
            "jinja": true,
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Run Pipeline 00→03",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/dev/run_all_pipelines.py"
        }
    ]
}

⚙️ .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Pipelines",
            "type": "shell",
            "command": "python src/pipelines/00_ingest/run.py && python src/pipelines/01_staging/run.py && python src/pipelines/02_processing/run.py && python src/pipelines/03_rag/run.py",
            "group": { "kind": "build", "isDefault": true },
            "presentation": { "reveal": "always" },
            "problemMatcher": []
        },
        {
            "label": "Start API",
            "type": "shell",
            "command": "uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000",
            "group": "test",
            "presentation": { "reveal": "always" }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "ruff check . --fix && black . && isort .",
            "group": "none"
        },
        {
            "label": "Docs Check",
            "type": "shell",
            "command": "python scripts/tools/check_md_links.py",
            "group": "none"
        }
    ]
}

## scripts/dev/run_all_pipelines.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI4OHS-HYBRID — Full Pipeline Runner
------------------------------------
Sequentially runs the ETL stages:
00_ingest → 01_staging → 02_processing → 03_rag

Usage:
    python scripts/dev/run_all_pipelines.py

The script logs start/end time, captures exceptions, and
writes results to logs/pipelines/run_all.log.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# === PATH SETUP ===
ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs" / "pipelines"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "run_all.log"

PIPELINE_ORDER = [
    "src/pipelines/00_ingest/run.py",
    "src/pipelines/01_staging/run.py",
    "src/pipelines/02_processing/run.py",
    "src/pipelines/03_rag/run.py",
]


def log(msg: str):
    """Write both to stdout and log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(formatted + "\n")


def run_stage(stage_path: str) -> bool:
    """Run a pipeline stage with subprocess."""
    log(f"▶ Starting stage: {stage_path}")
    start = time.time()
    try:
        subprocess.run([sys.executable, stage_path], check=True)
        elapsed = round(time.time() - start, 2)
        log(f"✅ Completed {stage_path} in {elapsed}s")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ ERROR in {stage_path}: {e}")
        return False


def main():
    log("=" * 60)
    log("🚀 AI4OHS-HYBRID — Full Pipeline Run START")
    log(f"Working directory: {ROOT_DIR}")
    log("=" * 60)

    overall_start = time.time()
    success_count = 0

    for stage in PIPELINE_ORDER:
        if run_stage(stage):
            success_count += 1
        else:
            log("⚠️ Skipping remaining stages due to error.")
            break

    total_time = round(time.time() - overall_start, 2)
    log("-" * 60)
    log(f"🏁 Finished {success_count}/{len(PIPELINE_ORDER)} stages in {total_time}s")
    log("=" * 60 + "\n")


if __name__ == "__main__":
    main()

🔍 Features

Sequential, fail-fast execution (stops on first failure).

Real-time console output + log file at logs/pipelines/run_all.log.

Timestamped logging for reproducible ETL audits.

Compatible with VS Code launch.json and tasks.json.

Cross-platform (Windows PowerShell / Linux bash).

✅ Example Output
[2025-11-09 21:57:10] 🚀 AI4OHS-HYBRID — Full Pipeline Run START
[2025-11-09 21:57:10] ▶ Starting stage: src/pipelines/00_ingest/run.py
[2025-11-09 21:57:15] ✅ Completed src/pipelines/00_ingest/run.py in 4.8s
[2025-11-09 21:57:15] ▶ Starting stage: src/pipelines/01_staging/run.py
[2025-11-09 21:57:23] ✅ Completed src/pipelines/01_staging/run.py in 7.5s
[2025-11-09 21:57:23] ▶ Starting stage: src/pipelines/02_processing/run.py
[2025-11-09 21:57:41] ✅ Completed src/pipelines/02_processing/run.py in 18.0s
[2025-11-09 21:57:41] ▶ Starting stage: src/pipelines/03_rag/run.py
[2025-11-09 21:57:50] ✅ Completed src/pipelines/03_rag/run.py in 8.8s
[2025-11-09 21:57:50] 🏁 Finished 4/4 stages in 39.1s

## scripts/dev/run_all_pipelines.ps1

<#
.SYNOPSIS
    AI4OHS-HYBRID — Full Pipeline Runner (PowerShell launcher)

.DESCRIPTION
    Launches scripts/dev/run_all_pipelines.py with robust logging, colorized output,
    and proper exit codes for Windows Task Scheduler and CI.

.USAGE
    pwsh -File scripts/dev/run_all_pipelines.ps1
    powershell -ExecutionPolicy Bypass -File scripts/dev/run_all_pipelines.ps1

.NOTES
    - Prefers .venv\Scripts\python.exe if present, otherwise falls back to system "python".
    - Transcript logs are saved under logs\pipelines\ with a timestamped filename.
#>

# Strict mode and fail-fast behavior
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ===== Path resolution (repo-root aware) =====
$devDir     = Split-Path -Parent $MyInvocation.MyCommand.Path         # ...\scripts\dev
$scriptsDir = Split-Path -Parent $devDir                               # ...\scripts
$repoRoot   = Split-Path -Parent $scriptsDir                           # repo root
$runnerPy   = Join-Path $devDir 'run_all_pipelines.py'
$logsDir    = Join-Path $repoRoot 'logs\pipelines'

# Ensure logs directory exists
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

# Timestamped transcript file
$stamp          = Get-Date -Format 'yyyyMMdd_HHmmss'
$transcriptPath = Join-Path $logsDir "run_all_ps1_$stamp.log"

# ===== Environment hardening =====
# Make sure Python uses UTF-8 for consistent logs
$env:PYTHONUTF8      = '1'
$env:PYTHONIOENCODING = 'utf-8'

# Prefer local venv python if available
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = 'python'
}

# Basic banner
Write-Host ('=' * 70)
Write-Host "AI4OHS-HYBRID — Pipeline Launcher (PowerShell)" -ForegroundColor Cyan
Write-Host "Repo Root     : $repoRoot"
Write-Host "Python        : $pythonExe"
Write-Host "Runner        : $runnerPy"
Write-Host "Transcript Log: $transcriptPath"
Write-Host ('=' * 70)

# Validate runner presence
if (-not (Test-Path $runnerPy)) {
    Write-Host "ERROR: Runner script not found: $runnerPy" -ForegroundColor Red
    exit 1
}

# Start transcript (best-effort; still proceed if it fails)
$transcriptStarted = $false
try {
    Start-Transcript -Path $transcriptPath -Force -ErrorAction Stop | Out-Null
    $transcriptStarted = $true
} catch {
    Write-Host "WARN: Could not start transcript: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Execute the Python orchestrator
$overallStart = Get-Date
try {
    Write-Host "[START] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') — Running full ETL (00→03)..." -ForegroundColor Green

    & $pythonExe $runnerPy
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-Host "[FAIL] run_all_pipelines.py exited with code $exitCode" -ForegroundColor Red
        if ($transcriptStarted) {
            try { Stop-Transcript | Out-Null } catch {}
        }
        exit $exitCode
    }

    $elapsed = New-TimeSpan -Start $overallStart -End (Get-Date)
    $elapsedMsg = "{0:hh\:mm\:ss}" -f $elapsed
    Write-Host "[DONE] All stages completed successfully in $elapsedMsg" -ForegroundColor Green

    if ($transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
    }

    exit 0
}
catch {
    $err = $_.Exception
    Write-Host "EXCEPTION: $($err.GetType().FullName)" -ForegroundColor Red
    Write-Host "MESSAGE  : $($err.Message)" -ForegroundColor Red
    if ($err.StackTrace) {
        Write-Host "STACKTRACE:" -ForegroundColor DarkGray
        Write-Host $err.StackTrace -ForegroundColor DarkGray
    }

    if ($transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
    }
    exit 1
}

######################
Tip (first run): If you hit execution policy blocks, run this once in an elevated PowerShell:

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force
