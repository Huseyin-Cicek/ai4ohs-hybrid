# =====================================================================
# services-list-export.ps1
#
# Tüm Windows servislerini CIM üzerinden JSON olarak kaydeder:
# C:\vscode-projects\ai4ohs-hybrid\logs\scripts\services-list-{timestamp}.json
# =====================================================================

# 1) Log klasörü hazırlanıyor
$logDir = "C:\vscode-projects\ai4ohs-hybrid\logs\scripts"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# 2) Zaman etiketi
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# 3) JSON dosya yolu
$logPath = Join-Path $logDir "services-list-$timestamp.json"

Write-Host ">>> CIM üzerinden servis listesi toplanıyor..."

try {
    # Win32_Service tüm servisleri verir (Running / Stopped vs.)
    $services = Get-CimInstance -ClassName Win32_Service -ErrorAction Stop |
        Select-Object `
            @{Name='Status';     Expression = { $_.State }}, `
            @{Name='Name';       Expression = { $_.Name }}, `
            @{Name='DisplayName';Expression = { $_.DisplayName }}, `
            @{Name='StartType';  Expression = { $_.StartMode }}

} catch {
    Write-Host "HATA: Get-CimInstance Win32_Service çağrısı başarısız: $($_.Exception.Message)" -ForegroundColor Red
    return
}

Write-Host ">>> Toplam $($services.Count) servis kaydedilecek."
Write-Host ">>> JSON oluşturuluyor..."

# 4) JSON’a çevir ve kaydet
$services | ConvertTo-Json -Depth 5 | Out-File $logPath -Encoding UTF8

Write-Host "=== Servis listesi kaydedildi ==="
Write-Host $logPath
# =====================================================================
