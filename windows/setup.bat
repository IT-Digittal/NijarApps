@echo off
REM Wrapper para ejecutar setup.ps1 sin tener que cambiar ExecutionPolicy
REM Funciona con doble clic desde el Explorador de Windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 (
    echo.
    echo Hubo un error. Pulsa cualquier tecla para cerrar.
    pause >nul
)
