@echo off
SETLOCAL
SET PROJECT_DIR=%~dp0
chcp 65001 >nul
set PYTHONUTF8=1

echo 测试：终端编码已切换为 UTF-8（若看到中文则正常）
echo Note: If you are in PowerShell, run as ` .\run_web.bat ` (PowerShell doesn't implicitly run scripts in current dir)
echo.

REM Check if venv exists
if not exist "%PROJECT_DIR%venv\Scripts\activate.bat" (
  echo [ERROR] Virtualenv not found at "%PROJECT_DIR%venv\Scripts\activate.bat"
  echo [ERROR] Please create a virtualenv or adjust this script.
  EXIT /B 1
)

CALL "%PROJECT_DIR%venv\Scripts\activate.bat"

REM Initialize database first
echo [1/3] Initializing database...
python "%PROJECT_DIR%init_db.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Database initialization failed
    EXIT /B 1
)
echo [OK] Database initialized
echo.

REM Check if ports are already in use
echo [2/3] Checking ports...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8001" ^| find "LISTENING"') do (
    echo [WARN] Port 8001 is already in use by PID %%a
    echo [INFO] Please run stop_web.bat first
    echo.
    tasklist /FI "PID eq %%a" /FO TABLE 2>nul
    EXIT /B 1
)
echo [OK] Port 8001 is available
echo.

REM Run uvicorn server
echo [3/3] Starting web server on http://127.0.0.1:8001 ...
echo.
python -m uvicorn bili_scraper.web:app --host 127.0.0.1 --port 8001 --timeout-keep-alive 5 --limit-concurrency 100
EXIT /B %ERRORLEVEL%
