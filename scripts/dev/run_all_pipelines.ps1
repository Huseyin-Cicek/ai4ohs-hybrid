Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$devDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptsDir = Split-Path -Parent $devDir
$repoRoot   = Split-Path -Parent $scriptsDir
$runnerPy   = Join-Path $devDir 'run_all_pipelines.py'
$logsDir    = Join-Path $repoRoot 'logs\pipelines'
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

$stamp          = Get-Date -Format 'yyyyMMdd_HHmmss'
$transcriptPath = Join-Path $logsDir "run_all_ps1_$stamp.log"

$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
$pythonExe  = (Test-Path $venvPython) ? $venvPython : 'python'

Write-Host ('='*70)
Write-Host "AI4OHS-HYBRID — Pipeline Launcher (PowerShell)" -ForegroundColor Cyan
Write-Host "Repo Root     : $repoRoot"
Write-Host "Python        : $pythonExe"
Write-Host "Runner        : $runnerPy"
Write-Host "Transcript Log: $transcriptPath"
Write-Host ('='*70)

$transcriptStarted = $false
try { Start-Transcript -Path $transcriptPath -Force | Out-Null; $transcriptStarted=$true } catch {}

try {
  Write-Host "[START] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') — Running full ETL (00→03)..." -ForegroundColor Green
  & $pythonExe $runnerPy
  $code = $LASTEXITCODE
  if ($code -ne 0) { Write-Host "[FAIL] run_all_pipelines.py exited with code $code" -ForegroundColor Red; if($transcriptStarted){try{Stop-Transcript|Out-Null}catch{}}; exit $code }
  if ($transcriptStarted) { try { Stop-Transcript | Out-Null } catch {} }
  exit 0
} catch {
  if ($transcriptStarted) { try { Stop-Transcript | Out-Null } catch {} }
  exit 1
}
