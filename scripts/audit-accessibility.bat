@echo off
REM ============================================================================
REM audit-accessibility.bat
REM Subtarea 5.8 del Plan de Trabajo Pre-SAT - Plataforma DTI Nijar
REM
REM Wrapper Windows que llama al script PowerShell.
REM ============================================================================

setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%audit-accessibility.ps1" %*
exit /b %ERRORLEVEL%
