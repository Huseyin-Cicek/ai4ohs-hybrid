# =====================================================================
# restore-services-from-snapshot.ps1
#
# Amaç:
#   services_before_optimize_20251116_203908.txt snapshot dosyasına göre
#   o anda Running olan servisleri tekrar aktif (Automatic/Manual + Running)
#   duruma getirmek.
# =====================================================================

# Admin kontrolü
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Bu script yönetici olarak çalıştırılmalı." -ForegroundColor Red
    return
}

# Snapshot dosyasının yolu
$snapshotFile = "C:\vscode-projects\ai4ohs-hybrid\logs\scripts\services_before_optimize_20251116_203908.txt"

if (-not (Test-Path $snapshotFile)) {
    Write-Host "Snapshot dosyası bulunamadı: $snapshotFile" -ForegroundColor Red
    return
}

Write-Host "Snapshot dosyası yükleniyor: $snapshotFile" -ForegroundColor Cyan

# Snapshot içinden Running satırlardaki servis adlarını çıkar
$servicesToStart = @()

Get-Content $snapshotFile | ForEach-Object {
    # Örnek satır:
    # Running  AppIDSvc           Application Identity
    if ($_ -match '^\s*Running\s+(\S+)\s+') {
        $servicesToStart += $Matches[1]
    }
}

Write-Host "Toplam $($servicesToStart.Count) servis restore edilecek…" -ForegroundColor Yellow

if ($servicesToStart.Count -eq 0) {
    Write-Warning "Snapshot'tan hiç servis okunamadı. Dosyanın formatını ve yolu kontrol et."
    return
}

function Restore-ServiceSafe {
    param([string]$Name)

    $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($svc -eq $null) {
        Write-Host "Servis bulunamadı (skip): $Name"
        return
    }

    # User-suffix (ör. _e079f) olanlara Manual, diğerlerine Automatic verelim
    if ($svc.Name -match '_[A-Za-z0-9]+$') {
        $startup = "Manual"
    } else {
        $startup = "Automatic"
    }

    Write-Host ">>> Restoring $Name (Startup=$startup)"

    try {
        Set-Service -Name $svc.Name -StartupType $startup -ErrorAction SilentlyContinue
        if ($svc.Status -ne "Running") {
            Start-Service -Name $svc.Name -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Warning "Restore edilemedi: $Name - $($_.Exception.Message)"
    }
}

foreach ($svcName in $servicesToStart) {
    Restore-ServiceSafe -Name $svcName
}

Write-Host "=== TÜM SERVİSLER SNAPSHOT'A GÖRE GERİ YÜKLENDİ ===" -ForegroundColor Green
Write-Host "Yeniden başlatma tavsiye edilir."
