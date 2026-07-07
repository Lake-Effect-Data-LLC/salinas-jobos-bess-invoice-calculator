@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-streamlit.ps1"
echo.
pause
