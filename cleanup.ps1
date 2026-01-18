# Bili Scraper Cleanup Tool
$ErrorActionPreference = "SilentlyContinue"
$PROJECT_DIR = $PSScriptRoot

Write-Host "========================================"
Write-Host "      Bili Scraper - Cleanup Tool"
Write-Host "========================================"
Write-Host ""

Write-Host "Performing cleanup operations..."
Write-Host ""

# Clear Python cache
Write-Host "[1/5] Cleaning Python cache files..."
$pycachePath = Join-Path $PROJECT_DIR "src\bili_scraper\__pycache__"
if (Test-Path $pycachePath) {
    Remove-Item -Path $pycachePath -Recurse -Force
    Write-Host "[OK] Deleted __pycache__ directory"
} else {
    Write-Host "[SKIP] __pycache__ directory not found"
}

# Clear log files
Write-Host "[2/5] Cleaning log files..."
$logsPath = Join-Path $PROJECT_DIR "logs\"
if (Test-Path $logsPath) {
    Get-ChildItem -Path $logsPath -Filter "*.log" | Remove-Item -Force
    Write-Host "[OK] Cleared logs directory"
} else {
    Write-Host "[SKIP] Logs directory not found"
}

# Clear lock file
Write-Host "[3/5] Cleaning lock file..."
$lockPath = Join-Path $PROJECT_DIR "run.lock"
if (Test-Path $lockPath) {
    Remove-Item -Path $lockPath -Force
    Write-Host "[OK] Deleted lock file"
} else {
    Write-Host "[SKIP] Lock file not found"
}

# Clear temporary files
Write-Host "[4/5] Cleaning temporary files..."
Get-ChildItem -Path $PROJECT_DIR -Filter "*.tmp" | Remove-Item -Force
Get-ChildItem -Path $PROJECT_DIR -Filter "*.bak" | Remove-Item -Force
Write-Host "[OK] Cleaned temporary files"

# Clear database content
Write-Host "[5/5] Clearing database content..."
$dbPath = Join-Path $PROJECT_DIR "data.sqlite"
$venvPython = Join-Path $PROJECT_DIR "venv\Scripts\python.exe"
$clearDbScript = Join-Path $PROJECT_DIR "clear_db.py"

if (Test-Path $dbPath) {
    if (Test-Path $venvPython) {
        $result = & $venvPython $clearDbScript 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Cleared database content"
        } else {
            Write-Host "[WARN] Failed to clear database, trying to delete file"
            Write-Host "[ERROR] $result"
            Remove-Item -Path $dbPath -Force
            Write-Host "[OK] Deleted database file"
        }
    } else {
        Write-Host "[WARN] Virtual environment Python not found, skipping database cleanup"
    }
} else {
    Write-Host "[SKIP] Database file not found"
}

Write-Host ""
Write-Host "========================================"
Write-Host "      Cleanup Complete"
Write-Host "========================================"
Write-Host ""
Write-Host "Cleaned items:"
Write-Host "  - Python cache files"
Write-Host "  - Log files"
Write-Host "  - Lock file"
Write-Host "  - Temporary files"
Write-Host "  - Database content"
Write-Host ""
Write-Host "Note: Database structure is preserved. To reuse, run the scraper first."
Write-Host ""
