# Bili Scraper Stop Service Script
Write-Host "========================================"
Write-Host "      Bili Scraper - Stop Service"
Write-Host "========================================"
Write-Host ""

# Find processes listening on ports 8000 and 8001
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess

if (-not $port8000 -and -not $port8001) {
    Write-Host "[INFO] No process found listening on port 8000 or 8001"
    Write-Host "[INFO] Web service may not be running"
    Write-Host ""
    exit 0
}

Write-Host "Found processes listening on the following ports:"
Write-Host "----------------------------------------"
if ($port8000) {
    Write-Host "Port 8000 PID: $port8000"
    Get-Process -Id $port8000 -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,WorkingSet | Format-Table -AutoSize
}
if ($port8001) {
    Write-Host "Port 8001 PID: $port8001"
    Get-Process -Id $port8001 -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,WorkingSet | Format-Table -AutoSize
}
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Stopping processes..."
Write-Host ""

# Kill processes
if ($port8000) {
    Stop-Process -Id $port8000 -Force -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "[OK] Stopped process on port 8000 (PID: $port8000)"
    } else {
        Write-Host "[WARN] Failed to stop process on port 8000"
    }
}

if ($port8001) {
    Stop-Process -Id $port8001 -Force -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "[OK] Stopped process on port 8001 (PID: $port8001)"
    } else {
        Write-Host "[WARN] Failed to stop process on port 8001"
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "      Operation Complete"
Write-Host "========================================"
