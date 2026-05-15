@echo off
REM ============================================================================
REM load-catalog.bat
REM Subtarea 6.8 del Plan de Trabajo Pre-SAT - Plataforma DTI Nijar
REM
REM Wrapper Windows que llama al script PowerShell.
REM
REM Uso:
REM   load-catalog.bat -Plantilla "C:\path\plantilla.xlsx" -DryRun
REM   load-catalog.bat -Plantilla "C:\path\plantilla.xlsx" -Usuario admin@nijar.es -Password ***
REM ============================================================================

setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%SCRIPT_DIR%load-catalog.ps1" %*
exit /b %ERRORLEVEL%
