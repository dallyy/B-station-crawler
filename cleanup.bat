@echo off
SETLOCAL
chcp 65001 >nul
set PYTHONUTF8=1

powershell.exe -ExecutionPolicy Bypass -File "%~dp0cleanup.ps1"

pause
ENDLOCAL
EXIT /B %ERRORLEVEL%
