# =============================================================
# Plataforma DTI Níjar — Logs en tiempo real
# =============================================================
# Uso:
#   .\windows\logs.ps1                  Logs de la API (por defecto)
#   .\windows\logs.ps1 -Service db      Logs de un servicio concreto
#   .\windows\logs.ps1 -Service all     Logs de todos los servicios
#   .\windows\logs.ps1 -Tail 200        Mas lineas de historico
#
# Servicios disponibles:
#   api, db, redis, mqtt, mqtt-subscriber, social-worker, rasa
# =============================================================

[CmdletBinding()]
param(
    [string]$Service = "api",
    [int]$Tail = 100
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Plataforma DTI Níjar — Logs" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicio: $Service  |  Ultimas lineas: $Tail" -ForegroundColor Yellow
Write-Host "Pulsa Ctrl+C para salir." -ForegroundColor Yellow
Write-Host ""

if ($Service -eq "all" -or $Service -eq "*") {
    & docker compose --profile workers --profile rasa logs -f --tail $Tail
} else {
    & docker compose logs -f --tail $Tail $Service
}
