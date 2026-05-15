# =============================================================
# Plataforma DTI Níjar — Estado de servicios
# =============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Plataforma DTI Níjar — Estado" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Docker version
Write-Host "Docker Desktop:" -ForegroundColor Yellow
try {
    $v = docker version --format '{{.Server.Version}}' 2>$null
    Write-Host "  Engine $v" -ForegroundColor Green
} catch {
    Write-Host "  ERROR — Docker no responde" -ForegroundColor Red
    exit 1
}

# Servicios del compose
Write-Host ""
Write-Host "Servicios Docker Compose:" -ForegroundColor Yellow
& docker compose --profile workers --profile rasa ps

# Health checks
Write-Host ""
Write-Host "Health checks de la API:" -ForegroundColor Yellow

try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    if ($r.StatusCode -eq 200) {
        Write-Host "  API:    OK (200)" -ForegroundColor Green
        $health = $r.Content | ConvertFrom-Json
        Write-Host "          Status: $($health.status)"
        if ($health.version) { Write-Host "          Version: $($health.version)" }
    }
} catch {
    Write-Host "  API:    NO RESPONDE" -ForegroundColor Red
}

try {
    $r = Invoke-WebRequest -Uri "http://localhost:5005/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    if ($r.StatusCode -eq 200) {
        Write-Host "  Rasa:   OK (200)" -ForegroundColor Green
    }
} catch {
    Write-Host "  Rasa:   no arrancado o no responde" -ForegroundColor Yellow
}

# Recursos
Write-Host ""
Write-Host "Uso de recursos por contenedor:" -ForegroundColor Yellow
& docker stats --no-stream --format "table {{.Name}}`t{{.CPUPerc}}`t{{.MemUsage}}`t{{.MemPerc}}" 2>$null

# Volumenes
Write-Host ""
Write-Host "Volumenes de datos:" -ForegroundColor Yellow
& docker volume ls --filter "name=nijar" --format "table {{.Name}}`t{{.Driver}}"

Write-Host ""
