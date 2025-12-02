# =====================================================================
# stability-diagnostics.ps1
#
# AI4OHS-HYBRID - Advanced Stability Diagnostics (READ-ONLY)
#
# Çıktılar:
#   JSON: C:\vscode-projects\ai4ohs-hybrid\logs\scripts\stability-diagnostics-{timestamp}.json
#   LOG : C:\vscode-projects\ai4ohs-hybrid\logs\scripts\stability-diagnostics-{timestamp}.log
#
# NOT:
#   - Sistem üzerinde ayar DEĞİŞTİRMEZ, sadece okur / raporlar.
#   - NVMe / TRIM / Thermal / Fan / Turbo / PowerLimit / Armoury Crate
#     diagnostikleri yeni optimizasyon mimarisine göre hizalanmıştır.
# =====================================================================

$ErrorActionPreference = "Stop"

# --- Ortak yollar ------------------------------------------------------
$root    = "C:\vscode-projects\ai4ohs-hybrid"
$logRoot = Join-Path $root "logs\scripts"
if (-not (Test-Path $logRoot)) {
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
}

$ts       = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $logRoot "stability-diagnostics-$ts.json"
$logPath  = Join-Path $logRoot "stability-diagnostics-$ts.log"

Start-Transcript -Path $logPath -Force

function Info($m){ Write-Host $m -ForegroundColor Cyan }
function Ok($m){ Write-Host $m -ForegroundColor Green }
function Warn($m){ Write-Host $m -ForegroundColor DarkYellow }
function Err($m){ Write-Host $m -ForegroundColor Red }

Info "=== AI4OHS-HYBRID Stability Diagnostics ==="
Info "JSON rapor : $jsonPath"
Info "Text log   : $logPath"
Write-Host ""

# Admin zorunlu değil ama bazı WMI/SMART çağrıları için avantajlı
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$IsAdmin   = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Warn "Yönetici olmadan da çalışır; bazı WMI/SMART verileri eksik olabilir."
}

# JSON kök objesi
$result = [ordered]@{
    Timestamp = (Get-Date).ToString("s")
    Hostname  = $env:COMPUTERNAME
}

# =====================================================================
# [1] Sistem Bilgisi
# =====================================================================
Info ">>> [1/7] Sistem bilgileri alınıyor..."

$os = Get-CimInstance -ClassName Win32_OperatingSystem
$cs = Get-CimInstance -ClassName Win32_ComputerSystem

$cpuName = (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)
$gpus    = Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

$ramTotalGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)

$result.System = [ordered]@{
    OS = [ordered]@{
        Caption      = $os.Caption
        Version      = $os.Version
        BuildNumber  = $os.BuildNumber
        InstallDate  = $os.InstallDate
    }
    Hardware = [ordered]@{
        Manufacturer = $cs.Manufacturer
        Model        = $cs.Model
        CPU          = $cpuName
        RAM_GB       = $ramTotalGB
        GPU          = $gpus | ForEach-Object {
            [ordered]@{
                Name          = $_.Name
                VRAM_GB       = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM / 1GB, 1) } else { $null }
                DriverVersion = $_.DriverVersion
            }
        }
    }
}
Ok "    OS: $($os.Caption)"

# =====================================================================
# [2] Güç Planı + Turbo / Power Limit Raw
# =====================================================================
Info ">>> [2/7] Güç planı / Turbo / Power limit bilgisi alınıyor..."

# Aktif şema
$activeSchemeGuid = $null
$activeSchemeName = $null
try {
    $raw = powercfg /GETACTIVESCHEME 2>$null
    $line = $raw | Select-Object -First 1
    if ($line -match 'Power Scheme GUID:\s+([0-9a-fA-F\-]+)\s+\((.+)\)') {
        $activeSchemeGuid = $Matches[1]
        $activeSchemeName = $Matches[2]
    }
} catch {
    Warn "powercfg /GETACTIVESCHEME okunamadı: $($_.Exception.Message)"
}

# SUB_PROCESSOR ham çıktı (Turbo.SubProcessorRaw)
$subProcRaw = $null
try {
    $subProcRaw = powercfg /q SCHEME_CURRENT SUB_PROCESSOR 2>$null
} catch {
    Warn "powercfg /q SUB_PROCESSOR çağrısı başarısız: $($_.Exception.Message)"
}

# PowerLimits.RawPowerCfg için (SCHEME_CURRENT tamamı değil, yine SUB_PROCESSOR odaklı)
$rawPowerCfg = $null
try {
    $rawPowerCfg = powercfg /q SCHEME_CURRENT 2>$null
} catch {
    Warn "powercfg /q SCHEME_CURRENT okunamadı: $($_.Exception.Message)"
}

$result.Power = [ordered]@{
    ActiveScheme = $activeSchemeGuid
    SchemeName   = $activeSchemeName
}

$result.Turbo = [ordered]@{
    SubProcessorRaw = if ($subProcRaw) { ($subProcRaw -join "`n") } else { $null }
}

$result.PowerLimits = [ordered]@{
    RawPowerCfg = if ($rawPowerCfg) { ($rawPowerCfg -join "`n") } else { $null }
}

Ok "    Active Power Scheme: $activeSchemeName ($activeSchemeGuid)"

# =====================================================================
# [3] CPU / RAM / Temel Load
# =====================================================================
Info ">>> [3/7] CPU / RAM yükü örnek verisi alınıyor..."

$cpuUtil    = $null
$queueLen   = $null
$cpuSource  = "Unavailable"

# Önce Get-Counter dene
try {
    $cpuCounter   = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction Stop
    $queueCounter = Get-Counter '\System\Processor Queue Length'      -ErrorAction Stop

    $cpuUtil  = [math]::Round($cpuCounter.CounterSamples[0].CookedValue, 1)
    $queueLen = $queueCounter.CounterSamples[0].CookedValue
    $cpuSource = "Get-Counter"
}
catch {
    Warn "Get-Counter başarısız: $($_.Exception.Message) - typeperf fallback deneniyor..."

    try {
        $tp = & typeperf "\Processor(_Total)\% Processor Time" -sc 1 2>$null
        if ($tp -and $tp.Count -ge 3) {
            $last = $tp[-1]
            $parts = $last.Split(',')
            $valStr = $parts[-1].Trim('"')
            $val = 0
            if ([double]::TryParse($valStr, [ref]$val)) {
                $cpuUtil = [math]::Round($val, 1)
                $cpuSource = "typeperf"
            }
        }
    } catch {
        Warn "typeperf fallback da başarısız: $($_.Exception.Message)"
    }
}

# RAM kullanım oranı
$osRef = Get-CimInstance Win32_OperatingSystem
$ramFreeGB = [math]::Round($osRef.FreePhysicalMemory * 1KB / 1GB, 1)
$ramUsedGB = [math]::Round($ramTotalGB - $ramFreeGB, 1)
$ramUsedPct = if ($ramTotalGB -gt 0) { [math]::Round(($ramUsedGB / $ramTotalGB) * 100, 1) } else { $null }

$result.CPU = [ordered]@{
    UtilizationPct = $cpuUtil
    QueueLength    = $queueLen
    Source         = $cpuSource
}

$result.Memory = [ordered]@{
    TotalGB = $ramTotalGB
    UsedGB  = $ramUsedGB
    FreeGB  = $ramFreeGB
    UsedPct = $ramUsedPct
}

Ok "    CPU Util: $cpuUtil % (Source=$cpuSource)"
Ok "    RAM Used: $ramUsedGB / $ramTotalGB GB"

# =====================================================================
# [4] Thermal / Fan / NVMe + TRIM (READ-ONLY)
# =====================================================================
Info ">>> [4/7] Thermal / Fan / NVMe / TRIM durumu okunuyor..."

# 4.1 Thermal zones (MSAcpi_ThermalZoneTemperature)
$thermalZones = @()
try {
    $tz = Get-CimInstance -Namespace root/WMI -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction Stop
    foreach ($t in $tz) {
        $curC  = [math]::Round(($t.CurrentTemperature / 10.0) - 273.15, 1)
        $critC = if ($t.CriticalTripPoint) { [math]::Round(($t.CriticalTripPoint / 10.0) - 273.15, 1) } else { $null }
        $passC = if ($t.PassiveTripPoint)  { [math]::Round(($t.PassiveTripPoint  / 10.0) - 273.15, 1) } else { $null }

        $thermalZones += [ordered]@{
            InstanceName       = $t.InstanceName
            CurrentC           = $curC
            CriticalTripPointC = $critC
            PassiveTripPointC  = $passC
        }
    }
}
catch {
    Warn "Thermal zone bilgisi alınamadı (MSAcpi_ThermalZoneTemperature): $($_.Exception.Message)"
}

# 4.2 Fan RPM (ASUS veya Win32_Fan)
$fans = @()
$fanSource = $null

try {
    # ASUS ROG için potansiyel WMI sınıfları (her sistemde olmayabilir)
    $asusFan = Get-CimInstance -Namespace root\WMI -ClassName ASUSWMI_Fan -ErrorAction Stop
    foreach ($f in $asusFan) {
        $fans += [ordered]@{
            Source   = "ASUSWMI_Fan"
            Name     = $f.InstanceName
            RPM      = $f.CurrentSpeed
            DutyPct  = $f.CurrentDuty
        }
    }
    if ($fans.Count -gt 0) { $fanSource = "ASUSWMI_Fan" }
}
catch {
    # Fallback: Win32_Fan
    try {
        $wfan = Get-WmiObject -Class Win32_Fan -ErrorAction Stop
        foreach ($f in $wfan) {
            $fans += [ordered]@{
                Source   = "Win32_Fan"
                Name     = $f.Name
                RPM      = $f.DesiredSpeed
                DutyPct  = $null
            }
        }
        if ($fans.Count -gt 0) { $fanSource = "Win32_Fan" }
    } catch {
        Warn "Fan RPM bilgisi alınamadı: $($_.Exception.Message)"
    }
}

# 4.3 NVMe + SMART (Get-PhysicalDisk + Get-StorageReliabilityCounter)
$disks = @()
try {
    $pdisks = Get-PhysicalDisk -ErrorAction Stop

    foreach ($d in $pdisks) {
        $isNvme = ($d.BusType -eq 'NVMe')
        $rel = $null
        try {
            $rel = Get-StorageReliabilityCounter -PhysicalDisk $d -ErrorAction Stop
        } catch {
            # bazı sistemlerde yetki / destek yok
        }

        $disks += [ordered]@{
            FriendlyName      = $d.FriendlyName
            BusType           = [string]$d.BusType
            IsNVMe            = $isNvme
            HealthStatus      = [string]$d.HealthStatus
            SizeGB            = [math]::Round($d.Size / 1GB, 1)
            Wear              = if ($rel) { $rel.Wear } else { $null }
            MediaErrorCount   = if ($rel) { $rel.MediaErrorCount } else { $null }
            TemperatureC      = if ($rel) { $rel.Temperature } else { $null }
            PredictionFailure = if ($rel) { $rel.PredictionFailure } else { $null }
        }
    }
}
catch {
    Warn "Get-PhysicalDisk / SMART bilgisi alınamadı: $($_.Exception.Message)"
}

# 4.4 TRIM durumu (global)
$trimStatus = [ordered]@{
    RawOutput            = $null
    DisableDeleteNotify  = $null
}
try {
    $fsRaw = fsutil behavior query DisableDeleteNotify 2>$null
    $trimStatus.RawOutput = ($fsRaw -join "`n")

    if ($fsRaw -match 'DisableDeleteNotify\s*=\s*(\d)') {
        $trimStatus.DisableDeleteNotify = [int]$Matches[1]
    }
}
catch {
    Warn "TRIM durumu okunamadı (fsutil): $($_.Exception.Message)"
}

$result.Thermal = [ordered]@{
    Zones        = $thermalZones
    FanSource    = $fanSource
}

$result.Fans = [ordered]@{
    Fans = $fans
}

$result.Storage = [ordered]@{
    Disks      = $disks
    TrimStatus = $trimStatus
}

Ok "    Thermal zones: $($thermalZones.Count) adet"
Ok "    NVMe/Disks:   $($disks.Count) adet"

# =====================================================================
# [5] Armoury Crate / ASUS / Sync & Security Servis Durumu
# =====================================================================
Info ">>> [5/7] Armoury Crate / servis sağlık durumu okunuyor..."

# Armoury / ASUS servisleri
$armourySvcNames = @(
    "ArmouryCrateControlInterface",
    "ArmouryCrateService",
    "AsusAppService",
    "AsusCertService",
    "ASUSOptimization",
    "ASUSSystemAnalysis",
    "ASUSSystemDiagnosis",
    "AsusPTPService",
    "ASUSSwitch",
    "AsusROGLSLService"
)

$armouryServices = @()
foreach ($name in $armourySvcNames) {
    $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
    if ($svc) {
        $armouryServices += [ordered]@{
            Name      = $svc.Name
            Status    = [string]$svc.Status
            StartType = [string]$svc.StartType
        }
    }
}

# Armoury Crate kurulum yolu (tahmini, sistemden sisteme değişebilir)
$armouryPaths = [ordered]@{
    ArmouryCrateRoot       = $null
    ArmouryCrateServiceExe = $null
    ArmouryCrateAppExe     = $null
}

try {
    $possibleRoots = @(
        "C:\Program Files\ASUS\ARMOURY CRATE Service",
        "C:\Program Files (x86)\ASUS\ARMOURY CRATE Service",
        "C:\Program Files\WindowsApps"
    )

    foreach ($p in $possibleRoots) {
        if (Test-Path $p) {
            $armouryPaths.ArmouryCrateRoot = $p
            break
        }
    }

    # exe arama (light, recursive değil)
    if ($armouryPaths.ArmouryCrateRoot -and (Test-Path $armouryPaths.ArmouryCrateRoot)) {
        $svcExe = Get-ChildItem -Path $armouryPaths.ArmouryCrateRoot -Filter "*ArmouryCrate.Service*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        $appExe = Get-ChildItem -Path $armouryPaths.ArmouryCrateRoot -Filter "*ArmouryCrate*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

        if ($svcExe) { $armouryPaths.ArmouryCrateServiceExe = $svcExe.FullName }
        if ($appExe) { $armouryPaths.ArmouryCrateAppExe     = $appExe.FullName }
    }
}
catch {
    Warn "Armoury Crate InstallPathInfo okunurken hata: $($_.Exception.Message)"
}

# Sync + Security (Allway Sync, OneDrive, Norton)
$syncSecurityServices = @()
$syncNames = @(
    "ALLWASYNCService",    # Allway Sync (bazı sistemlerde farklı olabilir)
    "FileSyncHelper",      # OneDrive yardımcı
    "OneSyncSvc*",         # MS sync host
    "Norton*",             # Norton servisleri
    "webthreatdefsvc",
    "WinDefend"
)

foreach ($pattern in $syncNames) {
    Get-Service -Name $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        $syncSecurityServices += [ordered]@{
            Name      = $_.Name
            Status    = [string]$_.Status
            StartType = [string]$_.StartType
        }
    }
}

$result.Armoury = [ordered]@{
    Services         = $armouryServices
    InstallPathInfo  = $armouryPaths
}

$result.Services = [ordered]@{
    SyncSecurity = $syncSecurityServices
}

Ok "    Armoury services: $($armouryServices.Count) kayıt"
Ok "    Sync/Security   : $($syncSecurityServices.Count) kayıt"

# =====================================================================
# [6] Event Log Analizi (Son 200 Warning/Error)
# =====================================================================
Info ">>> [6/7] Event log uyarı/hata analizi (System + Application)..."

$eventLookbackHours = 24

$systemEvents = @()
$appEvents    = @()

try {
    $since = (Get-Date).AddHours(-$eventLookbackHours)

    $systemEvents = Get-WinEvent -LogName System -ErrorAction SilentlyContinue |
        Where-Object { $_.LevelDisplayName -in @('Error','Warning') -and $_.TimeCreated -ge $since } |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                TimeCreated = $_.TimeCreated
                Level       = $_.LevelDisplayName
                Id          = $_.Id
                Provider    = $_.ProviderName
                Message     = $_.Message
            }
        }

    $appEvents = Get-WinEvent -LogName Application -ErrorAction SilentlyContinue |
        Where-Object { $_.LevelDisplayName -in @('Error','Warning') -and $_.TimeCreated -ge $since } |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                TimeCreated = $_.TimeCreated
                Level       = $_.LevelDisplayName
                Id          = $_.Id
                Provider    = $_.ProviderName
                Message     = $_.Message
            }
        }
}
catch {
    Warn "Event log okunurken hata: $($_.Exception.Message)"
}

$result.Events = [ordered]@{
    LookbackHours = $eventLookbackHours
    System        = $systemEvents
    Application   = $appEvents
}

Ok "    System events:      $($systemEvents.Count)"
Ok "    Application events: $($appEvents.Count)"

# =====================================================================
# [7] JSON yazımı
# =====================================================================
Info ">>> [7/7] JSON rapor kaydediliyor..."

try {
    $json = $result | ConvertTo-Json -Depth 8
    Set-Content -Path $jsonPath -Value $json -Encoding UTF8
    Ok "JSON : $jsonPath"
}
catch {
    Err "JSON yazılırken hata: $($_.Exception.Message)"
}

Ok "=== Stability diagnostics tamamlandı ==="
Stop-Transcript
