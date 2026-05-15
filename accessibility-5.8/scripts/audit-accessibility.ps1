# ============================================================================
# audit-accessibility.ps1
# Subtarea 5.8 del Plan de Trabajo Pre-SAT — Plataforma DTI Níjar
# ============================================================================
#
# Ejecuta una auditoría completa WCAG 2.1 AA sobre los frontales del proyecto
# (tótem y dashboard) usando axe-core + Lighthouse + Playwright.
#
# Uso (PowerShell desde la raíz del proyecto):
#   .\scripts\audit-accessibility.ps1
#   .\scripts\audit-accessibility.ps1 -Only totem
#   .\scripts\audit-accessibility.ps1 -Strict
#   .\scripts\audit-accessibility.ps1 -BaseUrl http://localhost:8000
#
# Salida en: reports\accessibility\audit-YYYY-MM-DD\
# ============================================================================

[CmdletBinding()]
param(
  [string]$Only = "",
  [switch]$Strict,
  [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent $ROOT  # raíz del proyecto

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host " Auditoria WCAG 2.1 AA - Plataforma DTI Nijar" -ForegroundColor Cyan
Write-Host " Subtarea 5.8 del Plan de Trabajo Pre-SAT" -ForegroundColor Cyan
Write-Host " Expediente 18962/2025 - IT DIGITTAL" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Node.js
Write-Host "[1/4] Verificando Node.js..." -ForegroundColor Yellow
try {
  $nodeVersion = (node --version) 2>$null
  if (-not $nodeVersion) { throw "Node no responde" }
  $major = [int]($nodeVersion.TrimStart('v').Split('.')[0])
  if ($major -lt 20) {
    Write-Host "  AVISO: Node $nodeVersion detectado, se requiere v20 o superior." -ForegroundColor Yellow
    Write-Host "  Descarga: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
  }
  Write-Host "  OK: Node $nodeVersion" -ForegroundColor Green
} catch {
  Write-Host "  ERROR: Node.js no esta instalado o no se encuentra en PATH." -ForegroundColor Red
  Write-Host "  Descarga: https://nodejs.org/  (version 20 LTS o superior)" -ForegroundColor Yellow
  exit 1
}

# 2. Verificar que el proyecto está arrancado
Write-Host "[2/4] Verificando que el proyecto este arrancado en $BaseUrl..." -ForegroundColor Yellow
try {
  $resp = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
  Write-Host "  OK: respuesta HTTP $($resp.StatusCode)" -ForegroundColor Green
} catch {
  Write-Host "  ERROR: el proyecto no responde en $BaseUrl" -ForegroundColor Red
  Write-Host "  Arrancalo con: .\windows\start.bat" -ForegroundColor Yellow
  exit 1
}

# 3. Instalar dependencias del script si hace falta
$scriptDir = Join-Path $ROOT "scripts"
Push-Location $scriptDir

Write-Host "[3/4] Instalando dependencias (primera vez tarda 2-5 min)..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
  npm install --silent 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: npm install fallo" -ForegroundColor Red
    Pop-Location
    exit 1
  }
} else {
  Write-Host "  OK: dependencias ya instaladas" -ForegroundColor Green
}

# 4. Ejecutar auditoría
Write-Host "[4/4] Ejecutando auditoria..." -ForegroundColor Yellow
Write-Host ""

$auditArgs = @("audit-accessibility.js", "--base=$BaseUrl")
if ($Only) { $auditArgs += "--only=$Only" }
if ($Strict) { $auditArgs += "--strict" }

node @auditArgs
$exitCode = $LASTEXITCODE

Pop-Location

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
  Write-Host " Auditoria SUPERADA. Informe en: reports\accessibility\" -ForegroundColor Green
} elseif ($exitCode -eq 1) {
  Write-Host " Auditoria FALLIDA: violaciones bloqueantes detectadas." -ForegroundColor Red
  Write-Host " Revisa el informe HTML para detalles y aplica los fixes." -ForegroundColor Yellow
} elseif ($exitCode -eq 2) {
  Write-Host " Auditoria FALLIDA: score Lighthouse insuficiente." -ForegroundColor Red
} else {
  Write-Host " Auditoria con error tecnico (codigo $exitCode)." -ForegroundColor Red
}
Write-Host "===============================================================" -ForegroundColor Cyan

exit $exitCode
