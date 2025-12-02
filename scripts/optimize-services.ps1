# =====================================================================
# repair-allwaysync-and-services.ps1
#
# Purpose:
#   - Safely revert selected services after running
#     optimizing-performans-stabilite.ps1 (or similar tuning scripts)
#   - Specifically try to restore Allway Sync service(s) to
#     Automatic + Running state if present
#
# Usage:
#   - Run PowerShell as Administrator
#   - cd C:\vscode-projects\ai4ohs-hybrid\scripts
#   - .\repair-allwaysync-and-services.ps1
# =====================================================================

# --- Admin check ------------------------------------------------------
$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Please run this script as Administrator." -ForegroundColor Red
    exit 1
}

# --- Helper logging functions ----------------------------------------
function Info($msg) { Write-Host "INFO : $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host " OK  : $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "WARN : $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "ERR  : $msg" -ForegroundColor Red }

Info "==============================================================="
Info "Repairing services (Allway Sync + optional others)..."
Info "==============================================================="

# =====================================================================
# 1) Define services to restore
#    - You can extend this list as needed.
# =====================================================================

# Primary targets: Allway Sync related services (name patterns vary by install)
$servicesToRestore = @(
    "AllwaySync",
    "AllwaySyncService",
    "Allway Sync Service"
)

# OPTIONAL: if you also want to revert some tuning from the optimization script,
# you can uncomment/add here. Example:
# $servicesToRestore += @(
#     "WSearch",          # Windows Search
#     "SysMain",          # Superfetch / SysMain
#     "DiagTrack",        # Telemetry
#     "dmwappushservice", # WAP Push
#     "MapsBroker"        # Downloaded Maps Manager
# )

# =====================================================================
# 2) Restore services: set to Automatic, then Start if not running
# =====================================================================
foreach ($svcName in $servicesToRestore) {
    try {
        $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($null -eq $svc) {
            Warn "Service not found: '$svcName' (skipping)."
            continue
        }

        Info "Restoring service: $($svc.Name) (DisplayName: $($svc.DisplayName))"

        try {
            Set-Service -Name $svc.Name -StartupType Automatic -ErrorAction Stop
            Info "  StartupType set to 'Automatic'."

            # Refresh status after changing startup type
            $svc = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue

            if ($svc.Status -ne "Running") {
                try {
                    Start-Service -Name $svc.Name -ErrorAction Stop
                    Ok "  Service started successfully (Status=Running)."
                } catch {
                    Warn "  Could not start service '$($svc.Name)': $($_.Exception.Message)"
                }
            } else {
                Ok "  Service already running."
            }
        } catch {
            Warn "  Could not set service '$($svc.Name)' to Automatic: $($_.Exception.Message)"
        }
    } catch {
        Warn "Unexpected error while processing '$svcName': $($_.Exception.Message)"
    }
}

# =====================================================================
# 3) (Optional) Try to repair Allway Sync via Scheduled Task
#    Some setups may not use a Windows service but a scheduled task.
# =====================================================================
Info "Checking for Allway Sync related scheduled tasks..."

try {
    $allwayTasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
        Where-Object {
            $_.TaskName -like "*Allway*" -or
            $_.TaskName -like "*Allway Sync*"
        }

    if ($allwayTasks -and $allwayTasks.Count -gt 0) {
        foreach ($t in $allwayTasks) {
            Info "  Found scheduled task: $($t.TaskName)"

            # Enable task if disabled
            if ($t.State -eq "Disabled") {
                try {
                    Enable-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath -ErrorAction Stop
                    Ok "    Task enabled."
                } catch {
                    Warn "    Could not enable task '$($t.TaskName)': $($_.Exception.Message)"
                }
            }

            # Try to run task once (non-blocking)
            try {
                Start-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath -ErrorAction SilentlyContinue
                Ok "    Triggered scheduled task run (non-blocking)."
            } catch {
                Warn "    Could not start scheduled task '$($t.TaskName)': $($_.Exception.Message)"
            }
        }
    } else {
        Info "  No Allway Sync related scheduled tasks found."
    }
}
catch {
    Warn "Error while querying scheduled tasks: $($_.Exception.Message)"
}

# =====================================================================
# 4) Finish
# =====================================================================
Ok  "Service repair routine completed."
Info "If Allway Sync still does not behave as expected, try:"
Info "  - Manually launching the Allway Sync GUI"
Info "  - Rebooting the system once to apply all changes cleanly"
Info "==============================================================="
