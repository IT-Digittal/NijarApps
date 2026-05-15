# =============================================================
# Plataforma DTI Níjar — Parada local Windows
# =============================================================
# Para todos los servicios pero MANTIENE los datos (volumenes).
# Para borrar tambien los datos, usar reset.ps1
# =============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Plataforma DTI Níjar — Parada" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Parando todos los servicios..." -ForegroundColor Yellow
& docker compose --profile workers --profile rasa down

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK — Plataforma detenida" -ForegroundColor Green
    Write-Host "     Los datos (BBDD, Redis, MQTT, modelos Rasa) se conservan en volumenes Docker."
    Write-Host "     Para borrarlos tambien, ejecuta: .\windows\reset.ps1"
} else {
    Write-Host ""
    Write-Host "AVISO — docker compose down devolvio error." -ForegroundColor Yellow
    Write-Host "        Comprueba si Docker Desktop esta arrancado."
}
Write-Host ""
