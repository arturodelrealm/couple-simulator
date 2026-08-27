@echo off
REM Wrapper for tasks.ps1 (cmd.exe)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tasks.ps1" %*
