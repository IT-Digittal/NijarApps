# =============================================================
# Plataforma DTI Níjar — Reset completo Windows
# =============================================================
# Para todos los servicios Y BORRA los volumenes (BBDD, Redis,
# MQTT, modelos Rasa). Equivale a empezar de cero.
# =============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host " Plataforma DTI Níjar — RESET COMPLETO" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "ATENCION: esto va a BORRAR todos los datos locales:"
Write-Host "  - Base de datos PostgreSQL (usuarios, contenidos, observaciones IoT)"
Write-Host "  - Cache de Redis"
Write-Host "  - Datos de MQTT"
Write-Host "  - Modelos entrenados de Rasa"
Write-Host ""
Write-Host "Tras ejecutar esto, en el siguiente .\windows\start.ps1 se cargaran los datos seed por defecto."
Write-Host ""

$confirm = Read-Host "Escribe SI (en mayusculas) para confirmar"

if ($confirm -ne "SI") {
    Write-Host ""
    Write-Host "Reset cancelado. No se ha tocado nada." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Parando servicios y borrando volumenes..." -ForegroundColor Yellow
& docker compose --profile workers --profile rasa down -v

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK — Plataforma reseteada completamente" -ForegroundColor Green
    Write-Host "     Para volver a arrancar: .\windows\start.ps1"
} else {
    Write-Host ""
    Write-Host "AVISO — docker compose down -v devolvio error." -ForegroundColor Yellow
}
Write-Host ""
