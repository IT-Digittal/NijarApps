# ============================================================================
# load-catalog.ps1
# Subtarea 6.8 del Plan de Trabajo Pre-SAT — Plataforma DTI Níjar
# ============================================================================
#
# Carga el catálogo de recursos turísticos rellenado por el Ayuntamiento
# en el backend FastAPI del proyecto.
#
# Uso (PowerShell desde la raíz del proyecto):
#   .\scripts\load-catalog.ps1 -Plantilla "C:\dev\plantilla.xlsx" -DryRun
#   .\scripts\load-catalog.ps1 -Plantilla "C:\dev\plantilla.xlsx" -Usuario admin@nijar.es -Password "***"
#   .\scripts\load-catalog.ps1 -Plantilla "C:\dev\plantilla.xlsx"  # usa env vars NIJAR_USER/NIJAR_PASS
# ============================================================================

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$Plantilla,
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Usuario = "",
  [string]$Password = "",
  [switch]$DryRun,
  [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host " Cargador del catalogo - Plataforma DTI Nijar" -ForegroundColor Cyan
Write-Host " Subtarea 6.8 del Plan de Trabajo Pre-SAT" -ForegroundColor Cyan
Write-Host " Expediente 18962/2025 - IT DIGITTAL" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow
try {
  $pyVersion = (python --version) 2>$null
  if (-not $pyVersion) { throw "Python no responde" }
  Write-Host "  OK: $pyVersion" -ForegroundColor Green
} catch {
  Write-Host "  ERROR: Python no esta instalado o no esta en PATH." -ForegroundColor Red
  Write-Host "  Descarga: https://www.python.org/  (3.11 o superior)" -ForegroundColor Yellow
  exit 1
}

# 2. Verificar plantilla
Write-Host "[2/4] Verificando plantilla..." -ForegroundColor Yellow
if (-not (Test-Path $Plantilla)) {
  Write-Host "  ERROR: no se encuentra el archivo $Plantilla" -ForegroundColor Red
  exit 1
}
Write-Host "  OK: $Plantilla" -ForegroundColor Green

# 3. Verificar backend (solo si no es dry-run)
if (-not $DryRun) {
  Write-Host "[3/4] Verificando backend en $BaseUrl..." -ForegroundColor Yellow
  try {
    Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
    Write-Host "  OK: backend responde" -ForegroundColor Green
  } catch {
    Write-Host "  ERROR: el proyecto no responde en $BaseUrl" -ForegroundColor Red
    Write-Host "  Arrancalo con: .\windows\start.bat" -ForegroundColor Yellow
    exit 1
  }
} else {
  Write-Host "[3/4] Modo dry-run: no se conecta al backend" -ForegroundColor Yellow
}

# 4. Instalar dependencias si hace falta
Write-Host "[4/4] Verificando dependencias Python..." -ForegroundColor Yellow
$deps = @("httpx", "openpyxl", "pydantic[email]")
foreach ($d in $deps) {
  $pkg = $d -replace "\[.*\]", ""
  $check = python -c "import $($pkg.Replace('-','_'))" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "  Instalando $d..." -ForegroundColor Yellow
    pip install --quiet $d
    if ($LASTEXITCODE -ne 0) {
      Write-Host "  ERROR al instalar $d" -ForegroundColor Red
      exit 1
    }
  }
}
Write-Host "  OK: dependencias instaladas" -ForegroundColor Green
Write-Host ""

# Ejecutar
$scriptPath = Join-Path $ROOT "scripts\load_catalog.py"
$args = @($scriptPath, "--plantilla", $Plantilla, "--base-url", $BaseUrl)
if ($DryRun) { $args += "--dry-run" }
if ($Usuario) { $args += @("--usuario", $Usuario) }
if ($Password) { $args += @("--password", $Password) }
if ($Verbose) { $args += "--verbose" }

Write-Host "Ejecutando carga..." -ForegroundColor Cyan
Write-Host ""

python @args
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
  Write-Host " CARGA COMPLETADA. Reporte en: reports\catalog-load\" -ForegroundColor Green
} else {
  Write-Host " Carga finalizada con errores. Revisa el reporte HTML." -ForegroundColor Yellow
}
Write-Host "===============================================================" -ForegroundColor Cyan

exit $exitCode
