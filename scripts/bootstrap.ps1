param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvPath = Join-Path $repoRoot ".venv"

function Initialize-Venv {
    if (-not (Test-Path $venvPath)) {
        Write-Host "[*] Creating virtual environment at $venvPath"
        python -m venv $venvPath
    }
    else {
        Write-Host "[i] Virtual environment already exists"
    }
}

function Get-PythonPath {
    $pythonExe = Join-Path $venvPath "Scripts/python.exe"
    if (-not (Test-Path $pythonExe)) {
        throw "Python executable not found at $pythonExe"
    }
    return $pythonExe
}

function Install-Packages {
    param(
        [string]$PythonExe
    )

    & $PythonExe -m pip install --upgrade pip

    $requirementsFile = if (Test-Path (Join-Path $repoRoot "requirements.lock")) {
        Join-Path $repoRoot "requirements.lock"
    }
    else {
        Join-Path $repoRoot "requirements.performans.txt"
    }

    Write-Host "[*] Installing packages from $requirementsFile"
    & $PythonExe -m pip install -r $requirementsFile

    Write-Host "[*] Installing pre-commit hooks"
    & $PythonExe -m pre_commit install
}

function Set-TasksFile {
    $vscodeDir = Join-Path $repoRoot ".vscode"
    if (-not (Test-Path $vscodeDir)) {
        New-Item -ItemType Directory -Path $vscodeDir | Out-Null
    }

    $tasksPath = Join-Path $vscodeDir "tasks.json"
    if ($Force -or -not (Test-Path $tasksPath)) {
        Write-Host "[*] Writing VS Code tasks to $tasksPath"
        $tasksContent = @'
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Pipelines 00→03",
      "type": "shell",
      "command": "python src/pipelines/00_ingest/run.py && python src/pipelines/01_staging/run.py && python src/pipelines/02_processing/run.py && python src/pipelines/03_rag/run.py",
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "options": {
        "env": {
          "PYTHONPATH": "${workspaceFolder}"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "Start API",
      "type": "shell",
      "command": "uvicorn src.ohs.api.main:app --reload --host 127.0.0.1 --port 8000",
      "options": {
        "env": {
          "PYTHONPATH": "${workspaceFolder}"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "Run Full System Validation",
      "type": "shell",
      "command": "python scripts/dev/run_all_pipelines.py",
      "group": {
        "kind": "test",
        "isDefault": false
      },
      "problemMatcher": [],
      "options": {
        "env": {
          "PYTHONPATH": "${workspaceFolder}"
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "Format Code (Ruff + Black)",
      "type": "shell",
      "command": "ruff check src scripts --fix && black src scripts",
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "Docs Check",
      "type": "shell",
      "command": "python scripts/tools/check_md_links.py",
      "presentation": {
        "reveal": "silent",
        "panel": "shared"
      }
    },
    {
      "label": "Simulate Offline CI",
      "type": "shell",
      "command": "python scripts/dev/offline_hooks/run_offline.py -- pytest -q",
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      },
      "problemMatcher": []
    }
  ]
}
'@
        Set-Content -Path $tasksPath -Value $tasksContent -Encoding UTF8
    }
    else {
        Write-Host "[i] Existing VS Code tasks preserved"
    }
}

Initialize-Venv
$pythonExe = Get-PythonPath
Install-Packages -PythonExe $pythonExe
Set-TasksFile

Write-Host "[✓] Bootstrap complete"
