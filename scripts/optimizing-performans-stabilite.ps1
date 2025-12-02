# =====================================================================
# Optimized PowerShell script for performance and stability tuning
# - Enables TRIM
# - Runs ReTrim on all partitions on NVMe disks
# - Sets selected services to Manual startup
# =====================================================================

[CmdletBinding()]
param()

# ---------------- Admin check ----------------------------------------
$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Run this script as Administrator." -ForegroundColor Red
    exit 1
}

# ---------------- Logging helpers ------------------------------------
function Info($msg) { Write-Host "INFO : $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "WARN : $msg" -ForegroundColor Yellow }
function Err($msg)  { Write-Host "ERR  : $msg"  -ForegroundColor Red }

Info "==============================================================="
Info "Performance & stability tuning (NVMe TRIM + services)..."
Info "==============================================================="

# =====================================================================
# [1] Enable TRIM globally
# =====================================================================
Info "[1] Enabling TRIM globally (DisableDeleteNotify = 0)..."
try {
    fsutil behavior set DisableDeleteNotify 0 | Out-Null
    Info "[1] TRIM is now enabled (if supported by the drive)."
} catch {
    Warn "[1] Failed to set TRIM global flag: $($_.Exception.Message)"
}

# =====================================================================
# [2] NVMe TRIM / ReTrim optimization
# =====================================================================
Info "[2] NVMe TRIM/ReTrim operations..."

try {
    # Get all NVMe physical disks
    $nvmeDisks = Get-PhysicalDisk -ErrorAction Stop | Where-Object { $_.BusType -eq 'NVMe' }

    if (-not $nvmeDisks -or $nvmeDisks.Count -eq 0) {
        Warn "[2] No NVMe disks detected (BusType=NVMe). Skipping ReTrim."
    } else {
        foreach ($pd in $nvmeDisks) {
            Info ("[2] NVMe Disk: FriendlyName='{0}', Serial='{1}'" -f $pd.FriendlyName, $pd.SerialNumber)

            # Map PhysicalDisk -> Disk (to get DiskNumber correctly)
            $diskObj = $null
            try {
                $diskObj = $pd | Get-Disk -ErrorAction Stop
            } catch {
                Warn ("[2] Get-Disk mapping failed for PhysicalDisk '{0}': {1}" -f $pd.FriendlyName, $_.Exception.Message)
                continue
            }

            # Get all partitions with drive letters
            $parts = $null
            try {
                $parts = Get-Partition -DiskNumber $diskObj.Number -ErrorAction Stop |
                         Where-Object { $_.DriveLetter -ne $null }
            } catch {
                Warn ("[2] Get-Partition failed for DiskNumber={0}: {1}" -f $diskObj.Number, $_.Exception.Message)
                continue
            }

            if (-not $parts -or $parts.Count -eq 0) {
                Warn ("[2] No lettered partitions found on DiskNumber={0} (NVMe)." -f $diskObj.Number)
                continue
            }

            foreach ($p in $parts) {
                $dl = $p.DriveLetter
                Info "[2] Optimizing volume: DriveLetter=$dl (Optimize-Volume -ReTrim)"
                try {
                    Optimize-Volume -DriveLetter $dl -ReTrim -ErrorAction SilentlyContinue | Out-Null
                } catch {
                    Warn ("[2] Optimize-Volume failed on DriveLetter={0}: {1}" -f $dl, $_.Exception.Message)
                }
            }
        }

        Info "[2] NVMe TRIM/ReTrim operations completed."
    }
} catch {
    Warn "[2] NVMe processing failed: $($_.Exception.Message)"
}

# =====================================================================
# [3] Service tuning (selected services -> Manual)
# =====================================================================
Info "[3] Service tuning..."

# List of services you want to set to Manual
# Adjust this list according to your environment
$toManual = @(
    "CCleaner7",        # Example: CCleaner service
    "ASUSOptimization"  # Example: ASUS optimization helper
)

foreach ($svcName in $toManual) {
    try {
        $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($null -eq $svc) {
            Warn "[3] Service not found: '$svcName' (skipping)."
            continue
        }

        if ($svc.StartType -ne "Manual") {
            Set-Service -Name $svc.Name -StartupType Manual -ErrorAction Stop
            Info "[3] Set '$($svc.Name)' StartupType -> Manual."
        } else {
            Info "[3] '$($svc.Name)' is already Manual. No change."
        }
    } catch {
        Warn "[3] Failed to set '$svcName' to Manual: $($_.Exception.Message)"
    }
}

Warn "If you need a full rollback, use System Restore (a restore point should be created by your main optimization script)."
Info "Done."
Info "==============================================================="
