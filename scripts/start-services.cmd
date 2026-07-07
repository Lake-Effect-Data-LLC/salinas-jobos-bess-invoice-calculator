@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-services.ps1"
echo.
pause
