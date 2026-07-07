@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0seed-and-verify-db.ps1"
echo.
pause
