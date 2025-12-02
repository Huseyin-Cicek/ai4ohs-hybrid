# Run as Administrator for full effect

Write-Host ">>> Cleaning user TEMP..."
try {
    Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "User TEMP cleaned."
} catch {
    Write-Warning "User TEMP clean error: $($_.Exception.Message)"
}

Write-Host ">>> Cleaning C:\Windows\Temp..."
try {
    Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "C:\Windows\Temp cleaned."
} catch {
    Write-Warning "C:\Windows\Temp clean error: $($_.Exception.Message)"
}

Write-Host ">>> Cleaning C:\Users\hcicek\AppData\Local\Temp..."
try {
    Remove-Item -Path "C:\Users\hcicek\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "C:\Users\hcicek\AppData\Local\Temp cleaned."
} catch {
    Write-Warning "C:\Users\hcicek\AppData\Local\Temp clean error: $($_.Exception.Message)"
}
