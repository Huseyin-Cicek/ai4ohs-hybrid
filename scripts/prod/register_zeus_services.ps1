<#
    register_zeus_services.ps1
    AI4OHS-HYBRID – Zeus layer görev kayıt scripti (Task Scheduler)

    - Ön koşulları kontrol eder
    - Zeus ile ilgili Python scriptleri için Windows Scheduled Task oluşturur/günceller
    - Görevler, Task Scheduler altında \AI4OHS\ klasörüne kaydedilir
    - python yerine her zaman TAM YOL kullanır (venv python öncelikli)
#>

param(
    [string]$ProjectRoot = "C:\vscode-projects\ai4ohs-hybrid",
    [string]$PythonExe   = ""   # Boş bırakılırsa otomatik çözülür
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# -------------------- Yardımcı fonksiyonlar --------------------

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR")]
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[{0}] {1,-5} {2}" -f $timestamp, $Level, $Message

    Write-Host $line

    try {
        $logDir  = Join-Path $ProjectRoot "logs\dev"
        $logFile = Join-Path $logDir "register_zeus_services.log"
        if (-not (Test-Path $logDir)) {
            New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        }
        Add-Content -Path $logFile -Value $line
    } catch {
        Write-Host "[LOGFAIL] $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Test-IsAdmin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Resolve-PythonExe {
    param(
        [string]$ProjectRoot,
        [string]$PythonExe
    )

    if ($PythonExe -and (Test-Path $PythonExe)) {
        return (Resolve-Path $PythonExe).Path
    }

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return (Resolve-Path $venvPython).Path
    }

    $cmdPython = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmdPython) {
        return $cmdPython.Source
    }

    throw "Python executable bulunamadı. -PythonExe parametresi ile açıkça belirt veya PATH'e ekle."
}

# -------------------- Ön kontroller --------------------

if (-not (Test-IsAdmin)) {
    Write-Log "Script'i Yönetici (Run as Administrator) olarak çalıştırmalısın." "ERROR"
    throw "Administrator yetkisi gerekli."
}

if (-not (Test-Path $ProjectRoot)) {
    throw "ProjectRoot bulunamadı: $ProjectRoot"
}

$Global:PythonResolvedExe = Resolve-PythonExe -ProjectRoot $ProjectRoot -PythonExe $PythonExe
Write-Log "Python yolu: $Global:PythonResolvedExe"

# -------------------- Görev tanımları --------------------
# İhtiyaca göre Script alanlarını güncelleyebilirsin.

$tasks = @(
    @{
        TaskName    = "AI4OHS_Zeus_Listener"
        Script      = "scripts\dev\zeus_listener.py"
        Description = "AI4OHS-HYBRID Zeus keyboard/voice listener"
        Trigger     = @{ Type = "AtLogon" }
        Enabled     = $true
    },
    @{
        TaskName    = "AI4OHS_File_Sanitizer"
        Script      = "scripts\dev\reorg_sanitizer.py"
        Description = "AI4OHS-HYBRID File Sanitizer (dropzone watcher)"
        Trigger     = @{ Type = "AtLogon" }
        Enabled     = $true
    },
    @{
        TaskName    = "AI4OHS_ML_Worker"
        Script      = "scripts\dev\ml_worker.py"
        Description = "AI4OHS-HYBRID Background ML worker"
        Trigger     = @{ Type = "Daily"; At = "03:00" }  # 03:00 her gün
        Enabled     = $true
    }
)

# -------------------- Task Scheduler objeleri --------------------

$taskPath = "\AI4OHS\"
$script:FailedTasks = @()

foreach ($t in $tasks) {

    $taskName    = $t.TaskName
    $scriptRel   = $t.Script
    $description = $t.Description
    $triggerCfg  = $t.Trigger
    $enabled     = $t.Enabled

    try {
        Write-Log "Registering task '$taskName'..." "INFO"

        $fullScriptPath = Join-Path $ProjectRoot $scriptRel
        if (-not (Test-Path $fullScriptPath)) {
            throw "Script not found: $fullScriptPath"
        }

        if (-not $Global:PythonResolvedExe -or -not (Test-Path $Global:PythonResolvedExe)) {
            throw "Global Python path is not set or invalid: $Global:PythonResolvedExe"
        }

        # --- Trigger oluşturma ---
        switch ($triggerCfg.Type) {
            "AtLogon" {
                $trigger = New-ScheduledTaskTrigger -AtLogOn
            }
            "Daily" {
                if (-not $triggerCfg.At) {
                    throw "Daily trigger için 'At' alanı zorunlu (ör: '03:00')"
                }
                $trigger = New-ScheduledTaskTrigger -Daily -At $triggerCfg.At
            }
            default {
                throw "Desteklenmeyen trigger tipi: $($triggerCfg.Type)"
            }
        }

        # --- Principal (mevcut kullanıcı, highest) ---
        $principal = New-ScheduledTaskPrincipal `
            -UserId "$env:UserDomain\$env:UserName" `
            -RunLevel Highest `
            -LogonType Interactive

        # --- Settings ---
        $settings = New-ScheduledTaskSettingsSet `
            -StartWhenAvailable `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -MultipleInstances IgnoreNew `
            -ExecutionTimeLimit (New-TimeSpan -Hours 4)

        # --- Action ---
        # NOT: New-ScheduledTaskAction için -Environment parametresi yok.
        # Çevresel değişkenleri .env + settings.py üzerinden yönetiyoruz.
        $arguments = "`"$fullScriptPath`""

        $action = New-ScheduledTaskAction `
            -Execute $Global:PythonResolvedExe `
            -Argument $arguments `
            -WorkingDirectory $ProjectRoot

        # --- Görevi kaydet / güncelle ---
        Register-ScheduledTask `
            -TaskName $taskName `
            -TaskPath $taskPath `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description $description `
            -Force | Out-Null

        if (-not $enabled) {
            Disable-ScheduledTask -TaskName $taskName -TaskPath $taskPath -ErrorAction SilentlyContinue | Out-Null
        } else {
            Enable-ScheduledTask  -TaskName $taskName -TaskPath $taskPath -ErrorAction SilentlyContinue | Out-Null
        }

        Write-Log "Task '$taskName' registered successfully." "INFO"
    }
    catch {
        Write-Log "Task '$taskName' FAILED: $_" "ERROR"
        $script:FailedTasks += $taskName
    }
}

# -------------------- Özet --------------------

if ($script:FailedTasks.Count -eq 0) {
    Write-Log "All Zeus tasks registered successfully." "INFO"
    exit 0
}
else {
    Write-Log "Some tasks failed to register:" "WARN"
    foreach ($f in $script:FailedTasks) {
        Write-Log " - $f" "WARN"
    }
    exit 1
}
